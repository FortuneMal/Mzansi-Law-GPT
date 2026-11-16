"use client";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { PageHeader } from "@/components/shell/PageHeader";
import { useAudit } from "./AuditProvider";
import { AuditResults } from "./AuditResults";
import { AuditRunning } from "./AuditRunning";
import { AuditSetup } from "./AuditSetup";

export function AuditView() {
  const { phase, start } = useAudit();

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6 sm:py-12">
      <PageHeader
        title="Contract review"
        description="Upload an employment contract, residential lease or consumer terms. Each relevant compliance area is checked against South African legislation, with plain-language findings and suggested wording."
      />

      {phase.name === "running" && <AuditRunning startedAt={phase.startedAt} />}
      {phase.name === "done" && <AuditResults result={phase.result} />}
      {(phase.name === "idle" || phase.name === "error") && (
        <div className="space-y-6">
          {phase.name === "error" && (
            <Alert
              tone="danger"
              title="The review could not be completed"
              action={
                <Button variant="secondary" size="sm" onClick={start}>
                  Try again
                </Button>
              }
            >
              {phase.message}
            </Alert>
          )}
          <AuditSetup />
        </div>
      )}
    </div>
  );
}
