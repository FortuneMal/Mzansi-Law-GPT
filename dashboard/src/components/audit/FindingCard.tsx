"use client";

import type { ReactNode } from "react";
import { Check, ChevronDown, CircleAlert, CircleCheck, CircleX, Copy } from "lucide-react";
import { useCopyToClipboard } from "@/hooks/useCopyToClipboard";
import { Badge, type Tone } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import type { Finding } from "@/lib/api";
import { cn } from "@/lib/cn";
import { toText } from "@/lib/format";
import { STATUS_LABELS } from "@/lib/report";

export const STATUS_TONES: Record<Finding["status"], Tone> = {
  "NON-COMPLIANT": "danger",
  RISK: "warning",
  COMPLIANT: "success",
};

const STATUS_ICONS = { "NON-COMPLIANT": CircleX, RISK: CircleAlert, COMPLIANT: CircleCheck } as const;

const ICON_COLORS: Record<Tone, string> = {
  danger: "text-danger",
  warning: "text-warning",
  success: "text-success",
  brand: "text-brand",
  neutral: "text-ink-subtle",
};

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <h4 className="mb-1.5 text-xs font-medium tracking-wide text-ink-subtle uppercase">{label}</h4>
      {children}
    </div>
  );
}

function Prose({ text }: { text: string }) {
  return <p className="text-sm leading-6 whitespace-pre-line text-ink-muted">{text}</p>;
}

function SuggestedWording({ text }: { text: string }) {
  const { copied, copy } = useCopyToClipboard();
  return (
    <div className="rounded-lg border border-brand/25 bg-brand-soft/60 p-3">
      <div className="mb-1.5 flex items-center justify-between gap-2">
        <h4 className="text-xs font-medium tracking-wide text-brand-ink uppercase">Suggested wording</h4>
        <Button variant="ghost" size="sm" className="h-7 px-2 text-xs" onClick={() => copy(text)}>
          {copied ? <Check aria-hidden className="size-3.5" /> : <Copy aria-hidden className="size-3.5" />}
          {copied ? "Copied" : "Copy"}
        </Button>
      </div>
      <p className="text-sm leading-6 whitespace-pre-line text-ink">{text}</p>
    </div>
  );
}

export function FindingCard({ finding }: { finding: Finding }) {
  const Icon = STATUS_ICONS[finding.status] ?? CircleAlert;
  const tone = STATUS_TONES[finding.status] ?? "neutral";
  const analysis = finding.analysis;
  const structured = typeof analysis === "object" && !analysis.error ? analysis : null;
  const fallbackText = structured ? "" : toText(typeof analysis === "object" ? analysis.raw || analysis.error : analysis);

  const clause = toText(structured?.contract_clause);
  const legalAnalysis = toText(structured?.legal_analysis);
  const plain = toText(structured?.citizen_explanation);
  const authority = toText(structured?.statutory_authority);
  const redline = finding.status === "COMPLIANT" ? "" : toText(structured?.recommended_redline);

  return (
    <details
      open={finding.status !== "COMPLIANT"}
      className="group rounded-xl border border-line bg-surface shadow-card open:border-line-strong"
    >
      <summary className="flex cursor-pointer items-center gap-3 rounded-xl px-4 py-3.5 select-none hover:bg-surface-muted sm:px-5">
        <Icon aria-hidden className={cn("size-5 shrink-0", ICON_COLORS[tone])} />
        <h3 className="min-w-0 flex-1 text-[15px] font-medium text-ink">{finding.domain}</h3>
        <Badge tone={tone}>{STATUS_LABELS[finding.status] ?? finding.status}</Badge>
        <ChevronDown aria-hidden className="size-4 shrink-0 text-ink-subtle transition-transform group-open:rotate-180" />
      </summary>

      <div className="space-y-5 border-t border-line px-4 py-5 sm:px-5">
        {structured ? (
          <>
            {plain && (
              <Field label="In plain language">
                <p className="text-[15px] leading-7 whitespace-pre-line text-ink">{plain}</p>
              </Field>
            )}
            {clause && (
              <Field label="What the contract says">
                <blockquote className="border-l-2 border-line-strong pl-3 font-serif text-[15px] leading-7 whitespace-pre-line text-ink-muted italic">
                  {clause}
                </blockquote>
              </Field>
            )}
            {legalAnalysis && (
              <Field label="Analysis">
                <Prose text={legalAnalysis} />
              </Field>
            )}
            {redline && <SuggestedWording text={redline} />}
            {authority && (
              <Field label="Legal basis">
                <Prose text={authority} />
              </Field>
            )}
          </>
        ) : (
          <Prose text={fallbackText || "No analysis was returned for this area."} />
        )}

        {finding.statutory_context_used && (
          <details className="group/ctx">
            <summary className="inline-flex cursor-pointer items-center gap-1 text-xs font-medium text-ink-subtle hover:text-ink-muted">
              <ChevronDown aria-hidden className="size-3.5 transition-transform group-open/ctx:rotate-180" />
              Legislation consulted
            </summary>
            <p className="mt-2 max-h-72 overflow-y-auto rounded-lg bg-surface-muted p-3 text-xs leading-5 whitespace-pre-line text-ink-muted scrollbar-thin">
              {finding.statutory_context_used}
            </p>
          </details>
        )}
      </div>
    </details>
  );
}
