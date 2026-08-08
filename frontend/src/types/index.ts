/** Types mirroring the backend API contract (backend/schemas/api.py). */

export interface Feedback {
  summary: string;
  strengths: string[];
  gaps: string[];
  next: string[];
  /** Extended field (not part of the spec) powering the score ring. */
  score?: number;
}

/** Spec-shaped response: `reply` + `done` plus informative extras. */
export interface InterviewResponse {
  reply: string;
  done: boolean;
  sessionId?: string;
  state?: string;
  questionNumber?: number;
  totalQuestions?: number;
  currentDay?: string | null;
  currentTopic?: string | null;
  feedback?: Feedback | null;
}

export interface CandidateSummary {
  id: string;
  name: string;
  role: string;
  experience?: number;
  education?: string;
  missionsCompleted?: number;
  missionsFirstTry?: number;
  struggles?: number;
  skipped?: number;
  failed?: number;
}

export interface SessionSnapshot {
  sessionId: string;
  candidateId: string;
  state: string;
  questionNumber: number;
  totalQuestions: number;
  interviewComplete: boolean;
  messages: Array<{ role: "candidate" | "interviewer"; text: string }>;
  feedback: Feedback | null;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  app: string;
  curriculumDays: number;
  candidates: number;
  specLoaded: boolean;
  llmConfigured: boolean;
  mockMode: boolean;
  datasetsError: string | null;
}

export interface ChatMessage {
  id: string;
  role: "candidate" | "interviewer";
  text: string;
  state?: string;
  questionNumber?: number;
  currentDay?: string | null;
  currentTopic?: string | null;
  isQuestion?: boolean;
}

/** SSE event received while a reply is being produced. */
export interface StreamEvent {
  type: "phase" | "reply" | "error";
  phase?: string;
  payload?: InterviewResponse;
  error?: { code?: string; message?: string };
}

export type Page = "landing" | "interview" | "feedback";
