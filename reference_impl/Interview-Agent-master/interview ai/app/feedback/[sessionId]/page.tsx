"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { FileQuestion } from "lucide-react";
import { useInterviewStore } from "@/lib/store";
import FeedbackReport from "@/components/FeedbackReport";

export default function FeedbackPage() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;

  const feedback = useInterviewStore((s) => s.feedback);
  const candidate = useInterviewStore((s) => s.selectedCandidate);
  const questionsAsked = useInterviewStore((s) => s.questionsAsked);
  const daysCovered = useInterviewStore((s) => s.daysCovered);
  const sessionStartedAt = useInterviewStore((s) => s.sessionStartedAt);

  // The persisted store hydrates from localStorage on the client; only render
  // the report once hydration has happened so the first client render matches
  // the server HTML (which always shows the empty state).
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => setHydrated(true), []);

  // Store was reset (e.g. page refresh) — show a graceful empty state
  if (!hydrated || !feedback) {
    return (
      <main className="animated-bg flex min-h-screen flex-col items-center justify-center gap-6 px-6 text-center">
        <div className="relative">
          <div className="absolute -inset-4 rounded-full bg-brand-violet/15 blur-2xl" />
          <div className="relative flex h-20 w-20 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03]">
            <FileQuestion size={32} className="text-ink-muted" />
          </div>
        </div>
        <div>
          <h1 className="font-display text-2xl font-bold text-ink-primary sm:text-3xl">
            No feedback report here yet
          </h1>
          <p className="mx-auto mt-3 max-w-md text-sm leading-relaxed text-ink-secondary">
            Reports are tied to a live interview session. Finish an interview with
            Alex to generate a score-backed report, or pick another candidate to
            start fresh.
          </p>
        </div>
        <Link href="/" className="btn-primary">
          Start a New Interview
        </Link>
      </main>
    );
  }

  return (
    <main className="animated-bg min-h-screen">
      <FeedbackReport
        feedback={feedback}
        candidate={candidate}
        questionsAsked={questionsAsked}
        daysCovered={daysCovered}
        startedAt={sessionStartedAt}
      />
    </main>
  );
}
