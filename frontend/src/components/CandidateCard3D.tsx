import { useRef, useState, useMemo, useCallback } from "react";
import type { CandidateSummary } from "../types";
import { RealisticAvatar } from "./CandidateCharacter";
import { ArrowRight, BookOpen, CheckCircle, XCircle, SkipForward } from "lucide-react";

interface CandidateCard3DProps {
  candidate: CandidateSummary;
  curriculumDaysTotal: number;
  onStartInterview: (id: string) => void;
  onViewDossier?: (id: string) => void;
}

// Deterministic palette per-candidate based on role
function getPalette(role: string, id: string) {
  const r = (role || "").toLowerCase();

  if (r.includes("data engineer") || r.includes("data scientist"))
    return { primary: "#f59e0b", secondary: "#8b5cf6", bg: "from-amber-950/60 via-violet-950/40", glow: "rgba(245,158,11,0.25)", bar: "from-amber-400 to-violet-500", border: "rgba(245,158,11,0.2)" };
  if (r.includes("backend") || r.includes("server"))
    return { primary: "#06b6d4", secondary: "#3b82f6", bg: "from-cyan-950/60 via-blue-950/40", glow: "rgba(6,182,212,0.25)", bar: "from-cyan-400 to-blue-500", border: "rgba(6,182,212,0.2)" };
  if (r.includes("ai engineer") || r.includes("machine learning"))
    return { primary: "#a78bfa", secondary: "#06b6d4", bg: "from-violet-950/60 via-cyan-950/40", glow: "rgba(167,139,250,0.25)", bar: "from-violet-400 to-cyan-400", border: "rgba(167,139,250,0.2)" };
  if (r.includes("devops") || r.includes("cloud") || r.includes("infrastructure"))
    return { primary: "#10b981", secondary: "#06b6d4", bg: "from-emerald-950/60 via-teal-950/40", glow: "rgba(16,185,129,0.25)", bar: "from-emerald-400 to-teal-400", border: "rgba(16,185,129,0.2)" };
  if (r.includes("marketing") || r.includes("ux") || r.includes("creative") || r.includes("hr"))
    return { primary: "#f43f5e", secondary: "#f59e0b", bg: "from-rose-950/60 via-amber-950/40", glow: "rgba(244,63,94,0.25)", bar: "from-rose-400 to-amber-400", border: "rgba(244,63,94,0.2)" };
  if (r.includes("business") || r.includes("analyst"))
    return { primary: "#fb923c", secondary: "#eab308", bg: "from-orange-950/60 via-yellow-950/40", glow: "rgba(251,146,60,0.25)", bar: "from-orange-400 to-yellow-400", border: "rgba(251,146,60,0.2)" };
  if (r.includes("architect") || r.includes("principal") || r.includes("distinguished"))
    return { primary: "#818cf8", secondary: "#34d399", bg: "from-indigo-950/60 via-emerald-950/40", glow: "rgba(129,140,248,0.25)", bar: "from-indigo-400 to-emerald-400", border: "rgba(129,140,248,0.2)" };
  if (r.includes("mobile") || r.includes("frontend"))
    return { primary: "#34d399", secondary: "#3b82f6", bg: "from-emerald-950/60 via-blue-950/40", glow: "rgba(52,211,153,0.25)", bar: "from-emerald-400 to-blue-400", border: "rgba(52,211,153,0.2)" };
  if (r.includes("legacy") || r.includes("it support"))
    return { primary: "#94a3b8", secondary: "#64748b", bg: "from-slate-950/60 via-slate-900/40", glow: "rgba(148,163,184,0.2)", bar: "from-slate-400 to-slate-500", border: "rgba(148,163,184,0.15)" };
  if (r.includes("junior") || r.includes("intern"))
    return { primary: "#60a5fa", secondary: "#c084fc", bg: "from-blue-950/60 via-purple-950/40", glow: "rgba(96,165,250,0.25)", bar: "from-blue-400 to-purple-400", border: "rgba(96,165,250,0.2)" };

  // Fallback — derive from id character sum
  const sum = id.split("").reduce((a, c) => a + c.charCodeAt(0), 0);
  const palettes = [
    { primary: "#6366f1", secondary: "#a78bfa", bg: "from-indigo-950/60 via-purple-950/40", glow: "rgba(99,102,241,0.25)", bar: "from-indigo-400 to-purple-400", border: "rgba(99,102,241,0.2)" },
    { primary: "#ec4899", secondary: "#8b5cf6", bg: "from-pink-950/60 via-violet-950/40", glow: "rgba(236,72,153,0.25)", bar: "from-pink-400 to-violet-400", border: "rgba(236,72,153,0.2)" },
  ];
  return palettes[sum % palettes.length];
}


// Compute which days to show in the timeline (show days where something happened, plus boundaries)
function getTimelineDays(completedDays: number[], skippedDays: number[], failedDays: number[]): number[] {
  const eventDays = new Set([...completedDays, ...skippedDays, ...failedDays]);
  // Always include day 1 and 31 as anchors if they exist in events or are near completion
  const milestones = [1, 7, 12, 16, 22, 27, 31];
  const toShow = new Set<number>();
  milestones.forEach(d => toShow.add(d));
  eventDays.forEach(d => toShow.add(d));
  return Array.from(toShow).sort((a, b) => a - b);
}

export function CandidateCard3D({ candidate, curriculumDaysTotal, onStartInterview, onViewDossier }: CandidateCard3DProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const palette = useMemo(() => getPalette(candidate.role, candidate.id), [candidate.role, candidate.id]);

  const completedDays = candidate.completedDays ?? [];
  const skippedDays = candidate.skippedDays ?? [];
  const failedDays = candidate.failedDays ?? [];
  const completedTopics = candidate.completedTopics ?? [];

  // Readiness: based on passed missions vs total curriculum days
  const passedCount = candidate.missionsCompleted ?? completedDays.length;
  const readinessScore = Math.min(100, Math.round((passedCount / curriculumDaysTotal) * 100));

  let readinessLabel = "Needs Practice";
  let readinessTextColor = "text-rose-400";
  let readinessBg = "bg-rose-500/10";
  let readinessBorder = "border-rose-500/20";

  if (readinessScore >= 75) {
    readinessLabel = "Interview Ready";
    readinessTextColor = "text-emerald-400";
    readinessBg = "bg-emerald-500/10";
    readinessBorder = "border-emerald-500/25";
  } else if (readinessScore >= 50) {
    readinessLabel = "Developing";
    readinessTextColor = "text-amber-400";
    readinessBg = "bg-amber-500/10";
    readinessBorder = "border-amber-500/20";
  }

  const timelineDays = useMemo(
    () => getTimelineDays(completedDays, skippedDays, failedDays),
    [completedDays, skippedDays, failedDays]
  );

  // Max topics to show
  const topicsToShow = completedTopics.slice(0, 4);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = -((e.clientY - rect.top - rect.height / 2) / rect.height) * 10;
    const y = ((e.clientX - rect.left - rect.width / 2) / rect.width) * 10;
    setTilt({ x, y });
  }, []);

  const handleMouseLeave = useCallback(() => {
    setIsHovered(false);
    setTilt({ x: 0, y: 0 });
  }, []);

  const handleMouseEnter = useCallback(() => setIsHovered(true), []);

  return (
    <div
      className="perspective-1000 w-full"
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onMouseEnter={handleMouseEnter}
    >
      <div
        ref={cardRef}
        className="relative w-full rounded-[22px] overflow-hidden preserve-3d transition-all duration-200 ease-out"
        style={{
          transform: isHovered
            ? `rotateX(${tilt.x}deg) rotateY(${tilt.y}deg) translateZ(8px)`
            : "rotateX(0deg) rotateY(0deg) translateZ(0)",
          background: `linear-gradient(145deg, #0d1117 0%, #111827 100%)`,
          border: `1px solid ${isHovered ? palette.border : "rgba(255,255,255,0.05)"}`,
          boxShadow: isHovered
            ? `0 24px 48px -12px ${palette.glow}, 0 0 0 1px ${palette.border}`
            : "0 4px 24px -8px rgba(0,0,0,0.6)",
        }}
      >
        {/* Dynamic highlight following mouse */}
        <div
          className="absolute inset-0 pointer-events-none rounded-[22px] transition-opacity duration-300"
          style={{
            opacity: isHovered ? 1 : 0,
            background: `radial-gradient(circle at ${50 + tilt.y * 3}% ${50 - tilt.x * 3}%, rgba(255,255,255,0.04) 0%, transparent 55%)`,
          }}
        />

        {/* ── CHARACTER STAGE ─────────────────────────────────── */}
        <div className={`relative w-full h-[240px] bg-gradient-to-b ${palette.bg} overflow-hidden`}>
          {/* Subtle environment grid */}
          <div
            className="absolute inset-0 opacity-[0.07]"
            style={{
              backgroundImage: `linear-gradient(rgba(255,255,255,0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.4) 1px, transparent 1px)`,
              backgroundSize: "28px 28px",
            }}
          />

          {/* Bottom fade into card body */}
          <div className="absolute bottom-0 left-0 w-full h-24 bg-gradient-to-t from-[#111827] to-transparent z-10" />

          {/* Ambient light source matching candidate palette */}
          <div
            className="absolute inset-0 pointer-events-none"
            style={{ background: `radial-gradient(ellipse 60% 50% at 50% 30%, ${palette.glow} 0%, transparent 70%)` }}
          />

          {/* Avatar — transitions forward on hover */}
          <div
            className="absolute bottom-0 left-1/2 w-[200px] h-[230px] transition-transform duration-250 ease-out"
            style={{
              transform: isHovered
                ? `translateX(-50%) translateZ(30px) scale(1.04) translateY(-6px)`
                : `translateX(-50%) translateZ(0) scale(1) translateY(0)`,
              filter: `drop-shadow(0 12px 24px ${palette.glow})`,
            }}
          >
            <div className="w-full h-full mask-avatar">
              <RealisticAvatar name={candidate.name} id={candidate.id} />
            </div>
          </div>

          {/* Readiness badge — top-right */}
          <div className="absolute top-3 right-3 z-20">
            <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold border ${readinessBg} ${readinessTextColor} ${readinessBorder}`}>
              <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: "currentColor" }} />
              {readinessLabel}
            </span>
          </div>
        </div>

        {/* ── IDENTITY ─────────────────────────────────────────── */}
        <div className="px-5 pt-4 pb-1">
          <h2 className="text-[19px] font-bold text-white tracking-tight leading-tight truncate">
            {candidate.name || candidate.id}
          </h2>
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] mt-0.5" style={{ color: palette.primary }}>
            {candidate.role}
          </p>
          {candidate.experience !== undefined && candidate.experience !== null && (
            <p className="text-[11px] text-slate-500 mt-0.5">
              {candidate.experience > 0 ? `${candidate.experience} yrs exp` : "Entry Level"}
              {candidate.education ? ` · ${candidate.education}` : ""}
            </p>
          )}
        </div>

        {/* ── STATS ──────────────────────────────────────────────── */}
        <div className="grid grid-cols-3 gap-px mx-5 mt-4 rounded-xl overflow-hidden border border-white/[0.04] text-center">
          <div className="bg-white/[0.03] px-3 py-3 flex flex-col items-center">
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-1">Passed</span>
            <span className="text-xl font-bold text-white">{passedCount}</span>
          </div>
          <div className="bg-white/[0.03] px-3 py-3 flex flex-col items-center border-x border-white/[0.04]">
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-1">Days</span>
            <span className="text-xl font-bold text-white">
              {passedCount}
              <span className="text-xs font-medium text-slate-500">/{curriculumDaysTotal}</span>
            </span>
          </div>
          <div className="bg-white/[0.03] px-3 py-3 flex flex-col items-center">
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-1">Ready</span>
            <span className={`text-xl font-bold ${readinessTextColor}`}>{readinessScore}%</span>
          </div>
        </div>

        {/* ── COHORT JOURNEY ─────────────────────────────────────── */}
        <div className="mx-5 mt-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[9px] font-bold text-slate-500 uppercase tracking-[0.15em]">Cohort Journey</span>
            <span className="text-[10px] font-semibold text-slate-400">
              {passedCount} / {curriculumDaysTotal} days
              {candidate.skipped ? <span className="ml-1 text-slate-600">· {candidate.skipped} skipped</span> : null}
            </span>
          </div>

          {/* Progress bar */}
          <div className="relative h-[5px] w-full rounded-full bg-white/[0.06] overflow-hidden mb-3">
            <div
              className={`absolute top-0 left-0 h-full rounded-full bg-gradient-to-r ${palette.bar}`}
              style={{ width: `${readinessScore}%`, transition: "width 1s ease-out" }}
            />
          </div>

          {/* Timeline nodes — strictly from candidate's actual days */}
          {timelineDays.length > 0 && (
            <div className="flex items-end gap-1 mt-1 flex-wrap">
              {timelineDays.slice(0, 14).map((day) => {
                const isCompleted = completedDays.includes(day);
                const isSkipped = skippedDays.includes(day);
                const isFailed = failedDays.includes(day);

                let nodeColor = "bg-white/[0.08]";
                let textColor = "text-slate-700";
                let Icon = null as React.FC<{className?: string}> | null;

                if (isCompleted) {
                  nodeColor = "";
                  textColor = "text-slate-300";
                } else if (isSkipped) {
                  nodeColor = "bg-amber-500/20";
                  textColor = "text-amber-600";
                  Icon = SkipForward;
                } else if (isFailed) {
                  nodeColor = "bg-rose-500/15";
                  textColor = "text-rose-600";
                  Icon = XCircle;
                }

                return (
                  <div key={day} className="flex flex-col items-center gap-[3px]">
                    <div
                      className={`w-[26px] h-[26px] rounded-[6px] flex items-center justify-center text-[8px] font-bold font-mono transition-all duration-200 ${nodeColor} ${textColor}`}
                      style={isCompleted ? { background: `${palette.primary}22`, color: palette.primary, border: `1px solid ${palette.primary}40` } : {}}
                      title={isCompleted ? "Passed" : isSkipped ? "Skipped" : isFailed ? "Failed" : "Not completed"}
                    >
                      {Icon ? <Icon className="w-2.5 h-2.5" /> : day}
                    </div>
                  </div>
                );
              })}
              {timelineDays.length > 14 && (
                <div className="flex items-center justify-center w-[26px] h-[26px] rounded-[6px] bg-white/[0.04] text-[8px] text-slate-600 font-mono font-bold">
                  +{timelineDays.length - 14}
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── INTERVIEWABLE TOPICS ──────────────────────────────── */}
        {topicsToShow.length > 0 && (
          <div className="mx-5 mt-4">
            <div className="flex items-center gap-1.5 mb-2">
              <BookOpen className="w-3 h-3 text-slate-500" />
              <span className="text-[9px] font-bold text-slate-500 uppercase tracking-[0.15em]">Interviewable Topics</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {topicsToShow.map((topic, i) => (
                <span
                  key={i}
                  className="text-[10px] font-medium px-2 py-1 rounded-md border text-slate-300"
                  style={{ background: `${palette.primary}12`, borderColor: `${palette.primary}30`, color: palette.primary }}
                >
                  {topic}
                </span>
              ))}
              {completedTopics.length > 4 && (
                <span className="text-[10px] font-medium px-2 py-1 rounded-md bg-white/[0.04] border border-white/[0.06] text-slate-500">
                  +{completedTopics.length - 4} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* ── SIGNALS ──────────────────────────────────────────── */}
        {(candidate.struggles !== undefined || candidate.missionsFirstTry !== undefined) && (
          <div className="mx-5 mt-4 flex items-center gap-3">
            {candidate.missionsFirstTry !== undefined && candidate.missionsFirstTry > 0 && (
              <div className="flex items-center gap-1 text-[10px] text-emerald-500">
                <CheckCircle className="w-3 h-3" />
                <span>{candidate.missionsFirstTry} first try</span>
              </div>
            )}
            {candidate.struggles !== undefined && candidate.struggles > 0 && (
              <div className="flex items-center gap-1 text-[10px] text-amber-500/80">
                <span>⟳</span>
                <span>{candidate.struggles} struggled</span>
              </div>
            )}
            {candidate.failed !== undefined && candidate.failed > 0 && (
              <div className="flex items-center gap-1 text-[10px] text-rose-500/70">
                <XCircle className="w-3 h-3" />
                <span>{candidate.failed} failed</span>
              </div>
            )}
          </div>
        )}

        {/* ── ACTIONS ──────────────────────────────────────────── */}
        <div className="flex items-stretch gap-2 mx-5 mt-5 mb-5">
          <button
            onClick={() => onViewDossier?.(candidate.id)}
            className="flex items-center justify-center gap-1.5 px-3 py-3 rounded-[12px] border border-white/[0.06] bg-white/[0.03] hover:bg-white/[0.07] text-slate-400 hover:text-white text-xs font-semibold transition-all duration-200"
            title="View full dossier"
          >
            <BookOpen className="w-4 h-4" />
            Dossier
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); onStartInterview(candidate.id); }}
            className="flex-1 flex items-center justify-center gap-2 py-3 rounded-[12px] text-white text-sm font-bold transition-all duration-200 group/btn"
            style={{
              background: `linear-gradient(135deg, ${palette.primary}, ${palette.secondary})`,
              boxShadow: isHovered ? `0 8px 24px -6px ${palette.glow}` : "none",
            }}
          >
            Start Interview
            <ArrowRight className="w-4 h-4 transition-transform duration-200 group-hover/btn:translate-x-1" />
          </button>
        </div>
      </div>
    </div>
  );
}
