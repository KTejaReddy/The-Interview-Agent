import type {
  CandidateSummary,
  HealthResponse,
  InterviewResponse,
  SessionSnapshot,
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

export function sendInterviewTurn(payload: {
  sessionId?: string | null;
  candidateId: string;
  message: string;
}): Promise<InterviewResponse> {
  return request<InterviewResponse>("/api/interview", {
    method: "POST",
    body: JSON.stringify(payload),
  });
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
