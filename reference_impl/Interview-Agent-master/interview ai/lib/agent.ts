import { InterviewSession, Candidate, InterviewMessage } from "@/types";
import { groqChat, groqChatStream } from "./groq";
import { buildSystemPrompt, buildFeedbackPrompt } from "./prompts";
import { createSession, getSession, updateSession } from "./session";
import { generateFeedback } from "./feedback";
import { getPassedMissions } from "./candidates";

const MIN_QUESTIONS = parseInt(process.env.MIN_QUESTIONS_REQUIRED || "8");
const MIN_DAYS = parseInt(process.env.MIN_DAYS_REQUIRED || "4");
const MAX_QUESTIONS = parseInt(process.env.MAX_QUESTIONS_PER_SESSION || "14");

/**
 * Initialize a brand new interview session.
 * Called when the request has no prior session history (start interview).
 * Pass `onToken` to stream the opening message to the client as it is generated.
 */
export async function startInterview(
  sessionId: string,
  candidate: Candidate,
  onToken?: (delta: string) => void
): Promise<{ reply: string; session: InterviewSession }> {
  const session = createSession(sessionId, candidate);

  // Build the system prompt with full candidate context
  const systemPrompt = buildSystemPrompt(candidate);

  // Initialize Groq history with system prompt
  session.groqHistory = [
    { role: "system", content: systemPrompt },
    {
      role: "user",
      content: `Please begin the interview. Greet ${candidate.member.name} professionally, introduce yourself as Alex, mention this is a technical interview covering their ABTalks AI Cohort work, and ask your first question.`,
    },
  ];

  // Get opening from Groq (streamed to the client when onToken is provided)
  const reply = onToken
    ? await groqChatStream(session.groqHistory, 0.7, 400, onToken)
    : await groqChat(session.groqHistory, 0.7, 400);

  // Add assistant reply to history
  session.groqHistory.push({ role: "assistant", content: reply });

  // Track in display messages
  session.messages.push({
    role: "interviewer",
    content: reply,
    timestamp: new Date().toISOString(),
    questionType: "opening",
  });

  session.questionsAsked = 1;
  updateSession(session);

  return { reply, session };
}

/**
 * Process a candidate's response and generate the next interviewer message.
 * Pass `onToken` to stream the reply to the client as it is generated.
 */
export async function processResponse(
  session: InterviewSession,
  candidateMessage: string,
  onToken?: (delta: string) => void
): Promise<{ reply: string; done: boolean; session: InterviewSession }> {
  // Record candidate message in display transcript
  session.messages.push({
    role: "candidate",
    content: candidateMessage,
    timestamp: new Date().toISOString(),
  });

  // Add candidate response to Groq history
  session.groqHistory.push({ role: "user", content: candidateMessage });

  // Keep Groq history bounded — system prompt + last 12 messages
  if (session.groqHistory.length > 13) {
    const systemMsg = session.groqHistory[0]; // always keep system prompt
    session.groqHistory = [systemMsg, ...session.groqHistory.slice(-12)];
  }

  // Get next interviewer message from Groq (streamed when onToken is provided)
  const rawReply = onToken
    ? await groqChatStream(session.groqHistory, 0.7, 600, onToken)
    : await groqChat(session.groqHistory, 0.7, 600);

  // Honor an explicit request to wrap up once the minimum is met (the
  // "End Interview" button sends a fixed message; a natural phrasing works too)
  const endRequested =
    /(?:wrap up|end|stop|conclude)(?: the)?(?: interview|session|our session)/i.test(
      candidateMessage
    ) && session.questionsAsked >= MIN_QUESTIONS;

  // Check if the interview is signaling completion — or the hard cap is hit
  const isComplete =
    endRequested ||
    (rawReply.includes("[INTERVIEW_COMPLETE]") &&
      session.questionsAsked >= MIN_QUESTIONS &&
      session.daysCovered.size >= MIN_DAYS) ||
    session.questionsAsked >= MAX_QUESTIONS;

  // Strip the completion marker from the displayed message
  const cleanReply = rawReply.replace("[INTERVIEW_COMPLETE]", "").trim();

  // Parse which day was just covered (look for "Day X" in the reply)
  const dayMatch = rawReply.match(/Day (\d+)/i);
  if (dayMatch) {
    session.daysCovered.add(parseInt(dayMatch[1]));
  }

  // Add to Groq history
  session.groqHistory.push({ role: "assistant", content: cleanReply });

  // Add to display messages
  session.messages.push({
    role: "interviewer",
    content: cleanReply,
    timestamp: new Date().toISOString(),
    questionType: isComplete ? "closing" : "technical",
  });

  session.questionsAsked += 1;

  if (isComplete) {
    session.interviewComplete = true;
    session.status = "completed";
  }

  updateSession(session);
  return { reply: cleanReply, done: isComplete, session };
}
