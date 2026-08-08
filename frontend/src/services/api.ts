import type {
  CandidateSummary,
  HealthResponse,
  InterviewResponse,
  SessionSnapshot,
  StreamEvent,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new ApiError(
      0,
      "network_error",
      "Cannot reach the interview backend. Is it running on port 8000?"
    );
  }

  const body = (await response.json().catch(() => ({}))) as any;

  if (!response.ok) {
    const detail = body?.detail ?? {};
    throw new ApiError(
      response.status,
      detail.code ?? "http_error",
      detail.message ?? `Request failed with status ${response.status}`
    );
  }
  return body as T;
}

/** Generate a fresh session id client-side (the spec's start request carries it). */
export function newSessionId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2, 12)}`;
}

export interface TurnPayload {
  sessionId?: string | null;
  candidateId?: string;
  message?: string;
  /** Spec start shape: the full candidate object (id resolved server-side). */
  candidate?: { member?: { id?: string }; id?: string } | null;
}

export function sendInterviewTurn(payload: TurnPayload): Promise<InterviewResponse> {
  return request<InterviewResponse>("/api/interview", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** Parse one SSE `data:` line into a StreamEvent. */
function parseSseData(line: string): StreamEvent | null {
  const trimmed = line.trim();
  if (!trimmed.startsWith("data:")) return null;
  const raw = trimmed.slice(5).trim();
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StreamEvent;
  } catch {
    return null;
  }
}

/**
 * Drive one turn over Server-Sent Events. `onEvent` receives phase/reply
 * events as they arrive; resolves with the final reply payload.
 */
export async function sendInterviewTurnStream(
  payload: TurnPayload,
  onEvent: (event: StreamEvent) => void
): Promise<InterviewResponse | null> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/api/interview`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError(
      0,
      "network_error",
      "Cannot reach the interview backend. Is it running on port 8000?"
    );
  }

  if (!response.ok || !response.headers.get("content-type")?.includes("text/event-stream")) {
    const body = (await response.json().catch(() => ({}))) as any;
    const detail = body?.detail ?? {};
    throw new ApiError(
      response.status,
      detail.code ?? "http_error",
      detail.message ?? `Request failed with status ${response.status}`
    );
  }

  if (!response.body) throw new ApiError(0, "stream_error", "Stream unavailable.");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalPayload: InterviewResponse | null = null;

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      const event = parseSseData(line);
      if (!event) continue;
      onEvent(event);
      if (event.type === "reply" && event.payload) {
        finalPayload = event.payload;
      }
      if (event.type === "error") {
        throw new ApiError(
          0,
          event.error?.code ?? "stream_error",
          event.error?.message ?? "The interviewer ran into a problem."
        );
      }
    }
  }
  return finalPayload;
}

export function fetchCandidates(): Promise<CandidateSummary[]> {
  return request<CandidateSummary[]>("/api/candidates");
}

export function fetchSession(sessionId: string): Promise<SessionSnapshot> {
  return request<SessionSnapshot>(`/api/interview/${sessionId}`);
}

export function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/api/health");
}
