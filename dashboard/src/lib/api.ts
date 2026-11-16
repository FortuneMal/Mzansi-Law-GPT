/**
 * Typed client for the Mzansi Law GPT FastAPI backend.
 * All network access from the dashboard goes through this module.
 */

export const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");

/** Collection the chat endpoints search. Kept explicit so the request body matches the API contract. */
const CHAT_COLLECTION = "mzansi_law_acts_v2";

// ---------------------------------------------------------------------------
// Types mirroring the API schema
// ---------------------------------------------------------------------------

export interface Source {
  act: string;
  section: string;
  content: string;
  source_file: string;
}

export interface HistoryMessage {
  role: "user" | "assistant";
  content: string;
}

export type ChatEvent =
  | { type: "sources"; sources: Source[]; timestamp: string }
  | { type: "delta"; content: string }
  | { type: "done" }
  | { type: "error"; detail: string };

export type FindingStatus = "COMPLIANT" | "NON-COMPLIANT" | "RISK";

export interface FindingAnalysis {
  status?: string;
  statutory_authority?: unknown;
  contract_clause?: unknown;
  legal_analysis?: unknown;
  citizen_explanation?: unknown;
  recommended_redline?: unknown;
  error?: string;
  raw?: string;
}

export interface Finding {
  domain: string;
  status: FindingStatus;
  analysis: FindingAnalysis | string;
  statutory_context_used: string;
}

export interface AuditResult {
  document_name: string;
  contract_type: string;
  overall_status: "PASSED" | "FAILED";
  violation_count: number;
  findings: Finding[];
  report_url?: string | null;
  timestamp: string;
}

export type ContractType = "auto" | "employment" | "lease" | "consumer_terms";

export interface ActInfo {
  key: string;
  title: string;
  filename: string;
  url: string;
}

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  constructor(message: string, readonly status?: number) {
    super(message);
    this.name = "ApiError";
  }
}

export function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

const UNREACHABLE_MESSAGE =
  "We couldn't reach the server. It may be starting up after a period of inactivity; please try again in a moment.";

async function request(path: string, init: RequestInit): Promise<Response> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init);
  } catch (error) {
    if (isAbortError(error)) throw error;
    throw new ApiError(UNREACHABLE_MESSAGE);
  }
  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response), response.status);
  }
  return response;
}

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body?.detail === "string" && body.detail.trim()) return body.detail;
  } catch {
    // Body was not JSON; fall through to the generic message.
  }
  return `The server returned an error (${response.status}). Please try again.`;
}

// ---------------------------------------------------------------------------
// Endpoints
// ---------------------------------------------------------------------------

/** Fire-and-forget request that wakes a sleeping backend (e.g. Render free tier) before the user needs it. */
export function wakeBackend(): void {
  fetch(`${API_BASE_URL}/api/health`).catch(() => undefined);
}

/**
 * Streams a chat answer. Yields the newline-delimited JSON events emitted by /api/chat/stream:
 * one "sources" event, then "delta" events, then a final "done" or "error".
 */
export async function* streamChat(
  params: { query: string; history: HistoryMessage[]; actFilter: string },
  signal: AbortSignal,
): AsyncGenerator<ChatEvent> {
  const response = await request("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: params.query,
      history: params.history,
      act_filter: params.actFilter,
      collection_name: CHAT_COLLECTION,
      force_local: false,
    }),
    signal,
  });
  if (!response.body) throw new ApiError("The server returned an empty response.");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        if (line.trim()) yield JSON.parse(line) as ChatEvent;
      }
    }
    buffer += decoder.decode();
    if (buffer.trim()) yield JSON.parse(buffer) as ChatEvent;
  } finally {
    reader.releaseLock();
  }
}

export async function auditContract(file: File, contractType: ContractType, signal: AbortSignal): Promise<AuditResult> {
  const form = new FormData();
  form.append("file", file);
  form.append("contract_type", contractType);
  form.append("force_local", "false");
  const response = await request("/api/audit", { method: "POST", body: form, signal });
  return (await response.json()) as AuditResult;
}

export async function fetchActs(signal: AbortSignal): Promise<ActInfo[]> {
  const response = await request("/api/acts", { signal });
  const body = await response.json();
  return Array.isArray(body?.acts) ? (body.acts as ActInfo[]) : [];
}
