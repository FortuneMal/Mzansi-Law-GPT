"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { ApiError, isAbortError, streamChat, type HistoryMessage, type Source } from "@/lib/api";
import { ACT_FILTERS } from "@/lib/catalog";
import { createId } from "@/lib/format";

export type MessageStatus = "pending" | "streaming" | "done" | "stopped" | "error";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: Source[];
  status: MessageStatus;
  error?: string;
}

interface ChatContextValue {
  messages: ChatMessage[];
  actFilter: string;
  setActFilter: (value: string) => void;
  isBusy: boolean;
  send: (text: string) => void;
  stop: () => void;
  retry: () => void;
  reset: () => void;
}

/** Number of prior completed messages sent as conversation history (matches the previous client). */
const HISTORY_LIMIT = 8;

const ChatContext = createContext<ChatContextValue | null>(null);

function toHistory(messages: ChatMessage[]): HistoryMessage[] {
  return messages
    .filter((m) => m.status === "done" && m.content.trim())
    .slice(-HISTORY_LIMIT)
    .map((m) => ({ role: m.role, content: m.content }));
}

export function ChatProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [actFilter, setActFilter] = useState(ACT_FILTERS[0].value);
  const messagesRef = useRef(messages);
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  const patchMessage = useCallback((id: string, patch: (m: ChatMessage) => Partial<ChatMessage>) => {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, ...patch(m) } : m)));
  }, []);

  const run = useCallback(
    async (query: string, history: HistoryMessage[], filter: string) => {
      const id = createId();
      const controller = new AbortController();
      controllerRef.current = controller;
      setMessages((prev) => [...prev, { id, role: "assistant", content: "", sources: [], status: "pending" }]);

      // Batch token deltas into one state update per animation frame.
      let buffered = "";
      let frame: number | null = null;
      const flush = () => {
        frame = null;
        if (!buffered) return;
        const chunk = buffered;
        buffered = "";
        patchMessage(id, (m) => ({ content: m.content + chunk }));
      };

      let outcome: Pick<ChatMessage, "status" | "error"> = {
        status: "error",
        error: "The answer ended unexpectedly. Please try again.",
      };

      try {
        for await (const event of streamChat({ query, history, actFilter: filter }, controller.signal)) {
          if (event.type === "sources") {
            patchMessage(id, () => ({ sources: event.sources, status: "streaming" }));
          } else if (event.type === "delta") {
            buffered += event.content;
            frame ??= requestAnimationFrame(flush);
          } else if (event.type === "done") {
            outcome = { status: "done", error: undefined };
          } else if (event.type === "error") {
            outcome = { status: "error", error: "The answer could not be completed. Please try again." };
          }
        }
      } catch (error) {
        outcome = isAbortError(error)
          ? { status: "stopped", error: undefined }
          : {
              status: "error",
              error: error instanceof ApiError ? error.message : "Something went wrong. Please try again.",
            };
      } finally {
        if (frame !== null) cancelAnimationFrame(frame);
        flush();
        patchMessage(id, () => outcome);
        if (controllerRef.current === controller) controllerRef.current = null;
      }
    },
    [patchMessage],
  );

  const isBusy = messages.some((m) => m.status === "pending" || m.status === "streaming");

  const send = useCallback(
    (text: string) => {
      const query = text.trim();
      if (!query || controllerRef.current) return;
      const history = toHistory(messagesRef.current);
      setMessages((prev) => [...prev, { id: createId(), role: "user", content: query, sources: [], status: "done" }]);
      void run(query, history, actFilter);
    },
    [actFilter, run],
  );

  const stop = useCallback(() => controllerRef.current?.abort(), []);

  const retry = useCallback(() => {
    if (controllerRef.current) return;
    const current = messagesRef.current;
    const last = current[current.length - 1];
    const prompt = current[current.length - 2];
    if (last?.role !== "assistant" || prompt?.role !== "user") return;
    setMessages(current.slice(0, -1));
    void run(prompt.content, toHistory(current.slice(0, -2)), actFilter);
  }, [actFilter, run]);

  const reset = useCallback(() => {
    controllerRef.current?.abort();
    setMessages([]);
  }, []);

  const value = useMemo<ChatContextValue>(
    () => ({ messages, actFilter, setActFilter, isBusy, send, stop, retry, reset }),
    [messages, actFilter, isBusy, send, stop, retry, reset],
  );

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat(): ChatContextValue {
  const context = useContext(ChatContext);
  if (!context) throw new Error("useChat must be used inside <ChatProvider>");
  return context;
}
