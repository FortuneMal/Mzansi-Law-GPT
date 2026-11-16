"use client";

import { ArrowDown, SquarePen } from "lucide-react";
import { useStickToBottom } from "@/hooks/useStickToBottom";
import { Button } from "@/components/ui/Button";
import { useChat } from "./ChatProvider";
import { Composer } from "./Composer";
import { EmptyState } from "./EmptyState";
import { AssistantMessage, UserMessage } from "./Messages";

const STATUS_ANNOUNCEMENTS = {
  pending: "Searching the legislation",
  streaming: "Writing the answer",
  done: "Answer ready",
  stopped: "Response stopped",
  error: "The answer could not be completed",
} as const;

export function ChatView() {
  const { messages, actFilter, setActFilter, isBusy, send, stop, retry, reset } = useChat();
  const last = messages[messages.length - 1];
  const { ref, isAtBottom, scrollToBottom } = useStickToBottom<HTMLDivElement>(
    `${messages.length}:${last?.content.length ?? 0}:${last?.status ?? ""}`,
  );
  const hasMessages = messages.length > 0;
  const announcement = last?.role === "assistant" ? STATUS_ANNOUNCEMENTS[last.status] : "";

  return (
    <div className="flex h-full min-h-0 flex-col">
      {hasMessages && (
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-line px-4 sm:px-6">
          <h1 className="text-sm font-medium text-ink">Conversation</h1>
          <Button variant="ghost" size="sm" onClick={reset}>
            <SquarePen aria-hidden className="size-4" />
            New conversation
          </Button>
        </header>
      )}

      <div className="relative min-h-0 flex-1">
        <div ref={ref} className="h-full overflow-y-auto scrollbar-thin">
          <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-6">
            {hasMessages ? (
              <div className="space-y-8">
                {messages.map((message, index) =>
                  message.role === "user" ? (
                    <UserMessage key={message.id} message={message} />
                  ) : (
                    <AssistantMessage
                      key={message.id}
                      message={message}
                      isLast={index === messages.length - 1}
                      onRetry={retry}
                    />
                  ),
                )}
              </div>
            ) : (
              <EmptyState onPick={send} />
            )}
          </div>
        </div>

        {!isAtBottom && hasMessages && (
          <Button
            variant="secondary"
            size="icon"
            onClick={scrollToBottom}
            aria-label="Scroll to latest message"
            className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full"
          >
            <ArrowDown aria-hidden className="size-4" />
          </Button>
        )}
      </div>

      <div className="shrink-0 px-4 pb-4 sm:px-6">
        <div className="mx-auto w-full max-w-3xl">
          <Composer
            isBusy={isBusy}
            actFilter={actFilter}
            onActFilterChange={setActFilter}
            onSend={send}
            onStop={stop}
          />
          <p className="mt-2 text-center text-xs text-ink-subtle">
            AI-generated guidance, not legal advice. Check important answers on{" "}
            <a
              href="http://www.saflii.org/"
              target="_blank"
              rel="noopener noreferrer"
              className="underline decoration-line-strong underline-offset-2 hover:text-ink-muted"
            >
              SAFLII
            </a>{" "}
            or with an attorney.
          </p>
        </div>
      </div>

      <p className="sr-only" aria-live="polite">
        {announcement}
      </p>
    </div>
  );
}
