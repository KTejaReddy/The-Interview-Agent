// ─── Curriculum ───────────────────────────────────────────────────────────────
export interface CurriculumDay {
  day: number;
  title: string;
  type: "SETUP" | "BUILD" | "AI_CORE" | "LEARN" | "SHIP_IT" | "OPTIMIZE" | "CAPSTONE";
  tools: string[];
  objectives: string[];
}

export interface CurriculumModule {
  n: number;
  title: string;
  days: [number, number]; // [startDay, endDay] inclusive
}

export interface Curriculum {
  cohort: string;
  modules: CurriculumModule[];
  days: CurriculumDay[];
}

// ─── Candidate ────────────────────────────────────────────────────────────────
export interface CandidateMember {
  id: string;
  name: string;
  jobRole: string;
  yearsExperience: number;
  education: string;
  status: "COMPLETED" | "IN_PROGRESS";
}

export interface Mission {
  day: number;
  title: string;
  passed?: boolean;
  skipped?: boolean;
  attempts?: number;
}

export interface CandidateSignals {
  commitDays: number;
  missionsCompleted: number;
  missionsFirstTry: number;
}

export interface Candidate {
  member: CandidateMember;
  missions: Mission[];
  signals: CandidateSignals;
}

export interface CandidatesFile {
  candidates: Candidate[];
}

// ─── Session ──────────────────────────────────────────────────────────────────
export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface InterviewMessage {
  role: "interviewer" | "candidate";
  content: string;
  timestamp: string;
  dayReference?: number;
  questionType?: "opening" | "technical" | "follow_up" | "probing" | "synthesis" | "closing";
}

export interface InterviewSession {
  sessionId: string;
  candidateId: string;
  candidate: Candidate;
  createdAt: number;           // Date.now()
  lastActivityAt: number;
  status: "active" | "completed" | "expired";
  messages: InterviewMessage[];   // Full display transcript
  groqHistory: ChatMessage[];     // Sent to Groq — rolling window of last 12
  questionsAsked: number;
  daysCovered: Set<number>;
  currentDayFocus?: number;
  interviewComplete: boolean;
  feedback?: FeedbackReport;
}

// ─── API Contract (from technical-spec.md — use EXACTLY) ─────────────────────

// Start Interview Request (first call — no message field)
export interface StartInterviewRequest {
  sessionId: string;
  candidate: Candidate;         // Full candidate object from candidates.json
}

// Conversation Turn Request (subsequent calls)
export interface TurnRequest {
  sessionId: string;
  message: string;              // Candidate's response text
}

// Union type for route handler
export type InterviewRequest = StartInterviewRequest | TurnRequest;

// Response for ongoing interview (done: false)
export interface OngoingInterviewResponse {
  reply: string;
  done: false;
}

// Response when interview is complete (done: true)
export interface CompletedInterviewResponse {
  reply: string;
  done: true;
  feedback: {
    summary: string;
    strengths: string[];
    gaps: string[];
    next: string[];
  };
}

export type InterviewResponse = OngoingInterviewResponse | CompletedInterviewResponse;

// ─── Feedback ─────────────────────────────────────────────────────────────────
export interface FeedbackReport {
  summary: string;
  strengths: string[];
  gaps: string[];
  next: string[];
  // Extended fields for the UI (not part of the API contract)
  overallScore?: number;
  topicScores?: { topic: string; day: number; score: number; note: string }[];
  recommendation?: "strong_hire" | "hire" | "consider" | "needs_growth";
}
