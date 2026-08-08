"use client";

import { Check, Flame, Target, Zap } from "lucide-react";
import { Candidate } from "@/types";
import clsx from "clsx";

interface TopicTrackerProps {
  candidate: Candidate;
  daysCovered: number[];
  questionsAsked: number;
  minQuestions: number;
}

export default function TopicTracker({
  candidate,
  daysCovered,
  questionsAsked,
  minQuestions,
}: TopicTrackerProps) {
  const { member, missions, signals } = candidate;
  const passed = missions.filter((m) => m.passed === true);
  const firstTryRate = Math.round(
    (signals.missionsFirstTry / Math.max(signals.missionsCompleted, 1)) * 100
  );

  // Circular progress ring (questions / minQuestions)
  const radius = 26;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.min(1, questionsAsked / Math.max(minQuestions, 1));
  const ringColor = pct >= 1 ? "#10B981" : "#7C3AED";

  return (
    <div className="flex h-full flex-col gap-5 overflow-y-auto p-5">
      {/* Candidate identity */}
      <div className="glass-card flex flex-col items-center gap-3 p-5 text-center">
        <img
          src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(member.name)}`}
          alt={`${member.name} avatar`}
          width={80}
          height={80}
          className="rounded-2xl bg-bg-elevated ring-1 ring-white/10"
        />
        <div>
          <h2 className="text-lg font-bold text-ink-primary">{member.name}</h2>
          <p className="text-xs text-brand-violet-light">{member.jobRole}</p>
          <p className="mt-0.5 text-[11px] text-ink-secondary">
            {member.yearsExperience} yrs · {member.education}
          </p>
        </div>

        {/* Mini stats */}
        <div className="grid w-full grid-cols-2 gap-2">
          <div className="rounded-lg border border-white/5 bg-white/[0.02] p-2">
            <p className="flex items-center justify-center gap-1 font-mono text-sm font-bold text-brand-amber">
              <Flame size={12} /> {signals.commitDays}
            </p>
            <p className="text-[9px] uppercase tracking-wider text-ink-muted">Commit days</p>
          </div>
          <div className="rounded-lg border border-white/5 bg-white/[0.02] p-2">
            <p className="flex items-center justify-center gap-1 font-mono text-sm font-bold text-brand-cyan">
              <Zap size={12} /> {firstTryRate}%
            </p>
            <p className="text-[9px] uppercase tracking-wider text-ink-muted">First-try rate</p>
          </div>
        </div>
      </div>

      {/* Interview progress ring */}
      <div className="glass-card flex items-center gap-4 p-5">
        <div className="relative h-16 w-16 shrink-0">
          <svg width={64} height={64} className="-rotate-90">
            <circle cx={32} cy={32} r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={7} />
            <circle
              cx={32}
              cy={32}
              r={radius}
              fill="none"
              stroke={ringColor}
              strokeWidth={7}
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={circumference * (1 - pct)}
              style={{ transition: "stroke-dashoffset 0.6s ease", filter: "drop-shadow(0 0 6px rgba(124,58,237,0.5))" }}
            />
          </svg>
          <span className="absolute inset-0 flex items-center justify-center font-mono text-sm font-bold">
            {Math.min(questionsAsked, minQuestions)}/{minQuestions}
          </span>
        </div>
        <div>
          <p className="flex items-center gap-1 text-sm font-semibold text-ink-primary">
            <Target size={14} className="text-brand-violet-light" /> Interview Progress
          </p>
          <p className="mt-0.5 text-[11px] leading-snug text-ink-secondary">
            {pct >= 1
              ? "Minimum met — you may end the interview."
              : `${minQuestions - Math.min(questionsAsked, minQuestions)} questions to minimum`}
          </p>
        </div>
      </div>

      {/* Topics covered */}
      <div className="glass-card flex-1 p-5">
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-ink-secondary">
          Topics Covered
        </h3>
        <ul className="space-y-1.5">
          {passed.map((m) => {
            const covered = daysCovered.includes(m.day);
            return (
              <li
                key={m.day}
                className={clsx(
                  "flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-xs transition-colors",
                  covered
                    ? "border border-brand-emerald/20 bg-brand-emerald/10 text-ink-primary"
                    : "border border-transparent text-ink-muted"
                )}
              >
                <span
                  className={clsx(
                    "flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded-full",
                    covered ? "bg-brand-emerald text-white" : "bg-white/5 text-ink-muted"
                  )}
                >
                  {covered ? <Check size={11} /> : (
                    <span className="font-mono text-[9px]">D{m.day}</span>
                  )}
                </span>
                <span className={clsx("truncate", covered ? "font-medium" : "")}>
                  {m.title}
                </span>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
