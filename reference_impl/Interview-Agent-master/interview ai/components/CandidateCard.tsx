"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, Award, CheckCircle2, Flame } from "lucide-react";
import { Candidate } from "@/types";
import { computeEngagementScore } from "@/lib/candidates";
import ProgressBar from "./ProgressBar";

interface CandidateCardProps {
  candidate: Candidate;
  index: number;
}

export default function CandidateCard({ candidate, index }: CandidateCardProps) {
  const { member, missions, signals } = candidate;

  const passed = missions.filter((m) => m.passed === true);
  const skipped = missions.filter((m) => m.skipped === true);
  const failed = missions.filter((m) => m.passed === false);
  const engagement = computeEngagementScore(candidate);
  const firstTryRate = Math.round(
    (signals.missionsFirstTry / Math.max(signals.missionsCompleted, 1)) * 100
  );

  const avatarUrl = `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(
    member.name
  )}`;

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.05 }}
      className="glass-card candidate-card group relative flex flex-col overflow-hidden"
    >
      {/* Top gradient hairline */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-brand-violet/60 to-transparent" />

      {/* Avatar + header */}
      <div className="flex items-start gap-4 p-5 pb-4">
        <div className="relative">
          <img
            src={avatarUrl}
            alt={`${member.name} avatar`}
            width={64}
            height={64}
            className="rounded-2xl bg-bg-elevated ring-1 ring-white/10 transition-transform duration-300 group-hover:scale-105"
          />
          <span className="absolute -bottom-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-brand-emerald text-[10px] text-white ring-2 ring-bg-card">
            ✓
          </span>
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-lg font-bold text-ink-primary">{member.name}</h3>
          <p className="truncate text-sm text-brand-violet-light">{member.jobRole}</p>
          <p className="mt-0.5 truncate text-xs text-ink-secondary">
            {member.yearsExperience} yrs · {member.education}
          </p>
        </div>
        <span className="flex shrink-0 items-center gap-1 rounded-full border border-brand-cyan/30 bg-brand-cyan/10 px-2 py-1 font-mono text-[11px] font-semibold text-brand-cyan">
          <Award size={12} /> {engagement}
        </span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 px-5 text-center">
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-2.5">
          <p className="font-mono text-lg font-bold text-ink-primary">
            {passed.length}
            <span className="text-xs font-normal text-ink-muted">/{missions.length}</span>
          </p>
          <p className="text-[10px] uppercase tracking-wider text-ink-muted">Missions Passed</p>
        </div>
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-2.5">
          <p className="flex items-center justify-center gap-1 font-mono text-lg font-bold text-ink-primary">
            <Flame size={14} className="text-brand-amber" />
            {signals.commitDays}
            <span className="text-xs font-normal text-ink-muted">/31</span>
          </p>
          <p className="text-[10px] uppercase tracking-wider text-ink-muted">Commit Days</p>
        </div>
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-2.5">
          <p className="font-mono text-lg font-bold text-brand-cyan">{firstTryRate}%</p>
          <p className="text-[10px] uppercase tracking-wider text-ink-muted">First-Try Rate</p>
        </div>
      </div>

      {/* Commit days bar */}
      <div className="px-5 pt-4">
        <ProgressBar value={signals.commitDays} max={31} showLabel />
      </div>

      {/* Mission day pills */}
      <div className="flex flex-wrap gap-1.5 px-5 py-4">
        {passed.map((m) => (
          <span
            key={`p-${m.day}`}
            title={`Day ${m.day}: ${m.title}`}
            className="rounded-full border border-brand-emerald/25 bg-brand-emerald/10 px-2 py-0.5 font-mono text-[10px] font-medium text-brand-emerald"
          >
            D{m.day}
          </span>
        ))}
        {skipped.map((m) => (
          <span
            key={`s-${m.day}`}
            title={`Day ${m.day}: ${m.title} (skipped)`}
            className="rounded-full border border-white/5 bg-white/[0.02] px-2 py-0.5 font-mono text-[10px] text-ink-muted line-through"
          >
            D{m.day}
          </span>
        ))}
        {failed.map((m) => (
          <span
            key={`f-${m.day}`}
            title={`Day ${m.day}: ${m.title} (not passed)`}
            className="rounded-full border border-brand-rose/25 bg-brand-rose/10 px-2 py-0.5 font-mono text-[10px] text-brand-rose/70 line-through"
          >
            D{m.day}
          </span>
        ))}
      </div>

      {/* Footer */}
      <div className="mt-auto flex items-center justify-between gap-3 border-t border-white/5 bg-white/[0.02] px-5 py-4">
        <span className="flex items-center gap-1.5 text-[11px] text-ink-secondary">
          <CheckCircle2 size={13} className="text-brand-emerald" />
          {missions.length - skipped.length - failed.length} interviewable topics
        </span>
        <Link
          href={`/interview/${member.id}`}
          className="btn-primary !px-4 !py-2 text-sm group/btn inline-flex items-center gap-1.5"
        >
          Start Interview
          <ArrowRight size={15} className="transition-transform group-hover/btn:translate-x-0.5" />
        </Link>
      </div>
    </motion.div>
  );
}
