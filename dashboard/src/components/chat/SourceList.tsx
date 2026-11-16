import { ChevronDown } from "lucide-react";
import type { Source } from "@/lib/api";
import { sectionLabel, sourceShortName, sourceTitle } from "@/lib/format";

/** The legislation excerpts an answer was grounded in. Each excerpt expands to show its text. */
export function SourceList({ sources }: { sources: Source[] }) {
  if (sources.length === 0) return null;

  return (
    <section aria-label="Sources" className="mt-5">
      <h3 className="mb-2 text-xs font-medium tracking-wide text-ink-subtle uppercase">
        Sources <span className="font-normal normal-case">({sources.length})</span>
      </h3>
      <ol className="space-y-1.5">
        {sources.map((source, index) => {
          const section = sectionLabel(source.section);
          return (
            <li key={`${source.source_file}-${source.section}-${index}`}>
              <details className="group rounded-lg border border-line bg-surface transition-colors open:border-line-strong">
                <summary className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm select-none hover:bg-surface-muted">
                  <span className="flex size-5 shrink-0 items-center justify-center rounded bg-surface-muted text-[11px] font-medium text-ink-muted tabular-nums">
                    {index + 1}
                  </span>
                  <span className="min-w-0 flex-1 truncate">
                    <span className="font-medium text-ink">{sourceShortName(source)}</span>
                    <span className="text-ink-subtle"> · {section ?? "Excerpt"}</span>
                  </span>
                  <ChevronDown
                    aria-hidden
                    className="size-4 shrink-0 text-ink-subtle transition-transform group-open:rotate-180"
                  />
                </summary>
                <div className="border-t border-line px-3 pt-2 pb-3">
                  <p className="mb-2 text-xs text-ink-subtle">{sourceTitle(source)}</p>
                  <p className="max-h-64 overflow-y-auto text-[13px] leading-6 whitespace-pre-line text-ink-muted scrollbar-thin">
                    {source.content}
                  </p>
                </div>
              </details>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
