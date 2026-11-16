"use client";

import { useRef, useState, type DragEvent } from "react";
import { FileText, Upload, X } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/cn";
import { formatFileSize } from "@/lib/format";
import { ACCEPTED_EXTENSIONS, useAudit } from "./AuditProvider";
import { CONTRACT_TYPES } from "./contractTypes";

function StepHeading({ step, title }: { step: number; title: string }) {
  return (
    <h2 className="flex items-center gap-2.5 text-sm font-semibold text-ink">
      <span className="flex size-6 items-center justify-center rounded-full bg-surface-muted text-xs text-ink-muted tabular-nums">
        {step}
      </span>
      {title}
    </h2>
  );
}

function FileDrop() {
  const { file, fileError, selectFile, clearFile } = useAudit();
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const onDrop = (event: DragEvent) => {
    event.preventDefault();
    setIsDragging(false);
    const dropped = event.dataTransfer.files?.[0];
    if (dropped) selectFile(dropped);
  };

  if (file) {
    return (
      <div className="flex items-center gap-3 rounded-xl border border-line bg-surface p-4 shadow-card">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-brand-soft text-brand-ink">
          <FileText aria-hidden className="size-5" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-ink">{file.name}</p>
          <p className="text-xs text-ink-subtle">{formatFileSize(file.size)}</p>
        </div>
        <Button variant="ghost" size="icon" onClick={clearFile} aria-label={`Remove ${file.name}`}>
          <X aria-hidden className="size-4" />
        </Button>
      </div>
    );
  }

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        className={cn(
          "flex flex-col items-center rounded-xl border border-dashed px-6 py-10 text-center transition-colors",
          isDragging ? "border-brand bg-brand-soft" : "border-line-strong bg-surface",
        )}
      >
        <div className="flex size-11 items-center justify-center rounded-full bg-surface-muted text-ink-muted">
          <Upload aria-hidden className="size-5" />
        </div>
        <p className="mt-4 text-sm font-medium text-ink">Drag your contract here</p>
        <p className="mt-1 text-xs text-ink-subtle">PDF, Word (.docx) or plain text, up to 15 MB</p>
        <Button variant="secondary" size="sm" className="mt-4" onClick={() => inputRef.current?.click()}>
          Choose a file
        </Button>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS.join(",")}
          className="sr-only"
          tabIndex={-1}
          aria-hidden
          onChange={(e) => {
            const chosen = e.target.files?.[0];
            if (chosen) selectFile(chosen);
            e.target.value = "";
          }}
        />
      </div>
      {fileError && (
        <p role="alert" className="mt-2 text-sm text-danger">
          {fileError}
        </p>
      )}
    </div>
  );
}

function ContractTypePicker() {
  const { contractType, setContractType } = useAudit();
  return (
    <fieldset>
      <legend className="sr-only">Contract type</legend>
      <div className="grid gap-2 sm:grid-cols-2">
        {CONTRACT_TYPES.map((option) => {
          const checked = option.value === contractType;
          return (
            <label
              key={option.value}
              className={cn(
                "flex cursor-pointer gap-3 rounded-xl border bg-surface p-4 shadow-card transition-colors",
                "has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-[var(--focus)]",
                checked ? "border-brand ring-1 ring-brand" : "border-line hover:border-line-strong",
              )}
            >
              <input
                type="radio"
                name="contract-type"
                value={option.value}
                checked={checked}
                onChange={() => setContractType(option.value)}
                className="mt-0.5 size-4 shrink-0 accent-[var(--brand)] focus:outline-none"
              />
              <span>
                <span className="block text-sm font-medium text-ink">{option.label}</span>
                <span className="mt-0.5 block text-xs leading-5 text-ink-subtle">{option.description}</span>
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

export function AuditSetup() {
  const { file, start } = useAudit();
  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <StepHeading step={1} title="Add the contract" />
        <FileDrop />
      </section>

      <section className="space-y-3">
        <StepHeading step={2} title="Choose the contract type" />
        <ContractTypePicker />
      </section>

      <div className="flex flex-col-reverse items-stretch gap-3 border-t border-line pt-6 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs leading-5 text-ink-subtle">
          Your document is processed by the review service and OpenAI. The uploaded file is deleted afterwards;
          the generated report, which quotes clauses, is kept on the server.
        </p>
        <Button variant="primary" onClick={start} disabled={!file}>
          Start review
        </Button>
      </div>
    </div>
  );
}
