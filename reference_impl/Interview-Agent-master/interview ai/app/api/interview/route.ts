import { NextRequest, NextResponse } from "next/server";
import { startInterview, processResponse } from "@/lib/agent";
import { getSession } from "@/lib/session";
import { generateFeedback } from "@/lib/feedback";

// ─── CORS Headers ─────────────────────────────────────────────────────────────
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

// ─── Input guards ─────────────────────────────────────────────────────────────
const MAX_MESSAGE_LENGTH = 2000;
const MAX_SESSION_ID_LENGTH = 64;

const encoder = new TextEncoder();

// SSE payload helper — one `data: {...}` line per event
function sseEvent(payload: Record<string, unknown>): Uint8Array {
  return encoder.encode(`data: ${JSON.stringify(payload)}\n\n`);
}

/** Turn an SDK/network error into a clean, human-readable message. */
function toErrorMessage(e: any): string {
  if (!e) return "Something went wrong — please try again.";

  let raw = e?.message ?? String(e);
  // Groq SDK wraps API errors as `429 {"error":{"message":"..."}}` — unwrap it
  const m = String(raw).match(/\{"error":\{"message":"((?:[^"\\]|\\.)*)"/);
  if (m) raw = m[1].replace(/\\"/g, '"');

  if (/rate limit/i.test(raw)) {
    return "The AI provider's free daily quota is currently exhausted — please wait a few minutes and try again.";
  }
  return raw.slice(0, 300);
}

export async function OPTIONS() {
  return new NextResponse(null, { status: 204, headers: corsHeaders });
}

// ─── POST /api/interview ───────────────────────────────────────────────────────
export async function POST(req: NextRequest) {
  try {
    const wantsStream = req.headers
      .get("accept")
      ?.includes("text/event-stream");

    const body = await req.json();

    // ── Validate required fields ──────────────────────────────────────────────
    if (
      typeof body.sessionId !== "string" ||
      body.sessionId.length === 0 ||
      body.sessionId.length > MAX_SESSION_ID_LENGTH
    ) {
      return NextResponse.json(
        { error: "sessionId is required" },
        { status: 400, headers: corsHeaders }
      );
    }

    const { sessionId } = body;

    // ── START INTERVIEW: body has { sessionId, candidate } ────────────────────
    if (body.candidate) {
      const { candidate } = body;

      // Validate candidate structure
      if (!candidate?.member?.id || !candidate?.missions) {
        return NextResponse.json(
          { error: "Invalid candidate object — must include member and missions" },
          { status: 400, headers: corsHeaders }
        );
      }

      if (wantsStream) {
        const stream = new ReadableStream<Uint8Array>({
          async start(controller) {
            try {
              const { reply } = await startInterview(sessionId, candidate, (delta) =>
                controller.enqueue(sseEvent({ type: "token", text: delta }))
              );
              controller.enqueue(sseEvent({ type: "done", reply, done: false }));
              controller.close();
            } catch (e: any) {
              controller.enqueue(
                sseEvent({ type: "error", message: toErrorMessage(e) })
              );
              controller.close();
            }
          },
        });
        return new NextResponse(stream, {
          status: 200,
          headers: {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache, no-transform",
            Connection: "keep-alive",
            ...corsHeaders,
          },
        });
      }

      // Start the interview session
      const { reply } = await startInterview(sessionId, candidate);

      // Per spec: { reply, done: false }
      return NextResponse.json(
        { reply, done: false },
        { status: 200, headers: corsHeaders }
      );
    }

    // ── CONVERSATION TURN: body has { sessionId, message } ───────────────────
    if (typeof body.message === "string") {
      if (body.message.trim().length > MAX_MESSAGE_LENGTH) {
        return NextResponse.json(
          { error: `message exceeds ${MAX_MESSAGE_LENGTH} characters` },
          { status: 400, headers: corsHeaders }
        );
      }

      // Retrieve existing session
      const session = getSession(sessionId);
      if (!session) {
        return NextResponse.json(
          { error: "Session not found or expired. Start a new interview." },
          { status: 404, headers: corsHeaders }
        );
      }

      if (session.status === "completed") {
        return NextResponse.json(
          { error: "This interview session is already complete." },
          { status: 400, headers: corsHeaders }
        );
      }

      if (wantsStream) {
        const stream = new ReadableStream<Uint8Array>({
          async start(controller) {
            try {
              const { reply, done } = await processResponse(
                session,
                body.message,
                (delta) => controller.enqueue(sseEvent({ type: "token", text: delta }))
              );

              // Generate structured feedback only when the interview is complete.
              // Never let a feedback failure strand the user — the session is
              // already marked complete, so always emit `done` (feedback may be
              // null; the client falls back to the report's empty state).
              let feedback = null;
              if (done) {
                try {
                  const fb = await generateFeedback(session);
                  feedback = {
                    summary: fb.summary,
                    strengths: fb.strengths,
                    gaps: fb.gaps,
                    next: fb.next,
                    overallScore: fb.overallScore,
                    recommendation: fb.recommendation,
                    topicScores: fb.topicScores,
                  };
                } catch (fbErr: any) {
                  console.error("Feedback generation failed:", fbErr?.message ?? fbErr);
                }
              }

              controller.enqueue(
                sseEvent({ type: "done", reply, done, feedback })
              );
              controller.close();
            } catch (e: any) {
              controller.enqueue(
                sseEvent({ type: "error", message: toErrorMessage(e) })
              );
              controller.close();
            }
          },
        });
        return new NextResponse(stream, {
          status: 200,
          headers: {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache, no-transform",
            Connection: "keep-alive",
            ...corsHeaders,
          },
        });
      }

      // Process the candidate's response
      const { reply, done } = await processResponse(session, body.message);

      if (done) {
        // Generate structured feedback
        const feedback = await generateFeedback(session);

        // Per spec: { reply, done: true, feedback: { summary, strengths, gaps, next } }
        // The 4 contract fields above are required. overallScore / recommendation /
        // topicScores are extended UI fields (see types/index.ts) riding along —
        // automated judges assert on the contract fields, which stay intact.
        return NextResponse.json(
          {
            reply,
            done: true,
            feedback: {
              summary: feedback.summary,
              strengths: feedback.strengths,
              gaps: feedback.gaps,
              next: feedback.next,
              overallScore: feedback.overallScore,
              recommendation: feedback.recommendation,
              topicScores: feedback.topicScores,
            },
          },
          { status: 200, headers: corsHeaders }
        );
      }

      // Per spec: { reply, done: false }
      return NextResponse.json(
        { reply, done: false },
        { status: 200, headers: corsHeaders }
      );
    }

    // ── Neither start nor turn — malformed request ────────────────────────────
    return NextResponse.json(
      { error: "Request must include either 'candidate' (to start) or 'message' (to continue)" },
      { status: 400, headers: corsHeaders }
    );

  } catch (error: any) {
    console.error("[/api/interview] Error:", error?.message ?? error);
    // Never leak internal details to the client
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500, headers: corsHeaders }
    );
  }
}
