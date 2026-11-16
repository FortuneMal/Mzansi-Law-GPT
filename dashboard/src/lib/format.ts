import type { Source } from "./api";
import { instrumentByFilename } from "./catalog";

const SMALL_WORDS = new Set(["of", "and", "the", "on", "for", "to", "in", "a", "an", "by"]);

/** "BASIC CONDITIONS OF EMPLOYMENT ACT 75 OF 1997 (BCEA)" -> "Basic Conditions of Employment Act 75 of 1997 (BCEA)". */
export function titleCase(text: string): string {
  if (text !== text.toUpperCase()) return text;
  return text
    .toLowerCase()
    .split(" ")
    .map((word, index) => {
      if (/^\(.*\)$/.test(word)) return word.toUpperCase();
      if (index > 0 && SMALL_WORDS.has(word)) return word;
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join(" ");
}

export function sourceTitle(source: Pick<Source, "act" | "source_file">): string {
  return instrumentByFilename(source.source_file)?.title ?? titleCase(source.act);
}

export function sourceShortName(source: Pick<Source, "act" | "source_file">): string {
  return instrumentByFilename(source.source_file)?.short ?? titleCase(source.act);
}

/** Ingestion labels chunks without a detected section number "Chunk_N"; show those as excerpts. */
export function sectionLabel(section: string): string | null {
  if (!section || section === "N/A" || /^chunk_/i.test(section)) return null;
  return `Section ${section}`;
}

const CONTRACT_TYPE_LABELS: Record<string, string> = {
  EMPLOYMENT: "Employment contract",
  LEASE: "Residential lease",
  CONSUMER_TERMS: "Consumer terms and conditions",
  GENERAL: "General contract",
};

export function contractTypeLabel(type: string): string {
  return CONTRACT_TYPE_LABELS[type.toUpperCase()] ?? titleCase(type.replace(/_/g, " "));
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDuration(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.floor(totalSeconds % 60);
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

/** Model JSON fields are usually strings but are not guaranteed to be; coerce safely for display. */
export function toText(value: unknown): string {
  if (value == null) return "";
  if (typeof value === "string") return value.trim();
  if (Array.isArray(value)) return value.map(toText).filter(Boolean).join("\n");
  if (typeof value === "object") {
    return Object.entries(value as Record<string, unknown>)
      .map(([k, v]) => `${k}: ${toText(v)}`)
      .join("\n");
  }
  return String(value);
}

export function createId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}
