/** Types mirroring the backend API contract (backend/schemas/api.py). */

export interface Feedback {
  summary: string;
  strengths: string[];
  gaps: string[];
  next: string[];
}

export interface InterviewResponse {
  sessionId: string;
  state: string;
  message: string;
  questionNumber: number;
  totalQuestions: number;
  currentDay: string | null;
  currentTopic: string | null;
  interviewComplete: boolean;
  feedback: Feedback | null;
}

export interface CandidateSummary {
  id: string;
  name: string;
  role: string;
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

export type Page = "landing" | "interview" | "feedback";
