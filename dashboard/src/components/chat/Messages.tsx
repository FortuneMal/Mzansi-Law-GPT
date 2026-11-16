"use client";

import { Check, Copy, RotateCcw, Scale } from "lucide-react";
import { useCopyToClipboard } from "@/hooks/useCopyToClipboard";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/cn";
import type { ChatMessage } from "./ChatProvider";
import { Markdown } from "./Markdown";
import { SourceList } from "./SourceList";

export function UserMessage({ message }: { message: ChatMessage }) {
  return (
    <div className="flex justify-end">
      <p className="max-w-[85%] rounded-2xl rounded-br-md bg-surface-muted px-4 py-2.5 text-[15px] leading-7 whitespace-pre-wrap text-ink [overflow-wrap:anywhere]">
        {message.content}
      </p>
    </div>
  );
}

interface AssistantMessageProps {
  message: ChatMessage;
  isLast: boolean;
  onRetry: () => void;
}

export function AssistantMessage({ message, isLast, onRetry }: AssistantMessageProps) {
  const { copied, copy } = useCopyToClipboard();
  const { status, content } = message;
  const isStreaming = status === "streaming";
  const canRetry = isLast && (status === "error" || status === "stopped");

  return (
    <article className="flex gap-3 sm:gap-4" aria-busy={status === "pending" || isStreaming}>
      <div
        aria-hidden
        className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg bg-brand text-on-brand"
      >
        <Scale className="size-4" />
      </div>

      <div className="min-w-0 flex-1">
        <h2 className="sr-only">Mzansi Law GPT</h2>

        {status === "pending" && (
          <p className="flex h-7 items-center gap-2 text-sm text-ink-subtle">
            <Spinner />
            Searching the legislation…
          </p>
        )}

        {content && <Markdown className={cn(isStreaming && "streaming-caret")}>{content}</Markdown>}
        {isStreaming && !content && <p className="streaming-caret h-7 text-sm text-ink-subtle" />}

        {status === "stopped" && <p className="mt-3 text-sm text-ink-subtle">You stopped this response.</p>}
        {status === "error" && (
          <Alert tone="danger" className="mt-3">
            {message.error}
          </Alert>
        )}

        {(status === "done" || status === "stopped") && <SourceList sources={message.sources} />}

        {(status === "done" || canRetry) && (
          <div className="mt-3 flex items-center gap-1">
            {status === "done" && content && (
              <Button variant="ghost" size="sm" onClick={() => copy(content)} aria-live="polite">
                {copied ? <Check aria-hidden className="size-3.5" /> : <Copy aria-hidden className="size-3.5" />}
                {copied ? "Copied" : "Copy"}
              </Button>
            )}
            {canRetry && (
              <Button variant="ghost" size="sm" onClick={onRetry}>
                <RotateCcw aria-hidden className="size-3.5" />
                Try again
              </Button>
            )}
          </div>
        )}
      </div>
    </article>
  );
}
