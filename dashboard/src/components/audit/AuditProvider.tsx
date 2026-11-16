"use client";

import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from "react";
import { ApiError, auditContract, isAbortError, type AuditResult, type ContractType } from "@/lib/api";

export const ACCEPTED_EXTENSIONS = [".pdf", ".docx", ".txt"];
export const MAX_FILE_BYTES = 15 * 1024 * 1024;

export type AuditPhase =
  | { name: "idle" }
  | { name: "running"; startedAt: number }
  | { name: "done"; result: AuditResult }
  | { name: "error"; message: string };

interface AuditContextValue {
  file: File | null;
  fileError: string | null;
  contractType: ContractType;
  phase: AuditPhase;
  selectFile: (file: File) => void;
  clearFile: () => void;
  setContractType: (type: ContractType) => void;
  start: () => void;
  cancel: () => void;
  startOver: () => void;
}

const AuditContext = createContext<AuditContextValue | null>(null);

function validateFile(file: File): string | null {
  const name = file.name.toLowerCase();
  if (!ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext))) {
    return "Choose a PDF, Word (.docx) or plain text (.txt) file.";
  }
  if (file.size === 0) return "This file is empty.";
  if (file.size > MAX_FILE_BYTES) return "This file is larger than 15 MB. Try a smaller or text-only version.";
  return null;
}

export function AuditProvider({ children }: { children: ReactNode }) {
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [contractType, setContractType] = useState<ContractType>("auto");
  const [phase, setPhase] = useState<AuditPhase>({ name: "idle" });
  const controllerRef = useRef<AbortController | null>(null);

  const selectFile = useCallback((candidate: File) => {
    const error = validateFile(candidate);
    setFileError(error);
    setFile(error ? null : candidate);
    setPhase({ name: "idle" });
  }, []);

  const clearFile = useCallback(() => {
    setFile(null);
    setFileError(null);
  }, []);

  const start = useCallback(async () => {
    if (!file || controllerRef.current) return;
    const controller = new AbortController();
    controllerRef.current = controller;
    setPhase({ name: "running", startedAt: Date.now() });
    try {
      const result = await auditContract(file, contractType, controller.signal);
      setPhase({ name: "done", result });
    } catch (error) {
      if (isAbortError(error)) {
        setPhase({ name: "idle" });
      } else {
        setPhase({
          name: "error",
          message: error instanceof ApiError ? error.message : "The review could not be completed. Please try again.",
        });
      }
    } finally {
      controllerRef.current = null;
    }
  }, [file, contractType]);

  const cancel = useCallback(() => controllerRef.current?.abort(), []);

  const startOver = useCallback(() => {
    controllerRef.current?.abort();
    setFile(null);
    setFileError(null);
    setPhase({ name: "idle" });
  }, []);

  const value = useMemo<AuditContextValue>(
    () => ({
      file,
      fileError,
      contractType,
      phase,
      selectFile,
      clearFile,
      setContractType,
      start: () => void start(),
      cancel,
      startOver,
    }),
    [file, fileError, contractType, phase, selectFile, clearFile, start, cancel, startOver],
  );

  return <AuditContext.Provider value={value}>{children}</AuditContext.Provider>;
}

export function useAudit(): AuditContextValue {
  const context = useContext(AuditContext);
  if (!context) throw new Error("useAudit must be used inside <AuditProvider>");
  return context;
}
