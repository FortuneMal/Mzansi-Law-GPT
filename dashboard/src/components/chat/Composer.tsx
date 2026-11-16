"use client";

import { useEffect, useId, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { ArrowUp, Square } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { ACT_FILTERS } from "@/lib/catalog";
import { cn } from "@/lib/cn";

const MAX_HEIGHT_PX = 220;

interface ComposerProps {
  isBusy: boolean;
  actFilter: string;
  onActFilterChange: (value: string) => void;
  onSend: (text: string) => void;
  onStop: () => void;
}

export function Composer({ isBusy, actFilter, onActFilterChange, onSend, onStop }: ComposerProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const filterId = useId();
  const canSend = value.trim().length > 0 && !isBusy;

  // Grow with the content up to a maximum height.
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, MAX_HEIGHT_PX)}px`;
  }, [value]);

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const submit = (event?: FormEvent) => {
    event?.preventDefault();
    if (!canSend) return;
    onSend(value);
    setValue("");
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) submit(event);
  };

  return (
    <form
      onSubmit={submit}
      className={cn(
        "rounded-2xl border border-line bg-surface shadow-raised transition-colors",
        "focus-within:border-line-strong",
      )}
    >
      <label htmlFor="chat-input" className="sr-only">
        Your question
      </label>
      <textarea
        id="chat-input"
        ref={textareaRef}
        rows={1}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about South African employment, privacy, consumer or company law"
        className="block w-full resize-none bg-transparent px-4 pt-3.5 pb-2 text-[15px] leading-6 text-ink placeholder:text-ink-subtle focus:outline-none scrollbar-thin"
      />

      <div className="flex items-center justify-between gap-3 px-3 pb-3">
        <div className="flex min-w-0 items-center gap-2">
          <label htmlFor={filterId} className="text-xs whitespace-nowrap text-ink-subtle">
            Search in
          </label>
          <select
            id={filterId}
            value={actFilter}
            onChange={(e) => onActFilterChange(e.target.value)}
            className="h-8 min-w-0 cursor-pointer rounded-lg border border-line bg-surface px-2 text-[13px] text-ink-muted hover:border-line-strong focus-visible:outline-2"
          >
            {ACT_FILTERS.map((filter) => (
              <option key={filter.value} value={filter.value}>
                {filter.label}
              </option>
            ))}
          </select>
        </div>

        {isBusy ? (
          <Button variant="secondary" size="icon" onClick={onStop} aria-label="Stop generating" title="Stop generating">
            <Square aria-hidden className="size-3.5 fill-current" />
          </Button>
        ) : (
          <Button type="submit" variant="primary" size="icon" disabled={!canSend} aria-label="Send question" title="Send (Enter)">
            <ArrowUp aria-hidden className="size-4" />
          </Button>
        )}
      </div>
    </form>
  );
}
