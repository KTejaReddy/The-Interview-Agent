import { X, GraduationCap, Briefcase, Layers, BookOpen, ShieldCheck, TrendingUp } from "lucide-react";
import { useEffect, useMemo } from "react";
import { createPortal } from "react-dom";
import { CandidateSummary } from "../types";
import { RealisticAvatar } from "./CandidateCharacter";
import { getPalette } from "../utils/palette";

interface CandidateDrawerProps {
  candidate: CandidateSummary | null;
  isOpen: boolean;
  onClose: () => void;
  onStartInterview: (candidateId: string) => void;
  curriculumDays: number;
}

export function CandidateDrawer({ candidate, isOpen, onClose, onStartInterview, curriculumDays }: CandidateDrawerProps) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
      const handleEscape = (e: KeyboardEvent) => {
        if (e.key === "Escape") onClose();
      };
      window.addEventListener("keydown", handleEscape);
      return () => {
        document.body.style.overflow = "";
        window.removeEventListener("keydown", handleEscape);
      };
    }
  }, [isOpen, onClose]);

  const palette = useMemo(
    () => (candidate ? getPalette(candidate.id, candidate.role) : null),
    [candidate]
  );

  if (!isOpen || !candidate || !palette) return null;

  const readiness = candidate.missionsCompleted ? Math.round((candidate.missionsCompleted / curriculumDays) * 100) : 0;

  // Real per-day outcomes drive the journey — never a coarse "count" estimate.
  const completedDays = candidate.completedDays ?? [];
  const skippedDays   = candidate.skippedDays   ?? [];
  const failedDays    = candidate.failedDays    ?? [];

  const signals: string[] = [];
  if (readiness >= 80) signals.push("Interview Ready");
  else if (readiness >= 50) signals.push("Growing Fast");
  else signals.push("Needs Practice");
  if (candidate.missionsFirstTry && candidate.missionsFirstTry > 5) signals.push("Confident Builder");
  if (candidate.struggles && candidate.struggles > 5) signals.push("Shows Perseverance");
  if (candidate.failed && candidate.failed > 0) signals.push("Resilient");

  const topics = candidate.completedTopics && candidate.completedTopics.length > 0 ? candidate.completedTopics : [];

  const journeyMilestones = [1, 7, 12, 16, 22, 27, 31].map((day) => {
    const done    = completedDays.includes(day);
    const skipped = skippedDays.includes(day);
    const failed  = failedDays.includes(day);
    return { day, done, skipped, failed };
  });

  const drawerContent = (
    <div className="fixed inset-0 z-[1000] flex justify-end" aria-modal="true" role="dialog" aria-labelledby="dossier-title">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-[#04060b]/80 backdrop-blur-md transition-opacity duration-300 animate-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer Surface */}
      <div
        className="relative w-[92vw] sm:w-[480px] md:w-[540px] h-full bg-[var(--ink-850)] border-l border-white/10 shadow-[-20px_0_60px_rgba(0,0,0,0.4)] flex flex-col overflow-y-auto animate-slide-in-right"
      >
        {/* Ambient accent wash behind the whole drawer */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ background: `radial-gradient(ellipse 80% 40% at 100% 0%, ${palette.p}12 0%, transparent 60%)` }}
        />

        {/* Header Section */}
        <div className="relative p-8 pb-6 border-b border-white/5 shrink-0" style={{ background: `linear-gradient(180deg, ${palette.p}0d 0%, transparent 100%)` }}>
          <button
            onClick={onClose}
            aria-label="Close dossier"
            className="absolute top-6 right-6 p-2 rounded-full bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors z-10"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="flex flex-col items-start pt-4">
            {/* Portrait with candidate accent ring */}
            <div
              className="relative w-28 h-28 mb-6 rounded-2xl overflow-hidden"
              style={{
                border: `1px solid ${palette.p}40`,
                boxShadow: `0 0 30px ${palette.p}30, 0 8px 24px -8px rgba(0,0,0,0.6)`,
                background: "var(--ink-800)",
              }}
            >
              <RealisticAvatar name={candidate.name} id={candidate.id} />
            </div>

            <h2 id="dossier-title" className="font-sans text-3xl font-black text-white tracking-tight mb-1">
              {candidate.name || candidate.id}
            </h2>
            <p className="text-[#a8b2c5] font-bold text-xs tracking-widest uppercase mb-2" style={{ color: palette.p }}>
              {candidate.role || "Candidate"}
            </p>

            <div className="flex flex-col gap-1.5 text-[12px] text-slate-400 mb-4">
              {candidate.experience !== undefined && (
                <span className="flex items-center gap-1.5">
                  <Briefcase className="w-3.5 h-3.5" />
                  {candidate.experience > 0 ? `${candidate.experience} years experience` : "Entry level"}
                </span>
              )}
              {candidate.education && (
                <span className="flex items-center gap-1.5">
                  <GraduationCap className="w-3.5 h-3.5" />
                  {candidate.education}
                </span>
              )}
            </div>

            <div className="flex flex-wrap gap-2">
              {signals.map((signal, idx) => (
                <span
                  key={idx}
                  className="px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest rounded-md"
                  style={{ background: `${palette.p}12`, border: `1px solid ${palette.p}30`, color: palette.p }}
                >
                  {signal}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Content Body */}
        <div className="relative flex-1 p-8 space-y-10">
          {/* Summary Section */}
          <section>
            <SectionHeader icon={<Layers className="w-3.5 h-3.5" />} title="Profile Summary" />
            <div className="grid grid-cols-3 gap-3">
              <StatCell label="Missions" value={String(candidate.missionsCompleted || 0)} color="#fff" />
              <StatCell label="Days" value={`${completedDays.length || candidate.missionsCompleted || 0}`} suffix={`/${curriculumDays}`} color="#fff" />
              <StatCell label="Readiness" value={`${readiness}%`} color={palette.p} accent />
            </div>
          </section>

          {/* Journey Section — real per-day outcomes */}
          <section>
            <SectionHeader icon={<TrendingUp className="w-3.5 h-3.5" />} title="Cohort Journey" />
            <div className="relative pt-1">
              <div className="journey-track">
                {journeyMilestones.map(({ day, done, skipped, failed }) => {
                  const state = done ? "passed" : skipped ? "skipped" : failed ? "failed" : "upcoming";
                  return (
                    <div
                      key={day}
                      className="journey-node"
                      title={`Day ${day}${done ? " ✓ passed" : skipped ? " (skipped)" : failed ? " ✗ failed" : " — upcoming"}`}
                      style={{ "--node-color": palette.p, "--node-glow": palette.ring } as React.CSSProperties}
                    >
                      <span
                        className={`node-dot ${state === "passed" ? "passed" : ""}`}
                        style={
                          state === "skipped"
                            ? { borderColor: "rgba(245,158,11,0.7)" }
                            : state === "failed"
                              ? { borderColor: "rgba(251,113,133,0.7)" }
                              : undefined
                        }
                      />
                      <span className={`node-label ${done ? "lit" : ""}`}>D{String(day).padStart(2, "0")}</span>
                    </div>
                  );
                })}
              </div>
              {/* Legend */}
              <div className="flex flex-wrap items-center gap-4 mt-4 text-[10px] text-slate-500">
                {completedDays.length > 0 && (
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full" style={{ background: palette.p, boxShadow: `0 0 6px ${palette.p}` }} />
                    {completedDays.length} passed
                  </span>
                )}
                {failedDays.length > 0 && (
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full border-2" style={{ borderColor: "#fb7185" }} />
                    {failedDays.length} struggled
                  </span>
                )}
                {skippedDays.length > 0 && (
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full border-2" style={{ borderColor: "#f59e0b" }} />
                    {skippedDays.length} skipped
                  </span>
                )}
              </div>
            </div>
          </section>

          {/* Topics Section */}
          <section>
            <SectionHeader icon={<BookOpen className="w-3.5 h-3.5" />} title="Interviewable Topics" />
            {topics.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {topics.map(t => (
                  <span
                    key={t}
                    className="topic-chip text-xs font-semibold"
                    style={{ background: `${palette.p}12`, borderColor: `${palette.p}28`, color: palette.p }}
                  >
                    {t}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-sm">No topics completed yet.</p>
            )}
          </section>

          {/* Integrity note */}
          <section>
            <div className="flex items-start gap-2.5 rounded-xl p-4" style={{ background: "rgba(34,197,94,0.06)", border: "1px solid rgba(34,197,94,0.16)" }}>
              <ShieldCheck className="w-4 h-4 mt-0.5 text-emerald-400 shrink-0" />
              <p className="text-[12px] text-slate-400 leading-relaxed">
                Interview integrity protection stays active during the assessment —
                leaving the window, pasting, or copying is recorded.
              </p>
            </div>
          </section>
        </div>

        {/* Sticky Footer CTA */}
        <div className="sticky bottom-0 p-6 bg-[var(--ink-850)]/95 backdrop-blur-md border-t border-white/5 shrink-0">
          <div className="mb-4">
            <h3 className="text-white text-sm font-bold mb-1">Interview Assessment</h3>
            <p className="text-slate-500 text-xs">Ready to evaluate this candidate's technical skills?</p>
          </div>
          <button
            onClick={() => onStartInterview(candidate.id)}
            className="btn w-full !py-4 text-[14px]"
            style={{
              color: "#fff",
              background: `linear-gradient(135deg, ${palette.bar})`,
              boxShadow: `0 8px 24px -8px ${palette.glow}, inset 0 1px 0 rgba(255,255,255,0.15)`,
              border: "1px solid rgba(255,255,255,0.14)",
            }}
          >
            Start Interview
            <span className="text-display-italic group-hover:translate-x-1 transition-transform">→</span>
          </button>
        </div>
      </div>
    </div>
  );

  return createPortal(drawerContent, document.body);
}

function SectionHeader({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <h3 className="flex items-center gap-2 text-[#8ca0bd] text-[10px] font-bold uppercase tracking-widest mb-4">
      {icon}
      {title}
    </h3>
  );
}

function StatCell({ label, value, suffix, color, accent }: { label: string; value: string; suffix?: string; color: string; accent?: boolean }) {
  return (
    <div
      className="p-4 rounded-xl border flex flex-col justify-center items-center relative overflow-hidden"
      style={{ background: "rgba(255,255,255,0.025)", borderColor: accent ? `${color}30` : "rgba(255,255,255,0.06)" }}
    >
      {accent && <div className="absolute inset-0" style={{ background: `${color}08` }} />}
      <span className="text-[#71809a] text-[9px] uppercase tracking-widest font-bold mb-1 relative z-10">{label}</span>
      <span className="stat-number text-[#f8fafc] text-xl font-black relative z-10" style={{ color }}>
        {value}
        {suffix && <span className="text-slate-500 text-sm font-medium">{suffix}</span>}
      </span>
    </div>
  );
}
