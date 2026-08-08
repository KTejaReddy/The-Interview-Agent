import { InterviewSession, Candidate } from "@/types";

// Global session map — survives across API calls within the same process
const sessions = new Map<string, InterviewSession>();

const SESSION_TIMEOUT_MS = parseInt(process.env.SESSION_TIMEOUT_MS || "7200000");

export function createSession(sessionId: string, candidate: Candidate): InterviewSession {
  const session: InterviewSession = {
    sessionId,
    candidateId: candidate.member.id,
    candidate,
    createdAt: Date.now(),
    lastActivityAt: Date.now(),
    status: "active",
    messages: [],
    groqHistory: [],
    questionsAsked: 0,
    daysCovered: new Set(),
    interviewComplete: false,
  };
  sessions.set(sessionId, session);
  return session;
}

export function getSession(sessionId: string): InterviewSession | null {
  const session = sessions.get(sessionId);
  if (!session) return null;

  // Check expiry
  if (Date.now() - session.lastActivityAt > SESSION_TIMEOUT_MS) {
    session.status = "expired";
    return null;
  }

  return session;
}

export function updateSession(session: InterviewSession): void {
  session.lastActivityAt = Date.now();
  sessions.set(session.sessionId, session);
}

export function getAllSessions(): InterviewSession[] {
  return Array.from(sessions.values());
}
