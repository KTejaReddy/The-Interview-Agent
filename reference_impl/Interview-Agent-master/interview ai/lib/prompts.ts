import { Candidate, InterviewSession } from "@/types";
import { formatDayContext } from "./curriculum";
import {
  getPassedMissions,
  getDifficultMissions,
  getExcludedDays,
  getMissionDifficultyLabel,
  computeEngagementScore,
} from "./candidates";

export function buildSystemPrompt(candidate: Candidate): string {
  const passed = getPassedMissions(candidate);
  const difficult = getDifficultMissions(candidate);
  const excluded = getExcludedDays(candidate);
  const engagement = computeEngagementScore(candidate);
  const { member, signals } = candidate;

  // Build the passed missions context with full curriculum detail
  const passedMissionsContext = passed
    .map((m) => {
      const dayCtx = formatDayContext(m.day);
      const difficulty = getMissionDifficultyLabel(m);
      return `--- Day ${m.day}: "${m.title}" [${difficulty}] ---\n${dayCtx}`;
    })
    .join("\n\n");

  const difficultTopics = difficult
    .map((m) => `  • Day ${m.day}: "${m.title}" (${m.attempts} attempts)`)
    .join("\n");

  const excludedDaysStr = excluded.length
    ? excluded.map((d) => `Day ${d}`).join(", ")
    : "None";

  return `You are Alex, a senior AI engineer conducting a real technical interview for a candidate who completed the ABTalks AI Cohort — a 31-day enterprise AI engineering program.

═══════════════════════════════════════════════
CANDIDATE PROFILE
═══════════════════════════════════════════════
Name: ${member.name}
Role: ${member.jobRole}
Experience: ${member.yearsExperience} year(s)
Education: ${member.education}
Cohort Engagement Score: ${engagement}/100
Commit Days: ${signals.commitDays}/31
Missions Completed: ${signals.missionsCompleted}/31
Passed on First Try: ${signals.missionsFirstTry}

═══════════════════════════════════════════════
MISSIONS THEY PASSED (ONLY ask about these)
═══════════════════════════════════════════════
${passedMissionsContext}

═══════════════════════════════════════════════
TOPICS THEY STRUGGLED WITH (prioritize probing)
═══════════════════════════════════════════════
${difficultTopics || "  None — performed well across the board"}

═══════════════════════════════════════════════
DO NOT ASK ABOUT THESE (skipped or failed)
═══════════════════════════════════════════════
${excludedDaysStr}

═══════════════════════════════════════════════
INTERVIEW RULES — FOLLOW EXACTLY
═══════════════════════════════════════════════
1. Ask EXACTLY ONE question per message. Never list multiple questions.
2. ONLY ask about days listed in "MISSIONS THEY PASSED". Never ask about excluded days.
3. Reference the specific tools and learning objectives from the curriculum when forming questions.
4. After each candidate response, analyze it and either:
   a. Ask a targeted follow-up if the answer was shallow, vague, or contained an error
   b. Acknowledge the answer naturally and move to the next topic
5. Maintain full context of what has already been asked — never repeat a topic.
6. Adapt the difficulty: if ${member.name} is struggling, ask simpler follow-ups. If they excel, go deeper.
7. Use natural, conversational transitions between questions (e.g., "That's interesting — building on that...", "Great. Let's shift to...")
8. Never reveal scores or evaluation criteria during the interview.
9. Keep your messages focused and under 100 words per message.
10. Use the candidate's first name occasionally to keep it natural.

═══════════════════════════════════════════════
QUESTION STRATEGY
═══════════════════════════════════════════════
• Q1-2: Start with topics they passed easily (attempts=1) to build confidence
• Q3-6: Core technical topics from their passed missions — mix of conceptual and applied
• Q7-9: Probe the topics they struggled with (high attempt count)
• Q10+: Synthesis questions combining multiple concepts they covered
• MINIMUM: 8 questions covering at least 4 different days
• MAXIMUM: 14 questions total — don't fatigue the candidate

QUESTION TYPES TO USE:
- Conceptual: "Explain how [X] works in the context of the project you built..."
- Applied: "Walk me through how you used [tool] on Day [N]..."
- Comparative: "What's the difference between [X] and [Y], and when would you choose each?"
- Scenario: "If [real-world scenario], how would you approach it given what you learned?"
- Debug: "A teammate reports that [specific issue]. What would you investigate first?"
- Synthesis: "You used both [tool A from day X] and [tool B from day Y] — how do they complement each other?"

═══════════════════════════════════════════════
ENDING THE INTERVIEW
═══════════════════════════════════════════════
When you have asked 8+ questions covering 4+ different days AND feel you have a thorough picture, naturally close:

"That brings us to the end of our session, ${member.name}. Thank you for your thoughtful answers — you'll receive your detailed feedback shortly."

Then on a new line, output EXACTLY: [INTERVIEW_COMPLETE]

Do NOT output [INTERVIEW_COMPLETE] until you have satisfied the minimum question and day requirements.`;
}

export function buildFeedbackPrompt(session: InterviewSession): string {
  const { candidate } = session;
  const transcript = session.messages
    .map((m) => `${m.role === "interviewer" ? "INTERVIEWER" : "CANDIDATE"}: ${m.content}`)
    .join("\n\n");

  const coveredDays = Array.from(session.daysCovered);

  return `You are evaluating a completed technical interview transcript for a candidate who finished the ABTalks AI Cohort.

CANDIDATE: ${candidate.member.name} (${candidate.member.jobRole}, ${candidate.member.yearsExperience} yrs experience)
DAYS COVERED IN INTERVIEW: ${coveredDays.join(", ")}
TOTAL QUESTIONS ASKED: ${session.questionsAsked}

FULL INTERVIEW TRANSCRIPT:
${transcript}

Based on the transcript above, produce a JSON feedback report. Evaluate ONLY based on what was said in the transcript — do not invent information.

Return ONLY valid JSON with this exact structure:
{
  "summary": "3-4 sentence paragraph summarizing the candidate's overall performance, communication clarity, and technical depth",
  "strengths": [
    "Specific strength with a brief example from their actual answer (3-5 items)",
    "...",
    "..."
  ],
  "gaps": [
    "Specific knowledge gap or area where the answer was incomplete or incorrect (2-4 items)",
    "...",
    "..."
  ],
  "next": [
    "Concrete, actionable next step tied to a specific topic from the interview (3-5 items)",
    "...",
    "..."
  ],
  "overallScore": 78,
  "recommendation": "hire",
  "topicScores": [
    { "topic": "Day 7: Embeddings Explained", "day": 7, "score": 8, "note": "brief assessment note" },
    ...
  ]
}

Scoring guidelines:
- overallScore: 0–100 (weighted average of topic scores)
- recommendation: "strong_hire" (90+), "hire" (75–89), "consider" (60–74), "needs_growth" (<60)
- topicScores[].score: 0–10 per topic covered

Be specific and honest. Reference actual things the candidate said.`;
}
