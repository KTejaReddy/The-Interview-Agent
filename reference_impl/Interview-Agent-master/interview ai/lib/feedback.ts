import { InterviewSession } from "@/types";
import { groqChat } from "./groq";
import { buildFeedbackPrompt } from "./prompts";
import { z } from "zod";

/**
 * Zod schema for the structured feedback the LLM is asked to produce.
 * Used to validate / normalize the model output so the API contract
 * (summary, strengths, gaps, next) is always satisfied.
 */
const feedbackSchema = z
  .object({
    summary: z.string().min(1).catch(""),
    strengths: z.array(z.string()).catch([]),
    gaps: z.array(z.string()).catch([]),
    next: z.array(z.string()).catch([]),
    overallScore: z.coerce.number().min(0).max(100).optional(),
    recommendation: z
      .enum(["strong_hire", "hire", "consider", "needs_growth"])
      .optional(),
    topicScores: z
      .array(
        z.object({
          topic: z.string(),
          day: z.number(),
          score: z.coerce.number().min(0).max(10),
          note: z.string(),
        })
      )
      .optional(),
  })
  .catch({
    summary: "",
    strengths: [],
    gaps: [],
    next: [],
  });

export interface FeedbackResult {
  summary: string;
  strengths: string[];
  gaps: string[];
  next: string[];
  overallScore?: number;
  recommendation?: string;
  topicScores?: any[];
}

export async function generateFeedback(
  session: InterviewSession
): Promise<FeedbackResult> {
  const prompt = buildFeedbackPrompt(session);

  // Use low temperature for deterministic, structured feedback
  const raw = await groqChat(
    [
      { role: "system", content: "You are a technical interview evaluator. Respond with valid JSON only." },
      { role: "user", content: prompt },
    ],
    0.1,  // Very low temperature — we want consistent, grounded feedback
    2000
  );

  // Parse JSON from the response — handle edge cases
  try {
    // Extract JSON from the response (Groq sometimes wraps in markdown code blocks)
    const jsonMatch = raw.match(/\{[\s\S]*\}/);
    if (!jsonMatch) throw new Error("No JSON found in response");

    // Validate + normalize with zod so the contract fields always exist
    const parsed = feedbackSchema.parse(JSON.parse(jsonMatch[0]));
    return {
      summary: parsed.summary,
      strengths: parsed.strengths,
      gaps: parsed.gaps,
      next: parsed.next,
      overallScore: parsed.overallScore,
      recommendation: parsed.recommendation,
      topicScores: parsed.topicScores,
    };
  } catch (e) {
    // Fallback if JSON parsing fails
    console.error("Feedback JSON parse error:", e);
    return {
      summary: raw.slice(0, 500),
      strengths: ["Completed the interview session"],
      gaps: ["Detailed feedback unavailable — please try again"],
      next: ["Review the cohort curriculum materials"],
    };
  }
}
