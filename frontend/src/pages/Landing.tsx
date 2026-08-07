import { useState } from "react";
import { useInterview } from "../context/InterviewContext";
import type { Page } from "../types";
import { Brand } from "../components/Brand";
import { ErrorBanner } from "../components/ErrorBanner";

interface LandingProps {
  onNavigate: (page: Page) => void;
}

const FEATURES = [
  {
    title: "Real conversations",
    text: "Every answer shapes the next question — deeper, simpler, or a recovery prompt — just like a real interviewer.",
    icon: "💬",
  },
  {
    title: "Curriculum-grounded",
    text: "Questions come only from your curriculum.json: objectives, tools, learning goals and topics — never hallucinated.",
    icon: "📚",
  },
  {
    title: "Adaptive difficulty",
    text: "The interviewer calibrates easy → medium → advanced from the candidate's profile inside candidate.json.",
    icon: "🎯",
  },
  {
    title: "Structured feedback",
    text: "When it's done you get summary, strengths, gaps and next steps — exactly the fields in technical-spec.md.",
    icon: "📋",
  },
];

export function Landing({ onNavigate }: LandingProps) {
  const { candidates, candidatesLoading, health, error, dismissError, startInterview, loading } =
    useInterview();
  const [selected, setSelected] = useState<string | null>(null);
  const [opening, setOpening] = useState("Hi! I'm ready to start.");

  const canStart = Boolean(selected) && !loading && !candidatesLoading;

  const handleStart = async () => {
    if (!selected) return;
    await startInterview(selected, opening);
    onNavigate("interview");
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Background decoration */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-32 left-1/2 h-[480px] w-[720px] -translate-x-1/2 rounded-full bg-accent-600/20 blur-[120px]" />
        <div className="absolute bottom-0 right-0 h-[360px] w-[420px] rounded-full bg-mint-500/10 blur-[120px]" />
      </div>

      <div className="relative mx-auto flex max-w-5xl flex-col items-center px-6 pb-20 pt-10">
        {/* Header */}
        <header className="flex w-full items-center justify-between">
          <Brand />
          <div className="flex items-center gap-3">
            {health && (
              <div
                className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-[11px] font-semibold ${
                  health.status === "ok"
                    ? "border-mint-500/30 bg-mint-500/10 text-mint-400"
                    : "border-amber-400/30 bg-amber-400/10 text-amber-400"
                }`}
              >
                <span className="h-1.5 w-1.5 rounded-full bg-current" />
                {health.status === "ok" ? "Backend online" : "Backend degraded"}
              </div>
            )}
          </div>
        </header>

        {/* Hero */}
        <section className="mt-16 text-center">
          <div className="mx-auto mb-5 inline-flex items-center gap-2 rounded-full border border-accent-500/30 bg-accent-500/10 px-4 py-1.5 text-xs font-medium text-accent-400 animate-fade-up">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent-400" />
            A live technical interviewer, powered by your data
          </div>
          <h1 className="mx-auto max-w-3xl bg-gradient-to-r from-white via-indigo-100 to-mint-200 bg-clip-text text-5xl font-extrabold leading-tight tracking-tight text-transparent md:text-6xl animate-fade-up">
            Face a real interview — <br className="hidden md:block" />
            before the real one.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-400 animate-fade-up">
            Pick a candidate profile and step into a conversation with a calm
            Senior Staff Engineer who adapts to everything you say — across at
            least 8 questions and 4 curriculum days — then hands you structured
            feedback.
          </p>
        </section>

        {/* Feature grid */}
        <section className="mt-14 grid w-full grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((feature, index) => (
            <div
              key={feature.title}
              className="rounded-2xl border border-base-700 bg-base-800/60 p-5 backdrop-blur transition-all duration-300 hover:-translate-y-1 hover:border-accent-500/40 hover:shadow-lg hover:shadow-accent-500/10 animate-fade-up"
              style={{ animationDelay: `${index * 70}ms` }}
            >
              <div className="mb-3 text-2xl">{feature.icon}</div>
              <h3 className="mb-1.5 font-semibold text-white">{feature.title}</h3>
              <p className="text-sm leading-relaxed text-slate-400">{feature.text}</p>
            </div>
          ))}
        </section>

        {/* Start panel */}
        <section className="mt-14 w-full max-w-2xl animate-fade-up" style={{ animationDelay: "200ms" }}>
          {error && (
            <div className="mb-4">
              <ErrorBanner message={error} onDismiss={dismissError} />
            </div>
          )}

          <div className="rounded-3xl border border-base-700 bg-base-800/70 p-7 shadow-2xl shadow-black/40 backdrop-blur">
            <h2 className="text-xl font-bold text-white">Start an interview</h2>
            <p className="mt-1 text-sm text-slate-400">
              Select which candidate from <span className="font-mono text-accent-400">candidate.json</span> is being interviewed.
            </p>

            {candidatesLoading ? (
              <div className="mt-5 space-y-3">
                {[0, 1].map((i) => (
                  <div key={i} className="h-16 animate-pulse rounded-2xl bg-base-700/60" />
                ))}
              </div>
            ) : candidates.length === 0 ? (
              <div className="mt-5 rounded-2xl border border-amber-400/30 bg-amber-400/10 p-4 text-sm text-amber-200">
                No candidates found. Place <span className="font-mono">candidate.json</span> in{" "}
                <span className="font-mono">backend/data/</span> and restart the backend.
              </div>
            ) : (
              <div className="mt-5 grid grid-cols-1 gap-3">
                {candidates.map((candidate) => {
                  const active = selected === candidate.id;
                  return (
                    <button
                      key={candidate.id}
                      onClick={() => setSelected(candidate.id)}
                      className={`group flex items-center justify-between rounded-2xl border px-5 py-4 text-left transition-all duration-200 ${
                        active
                          ? "border-accent-500/60 bg-accent-500/10 shadow-lg shadow-accent-500/10"
                          : "border-base-700 bg-base-900/60 hover:border-accent-500/40 hover:bg-base-800"
                      }`}
                    >
                      <div>
                        <p className="font-semibold text-white">
                          {candidate.name || candidate.id}
                        </p>
                        <p className="text-sm text-slate-400">
                          {candidate.role || "No role provided"} ·{" "}
                          <span className="font-mono text-xs">{candidate.id}</span>
                        </p>
                      </div>
                      <span
                        className={`flex h-5 w-5 items-center justify-center rounded-full border-2 transition ${
                          active
                            ? "border-accent-400 bg-accent-500"
                            : "border-slate-600 group-hover:border-accent-500/50"
                        }`}
                      >
                        {active && <span className="h-2 w-2 rounded-full bg-white" />}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}

            <div className="mt-5">
              <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-slate-500">
                Your opening message
              </label>
              <input
                value={opening}
                onChange={(event) => setOpening(event.target.value)}
                className="w-full rounded-xl border border-base-700 bg-base-900/70 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-accent-500/60 focus:ring-2 focus:ring-accent-500/20"
                placeholder="Hi! I'm ready to start."
              />
            </div>

            <button
              onClick={handleStart}
              disabled={!canStart}
              className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-accent-600 to-indigo-500 px-6 py-3.5 font-semibold text-white shadow-lg shadow-accent-600/30 transition-all duration-200 hover:shadow-xl hover:shadow-accent-600/40 hover:brightness-110 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:brightness-100"
            >
              {loading ? (
                <>
                  <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2.5" opacity="0.25" />
                    <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
                  </svg>
                  Starting interview…
                </>
              ) : (
                <>
                  Start the interview
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </>
              )}
            </button>
          </div>
        </section>

        <footer className="mt-16 text-center text-xs text-slate-600">
          Driven by curriculum.json · candidate.json · technical-spec.md — read-only, never modified.
        </footer>
      </div>
    </div>
  );
}
