"use client";

import { Bot, Clock, ListChecks } from "lucide-react";
import ProgressBar from "./ProgressBar";

interface InterviewHeaderProps {
  questionsAsked: number;
  maxQuestions: number;
  timerLabel: string;
}

export default function InterviewHeader({
  questionsAsked,
  maxQuestions,
  timerLabel,
}: InterviewHeaderProps) {
  return (
    <div className="glass-card flex items-center gap-5 rounded-none border-x-0 border-t-0 px-6 py-4">
      {/* Left — interviewer identity */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-brand-violet to-brand-cyan text-lg shadow-glow">
          🤖
        </div>
        <div>
          <p className="text-sm font-bold text-ink-primary">Alex — AI Interviewer</p>
          <p className="flex items-center gap-1 text-[11px] text-ink-secondary">
            <Bot size={11} /> llama-3.3-70b-versatile
          </p>
        </div>
      </div>

      {/* Center — progress bar */}
      <div className="min-w-0 flex-1 px-2">
        <div className="mb-1.5 flex items-center justify-between text-[11px] text-ink-secondary">
          <span className="flex items-center gap-1">
            <ListChecks size={12} className="text-brand-violet-light" />
            Interview progress
          </span>
          <span className="font-mono tabular-nums">
            {questionsAsked} / {maxQuestions} questions
          </span>
        </div>
        <ProgressBar value={questionsAsked} max={maxQuestions} />
      </div>

      {/* Right — timer */}
      <div className="flex items-center gap-2 rounded-xl border border-white/5 bg-white/[0.02] px-3 py-2">
        <Clock size={14} className="text-brand-cyan" />
        <span className="font-mono text-sm font-semibold tabular-nums text-ink-primary">
          {timerLabel}
        </span>
      </div>
    </div>
  );
}
