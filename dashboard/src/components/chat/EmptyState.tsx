import { ArrowUpRight } from "lucide-react";

/** Starter questions chosen from topics the indexed legislation actually covers. */
const SUGGESTIONS = [
  { topic: "Employment", question: "How much overtime can my employer require, and how must it be paid?" },
  { topic: "Privacy", question: "What must a company do if customer data is accessed without authorisation?" },
  { topic: "Consumer rights", question: "Can I cancel a contract I signed after a direct marketing call?" },
  { topic: "Companies", question: "When may a company's board start business rescue proceedings?" },
];

export function EmptyState({ onPick }: { onPick: (question: string) => void }) {
  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col items-center px-1 pt-10 pb-6 text-center sm:pt-20">
      <h1 className="font-serif text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
        What would you like to know?
      </h1>
      <p className="mt-3 max-w-lg text-[15px] leading-7 text-ink-muted">
        Ask a question about South African law. Answers are drawn from excerpts of legislation and list the
        sources they rely on.
      </p>

      <ul className="mt-10 grid w-full gap-3 text-left sm:grid-cols-2">
        {SUGGESTIONS.map((s) => (
          <li key={s.question}>
            <button
              type="button"
              onClick={() => onPick(s.question)}
              className="group flex h-full w-full flex-col gap-1.5 rounded-xl border border-line bg-surface p-4 shadow-card transition-colors hover:border-line-strong hover:bg-surface-muted"
            >
              <span className="flex items-center justify-between text-xs font-medium text-brand-ink">
                {s.topic}
                <ArrowUpRight
                  aria-hidden
                  className="size-3.5 text-ink-subtle transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
                />
              </span>
              <span className="text-sm leading-6 text-ink">{s.question}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
