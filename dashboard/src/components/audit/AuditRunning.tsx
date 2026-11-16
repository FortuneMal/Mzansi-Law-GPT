"use client";

import { useElapsedSeconds } from "@/hooks/useElapsedSeconds";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { formatDuration } from "@/lib/format";
import { useAudit } from "./AuditProvider";
import { CONTRACT_TYPES } from "./contractTypes";

/**
 * The API does not report progress, so this shows honest status (elapsed time and what is being
 * checked) rather than a simulated percentage.
 */
export function AuditRunning({ startedAt }: { startedAt: number }) {
  const { file, contractType, cancel } = useAudit();
  const elapsed = useElapsedSeconds(startedAt);
  const option = CONTRACT_TYPES.find((t) => t.value === contractType);

  return (
    <section
      aria-live="polite"
      aria-busy="true"
      className="rounded-2xl border border-line bg-surface p-6 shadow-card sm:p-8"
    >
      <div className="flex items-start gap-4">
        <Spinner className="mt-1 size-5 text-brand" />
        <div className="min-w-0 flex-1">
          <h2 className="text-base font-semibold text-ink">Reviewing {file?.name ?? "your contract"}</h2>
          <p className="mt-1 text-sm text-ink-muted">
            This usually takes under a minute. Keep this page open.{" "}
            <span className="text-ink-subtle tabular-nums">Elapsed {formatDuration(elapsed)}</span>
          </p>
        </div>
      </div>

      <div className="mt-6 rounded-xl bg-surface-muted p-4">
        <p className="text-xs font-medium tracking-wide text-ink-subtle uppercase">Being checked</p>
        {option && option.areas.length > 0 ? (
          <ul className="mt-2 space-y-1.5 text-sm text-ink-muted">
            {option.areas.map((area) => (
              <li key={area} className="flex items-center gap-2">
                <span aria-hidden className="size-1.5 rounded-full bg-line-strong" />
                {area}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-sm text-ink-muted">
            Detecting the contract type, then checking the compliance areas that apply to it.
          </p>
        )}
      </div>

      <div className="mt-6 flex justify-end">
        <Button variant="ghost" size="sm" onClick={cancel}>
          Cancel
        </Button>
      </div>
    </section>
  );
}
