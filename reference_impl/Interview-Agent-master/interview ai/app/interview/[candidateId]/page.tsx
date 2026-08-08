"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import {
  AlertTriangle,
  CircleStop,
  Loader2,
  Mic,
  RefreshCw,
  Send,
  Square,
} from "lucide-react";
import { useInterviewStore } from "@/lib/store";
import { getCandidateById } from "@/lib/candidates";
import { FeedbackReport, InterviewMessage } from "@/types";
import ChatBubble from "@/components/ChatBubble";
import TypingIndicator from "@/components/TypingIndicator";
import InterviewHeader from "@/components/InterviewHeader";
import TopicTracker from "@/components/TopicTracker";

const MAX_QUESTIONS = 14;
const MIN_QUESTIONS = 8;
const MAX_INPUT_CHARS = 2000;
const END_INTERVIEW_MESSAGE =
  "I'd like to wrap up the interview now — I think we've covered enough topics.";
const COMPLETION_MARKER = "[INTERVIEW_COMPLETE]";

function extractDay(reply: string): number | null {
  const match = reply.match(/Day (\d+)/i);
  return match ? parseInt(match[1], 10) : null;
}

interface StreamEvent {
  type: "token" | "done" | "error";
  text?: string;
  reply?: string;
  done?: boolean;
  message?: string;
  feedback?: any;
}

/**
 * Read an SSE response, dispatching token/error events to the handlers,
 * and resolve with the final `done` payload (or null if the stream closed
 * without one).
 */
async function consumeSSE(
  res: Response,
  handlers: {
    onToken: (text: string) => void;
    onError: (message: string) => void;
  }
): Promise<StreamEvent | null> {
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";
    for (const block of blocks) {
      const line = block.trim();
      if (!line.startsWith("data:")) continue;
      const json = line.slice(5).trim();
      if (!json) continue;
      let evt: StreamEvent;
      try {
        evt = JSON.parse(json);
      } catch {
        continue;
      }
      if (evt.type === "token") handlers.onToken(evt.text ?? "");
      else if (evt.type === "done") return evt;
      else if (evt.type === "error") handlers.onError(evt.message ?? "Something went wrong.");
    }
  }
  return null;
}

export default function InterviewPage() {
  const params = useParams<{ candidateId: string }>();
  const candidateId = params.candidateId;
  const router = useRouter();

  const candidate = useInterviewStore((s) => s.selectedCandidate);
  const sessionId = useInterviewStore((s) => s.sessionId);
  const sessionStartedAt = useInterviewStore((s) => s.sessionStartedAt);
  const messages = useInterviewStore((s) => s.messages);
  const isLoading = useInterviewStore((s) => s.isLoading);
  const questionsAsked = useInterviewStore((s) => s.questionsAsked);
  const daysCovered = useInterviewStore((s) => s.daysCovered);
  const isComplete = useInterviewStore((s) => s.isComplete);
  const retrySignal = useInterviewStore((s) => s.retrySignal);

  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sessionDead, setSessionDead] = useState(false);
  const [timer, setTimer] = useState("00:00");
  const [streaming, setStreaming] = useState<{ text: string; phase: "start" | "turn" } | null>(null);
  const [listening, setListening] = useState(false);

  // The persisted store hydrates from localStorage on the client, so the first
  // client render can differ from the server HTML. Gate store-rendered content
  // on a hydration flag to avoid SSR hydration mismatches.
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => setHydrated(true), []);

  const scrollRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const recognitionRef = useRef<any>(null);
  const finalTranscriptRef = useRef("");
  const speechSupportedRef = useRef(
    typeof window !== "undefined" &&
      !!(
        (window as any).SpeechRecognition ||
        (window as any).webkitSpeechRecognition
      )
  );

  // ── 1. Resolve candidate: store → data file → redirect ─────────────────────
  useEffect(() => {
    const stored = useInterviewStore.getState().selectedCandidate;
    if (stored?.member.id === candidateId) return;
    const found = getCandidateById(candidateId);
    if (found) {
      useInterviewStore.getState().reset();
      useInterviewStore.getState().setCandidate(found);
    } else {
      router.replace("/");
    }
  }, [candidateId, router]);

  // ── 2. Start the interview once candidate is set and no session exists ──────
  useEffect(() => {
    if (!candidate || sessionId) return;

    let cancelled = false; // guards against StrictMode's dev double-invoke
    const ac = new AbortController();
    abortRef.current = ac;

    (async () => {
      setError(null);
      useInterviewStore.getState().setLoading(true);
      setStreaming({ text: "", phase: "start" });

      const sid = crypto.randomUUID();

      try {
        const res = await fetch("/api/interview", {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
          body: JSON.stringify({ sessionId: sid, candidate }),
          signal: ac.signal,
        });
        if (cancelled) return;
        if (!res.ok || !res.body) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data?.error || `Request failed (${res.status})`);
        }

        // Buffer the streamed opening; commit the session only on a clean finish
        const result = await consumeSSE(res, {
          onToken: (t) =>
            setStreaming((s) => (s ? { ...s, text: s.text + t } : s)),
          onError: (m) => {
            throw new Error(m);
          },
        });

        if (cancelled) return;
        if (!result?.reply) throw new Error("The interview stream ended unexpectedly.");

        // Only commit the session once the start succeeded — a failed start
        // leaves sessionId null so the Retry button can re-trigger this effect.
        useInterviewStore.getState().setSessionId(sid);
        useInterviewStore.getState().setSessionStartedAt(Date.now());

        const message: InterviewMessage = {
          role: "interviewer",
          content: result.reply,
          timestamp: new Date().toISOString(),
          questionType: "opening",
        };
        useInterviewStore.getState().addMessage(message);
        useInterviewStore.getState().incrementQuestions();

        const day = extractDay(result.reply);
        if (day) useInterviewStore.getState().addDay(day);
      } catch (e: any) {
        if (cancelled || e?.name === "AbortError") return;
        setError(e?.message || "Could not reach the interview engine.");
      } finally {
        if (!cancelled) {
          useInterviewStore.getState().setLoading(false);
          setStreaming(null);
        }
      }
    })();
    return () => {
      cancelled = true;
      ac.abort();
    };
  }, [candidate, sessionId, retrySignal]);

  // ── 3. Live timer ───────────────────────────────────────────────────────────
  useEffect(() => {
    if (!sessionStartedAt) return;
    const tick = () => {
      const secs = Math.max(0, Math.floor((Date.now() - sessionStartedAt) / 1000));
      const mm = String(Math.floor(secs / 60)).padStart(2, "0");
      const ss = String(secs % 60).padStart(2, "0");
      setTimer(`${mm}:${ss}`);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [sessionStartedAt]);

  // ── 4. Auto-scroll to latest message ────────────────────────────────────────
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages.length, isLoading, streaming?.text.length]);

  // ── 5. Stop any active speech recognition on unmount ────────────────────────
  useEffect(() => {
    return () => {
      recognitionRef.current?.stop?.();
      abortRef.current?.abort();
    };
  }, []);

  // ── Submit a candidate answer (streamed) ────────────────────────────────────
  const submit = async (raw: string) => {
    const text = raw.trim();
    if (!text || isLoading || !sessionId || isComplete) return;

    setInput("");
    setError(null);

    useInterviewStore.getState().addMessage({
      role: "candidate",
      content: text,
      timestamp: new Date().toISOString(),
    });
    useInterviewStore.getState().setLoading(true);
    setStreaming({ text: "", phase: "turn" });

    const ac = new AbortController();
    abortRef.current = ac;

    try {
      const res = await fetch("/api/interview", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
        body: JSON.stringify({ sessionId, message: text }),
        signal: ac.signal,
      });
      if (!res.ok || !res.body) {
        const data = await res.json().catch(() => ({}));
        // A 404 means the server-side session expired or was evicted — offer a restart
        if (res.status === 404) setSessionDead(true);
        throw new Error(data?.error || `Request failed (${res.status})`);
      }

      const result = await consumeSSE(res, {
        onToken: (t) =>
          setStreaming((s) => (s ? { ...s, text: s.text + t } : s)),
        onError: (m) => {
          throw new Error(m);
        },
      });
      if (!result?.reply) throw new Error("The interview stream ended unexpectedly.");

      useInterviewStore.getState().addMessage({
        role: "interviewer",
        content: result.reply,
        timestamp: new Date().toISOString(),
        questionType: result.done ? "closing" : "technical",
      });
      useInterviewStore.getState().incrementQuestions();

      const day = extractDay(result.reply);
      if (day) useInterviewStore.getState().addDay(day);

      if (result.done) {
        // Navigate regardless — if feedback generation failed server-side, the
        // report page shows its graceful empty state instead of stranding the user.
        if (result.feedback) {
          const feedback: FeedbackReport = {
            summary: result.feedback.summary ?? "",
            strengths: result.feedback.strengths ?? [],
            gaps: result.feedback.gaps ?? [],
            next: result.feedback.next ?? [],
            overallScore: result.feedback.overallScore,
            recommendation: result.feedback.recommendation,
            topicScores: result.feedback.topicScores,
          };
          useInterviewStore.getState().setComplete(feedback);
        }
        router.push(`/feedback/${sessionId}`);
      }
    } catch (e: any) {
      if (e?.name === "AbortError") return;
      setError(e?.message || "Something went wrong — please try again.");
    } finally {
      useInterviewStore.getState().setLoading(false);
      setStreaming(null);
    }
  };

  // ── Voice input (Web Speech API) ────────────────────────────────────────────
  const toggleVoice = () => {
    const SR =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;
    if (!SR) return;

    if (listening) {
      recognitionRef.current?.stop?.();
      setListening(false);
      return;
    }

    const rec = new SR();
    rec.lang = "en-US";
    rec.interimResults = true;
    rec.continuous = false;
    recognitionRef.current = rec;

    finalTranscriptRef.current = input.trim() ? input.trim() + " " : "";
    setListening(true);

    rec.onresult = (e: any) => {
      let interim = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const res = e.results[i];
        if (res.isFinal) {
          finalTranscriptRef.current += (finalTranscriptRef.current && !finalTranscriptRef.current.endsWith(" ") ? " " : "") + res[0].transcript.trim();
        } else {
          interim += res[0].transcript;
        }
      }
      const combined = finalTranscriptRef.current + (interim ? " " + interim : "");
      setInput(combined.slice(0, MAX_INPUT_CHARS));
    };
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);
    rec.start();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit(input);
    }
  };

  const canEndEarly = questionsAsked >= MIN_QUESTIONS && !isComplete && !isLoading;
  const streamedText = streaming?.text.replaceAll(COMPLETION_MARKER, "") ?? "";

  return (
    <div className="flex h-screen overflow-hidden bg-bg-primary">
      {/* ── Left sidebar (25%, fixed) ─────────────────────────────────────── */}
      <aside className="hidden w-[25%] max-w-xs shrink-0 border-r border-white/5 bg-bg-secondary lg:block">
        {hydrated && candidate && (
          <TopicTracker
            candidate={candidate}
            daysCovered={daysCovered}
            questionsAsked={questionsAsked}
            minQuestions={MIN_QUESTIONS}
          />
        )}
      </aside>

      {/* ── Right main panel ──────────────────────────────────────────────── */}
      <div className="flex min-w-0 flex-1 flex-col">
        <InterviewHeader
          questionsAsked={questionsAsked}
          maxQuestions={MAX_QUESTIONS}
          timerLabel={timer}
        />

        {/* Error banner */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="overflow-hidden"
            >
              <div className="mx-4 mt-4 flex items-center gap-3 rounded-xl border border-brand-rose/30 bg-brand-rose/10 px-4 py-3 text-sm text-brand-rose">
                <AlertTriangle size={16} className="shrink-0" />
                <span className="flex-1">{error}</span>
                {sessionDead ? (
                  <button
                    onClick={() => {
                      setSessionDead(false);
                      useInterviewStore.getState().reset();
                      router.replace(`/interview/${candidateId}`);
                    }}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-brand-rose/40 px-3 py-1.5 text-xs font-semibold transition-colors hover:bg-brand-rose/20"
                  >
                    <RefreshCw size={12} /> Restart Interview
                  </button>
                ) : (
                  !sessionStartedAt && (
                    <button
                      onClick={() => useInterviewStore.getState().retryStart()}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-brand-rose/40 px-3 py-1.5 text-xs font-semibold transition-colors hover:bg-brand-rose/20"
                    >
                      <RefreshCw size={12} /> Retry
                    </button>
                  )
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Chat area */}
        <div
          ref={scrollRef}
          className="flex-1 space-y-4 overflow-y-auto px-4 py-6 sm:px-8"
        >
          {hydrated && messages.length === 0 && !isLoading && !streaming && (
            <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
              <div className="relative">
                <div className="absolute -inset-4 rounded-full bg-brand-violet/20 blur-2xl" />
                <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-violet to-brand-cyan text-3xl shadow-glow">
                  🤖
                </div>
              </div>
              <div>
                <p className="text-sm font-semibold text-ink-primary">
                  Alex is preparing your interview
                </p>
                <p className="mx-auto mt-1 max-w-xs text-xs leading-relaxed text-ink-muted">
                  Questions will be drawn from the missions this candidate actually
                  completed during the cohort.
                </p>
              </div>
            </div>
          )}

          {hydrated &&
            messages.map((m, i) => (
              <ChatBubble key={`${m.timestamp}-${i}`} message={m} />
            ))}

          {/* Live-streaming interviewer reply */}
          {streaming && (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="flex items-start gap-3"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-violet to-brand-cyan text-sm shadow-glow">
                🤖
              </div>
              <div className="bubble-interviewer !max-w-[75%]">
                <p className="whitespace-pre-wrap text-[15px] leading-relaxed text-ink-primary">
                  {streamedText}
                  <span className="ml-0.5 inline-block h-4 w-[2px] animate-pulse rounded-full bg-brand-cyan-light align-middle" />
                </p>
              </div>
            </motion.div>
          )}

          {isLoading && !streaming && <TypingIndicator />}
        </div>

        {/* Input area */}
        <div className="border-t border-white/5 bg-bg-secondary/80 px-4 py-4 backdrop-blur sm:px-8">
          <div className="mx-auto max-w-3xl">
            <div className="glass-card overflow-hidden !rounded-2xl">
              <textarea
                rows={3}
                value={input}
                onChange={(e) => setInput(e.target.value.slice(0, MAX_INPUT_CHARS))}
                onKeyDown={handleKeyDown}
                placeholder={
                  listening
                    ? "Listening… speak your answer"
                    : "Type your answer here, or tap the mic…"
                }
                disabled={isLoading || isComplete || listening}
                className="w-full resize-none bg-transparent px-4 py-3 text-[15px] leading-relaxed text-ink-primary placeholder:text-ink-muted focus:outline-none disabled:opacity-50"
              />
              <div className="flex items-center justify-between gap-3 border-t border-white/5 px-4 py-2.5">
                <span className="font-mono text-[11px] text-ink-muted tabular-nums">
                  {input.length}/{MAX_INPUT_CHARS}
                  <span className="mx-2 text-white/10">|</span>
                  Enter to send · Shift+Enter for newline
                </span>
                <div className="flex items-center gap-2">
                  {hydrated && speechSupportedRef.current && (
                    <button
                      onClick={toggleVoice}
                      disabled={isLoading || isComplete}
                      aria-label={listening ? "Stop recording" : "Answer by voice"}
                      className={
                        "inline-flex h-9 w-9 items-center justify-center rounded-xl border transition-all disabled:opacity-40 " +
                        (listening
                          ? "border-brand-rose/50 bg-brand-rose/15 text-brand-rose animate-pulse"
                          : "border-white/10 bg-white/[0.03] text-ink-secondary hover:border-brand-violet/40 hover:text-brand-violet-light")
                      }
                    >
                      {listening ? <Square size={14} /> : <Mic size={14} />}
                    </button>
                  )}
                  {canEndEarly && (
                    <button
                      onClick={() => submit(END_INTERVIEW_MESSAGE)}
                      disabled={isLoading}
                      className="inline-flex items-center gap-1.5 rounded-xl border border-brand-amber/30 bg-brand-amber/10 px-3.5 py-2 text-xs font-semibold text-brand-amber transition-all hover:bg-brand-amber/20 disabled:opacity-50"
                    >
                      <CircleStop size={13} /> End Interview
                    </button>
                  )}
                  <button
                    onClick={() => submit(input)}
                    disabled={!input.trim() || isLoading || isComplete}
                    className="btn-primary inline-flex !rounded-xl !px-4 !py-2 disabled:cursor-not-allowed disabled:opacity-40"
                    aria-label="Send message"
                  >
                    {isLoading ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <Send size={16} />
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
