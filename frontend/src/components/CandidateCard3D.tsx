import { useRef, useState, useMemo, useCallback } from "react";
import type { CandidateSummary } from "../types";
import { RealisticAvatar } from "./CandidateCharacter";
import { getPalette, type CandidatePalette } from "../utils/palette";
import { ArrowRight, BookOpen, AlertCircle, SkipForward, Sparkles } from "lucide-react";

interface CandidateCard3DProps {
  candidate: CandidateSummary;
  curriculumDaysTotal: number;
  onStartInterview: (id: string) => void;
  onViewDossier?: (id: string) => void;
  animationDelay?: number;
}

// Role → environment keyword for the cinematic stage tag
function getEnvLabel(role: string): string {
  const r = (role || "").toLowerCase();
  if (r.includes("data"))        return "Data Lab";
  if (r.includes("ai") || r.includes("machine")) return "AI Research";
  if (r.includes("devops") || r.includes("cloud")) return "Infrastructure";
  if (r.includes("backend"))     return "API Engineering";
  if (r.includes("software") || r.includes("engineer")) return "Engineering";
  if (r.includes("marketing"))   return "Growth Studio";
  if (r.includes("hr"))          return "People Ops";
  if (r.includes("analyst"))     return "Analytics";
  if (r.includes("ux") || r.includes("researcher")) return "UX Research";
  if (r.includes("architect"))   return "Architecture";
  if (r.includes("mobile"))      return "Mobile";
  if (r.includes("junior") || r.includes("intern")) return "Early Career";
  if (r.includes("legacy"))      return "Systems";
  if (r.includes("it support"))  return "IT Ops";
  return "Engineering";
}

// Environment SVG patterns per category
function EnvPattern({ role, palette }: { role: string; palette: CandidatePalette }) {
  const r = (role || "").toLowerCase();
  const c = palette.p;

  if (r.includes("data") || r.includes("analyst")) {
    return (
      <svg className="absolute inset-0 w-full h-full opacity-[0.18]" viewBox="0 0 320 200" fill="none">
        {[20,50,80,110,140,170,200,230,260,290].map((x,i) => (
          <rect key={i} x={x} y={100 + Math.sin(i * 0.9) * 35} width="18" height={80 - Math.sin(i*0.9)*35}
            fill={c} fillOpacity={0.3 + (i % 3) * 0.15} rx="2"/>
        ))}
        {[0,1,2,3,4].map(i => (
          <line key={i} x1="0" y1={40 + i*30} x2="320" y2={40 + i*30} stroke={c} strokeOpacity="0.15" strokeDasharray="4 8"/>
        ))}
        <path d="M10,170 L50,130 L100,145 L160,100 L220,115 L280,80 L320,90" stroke={c} strokeWidth="1.5" strokeOpacity="0.5" fill="none" strokeLinecap="round"/>
        <circle cx="160" cy="100" r="3" fill={c} fillOpacity="0.8"/>
        <circle cx="280" cy="80"  r="3" fill={c} fillOpacity="0.8"/>
      </svg>
    );
  }
  if (r.includes("ai") || r.includes("machine")) {
    return (
      <svg className="absolute inset-0 w-full h-full opacity-[0.18]" viewBox="0 0 320 200" fill="none">
        {[[60,60],[60,100],[60,140]].map(([y1], i) =>
          [60,100,140,180].map((dy, j) => (
            <line key={`${i}-${j}`} x1="70" y1={y1} x2="150" y2={dy} stroke={c} strokeOpacity="0.2" strokeWidth="0.8"/>
          ))
        )}
        {[60,100,140,180].map((sy, i) =>
          [80,120,160].map((dy, j) => (
            <line key={`r${i}-${j}`} x1="170" y1={sy} x2="250" y2={dy} stroke={c} strokeOpacity="0.2" strokeWidth="0.8"/>
          ))
        )}
        {[60,100,140].map(y => <circle key={y} cx="65" cy={y} r="5" fill={c} fillOpacity="0.5" stroke={c} strokeOpacity="0.8" strokeWidth="1"/>)}
        {[60,100,140,180].map(y => <circle key={y} cx="160" cy={y} r="5" fill={c} fillOpacity="0.4" stroke={c} strokeOpacity="0.7" strokeWidth="1"/>)}
        {[80,120,160].map(y => <circle key={y} cx="255" cy={y} r="5" fill={c} fillOpacity="0.6" stroke={c} strokeOpacity="0.9" strokeWidth="1"/>)}
      </svg>
    );
  }
  if (r.includes("devops") || r.includes("cloud")) {
    return (
      <svg className="absolute inset-0 w-full h-full opacity-[0.18]" viewBox="0 0 320 200" fill="none">
        {[0,1,2,3,4,5].map(i => (
          <rect key={i} x="60" y={20 + i * 28} width="200" height="20" rx="3" stroke={c} strokeOpacity="0.4" strokeWidth="1" fill={c} fillOpacity={i === 2 ? 0.12 : 0.04}/>
        ))}
        {[0,1,2,3,4,5].map(i => (
          <circle key={i} cx="248" cy={30 + i * 28} r="4" fill={i === 2 ? c : "transparent"} stroke={c} strokeOpacity={i === 2 ? 0.9 : 0.3} strokeWidth="1.2"/>
        ))}
        <line x1="160" y1="188" x2="160" y2="168" stroke={c} strokeOpacity="0.4" strokeWidth="1" strokeDasharray="3 3"/>
        <line x1="100" y1="188" x2="220" y2="188" stroke={c} strokeOpacity="0.3" strokeWidth="1"/>
      </svg>
    );
  }
  if (r.includes("marketing") || r.includes("hr") || r.includes("ux") || r.includes("researcher")) {
    return (
      <svg className="absolute inset-0 w-full h-full opacity-[0.18]" viewBox="0 0 320 200" fill="none">
        <path d="M-10,100 C60,60 120,140 180,90 C240,40 280,120 330,80" stroke={c} strokeWidth="2" strokeOpacity="0.5" fill="none" strokeLinecap="round"/>
        <path d="M-10,130 C50,90 130,160 200,110 C270,60 300,140 330,100" stroke={c} strokeWidth="1.2" strokeOpacity="0.3" fill="none" strokeLinecap="round"/>
        {[60,130,200,270].map((x,i) => (
          <circle key={i} cx={x} cy={[90, 115, 80, 105][i]} r="4" fill={c} fillOpacity={0.5 + i*0.1}/>
        ))}
        {[1,2,3,4,5,6].map(i => (
          <circle key={i} cx={i*50} cy={50} r={2+i*0.5} fill={c} fillOpacity="0.15"/>
        ))}
      </svg>
    );
  }
  // Default — code / terminal lines
  return (
    <svg className="absolute inset-0 w-full h-full opacity-[0.15]" viewBox="0 0 320 200" fill="none">
      {[30,55,80,110,135,160].map((y,i) => (
        <rect key={i} x={20 + (i%3)*8} y={y} width={60 + Math.sin(i*1.3)*60} height="8" rx="2" fill={c} fillOpacity={0.15 + (i%3)*0.08}/>
      ))}
      <rect x="20" y="180" width="8" height="10" rx="1.5" fill={c} fillOpacity="0.6"/>
      {[1,2,3].map(i => (
        <path key={i} d={`M${80+i*60},50 L${100+i*60},65 L${80+i*60},80`} stroke={c} strokeWidth="1.5" strokeOpacity="0.3" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
      ))}
    </svg>
  );
}

// ─── MAIN COMPONENT ──────────────────────────────────────────
export function CandidateCard3D({
  candidate,
  curriculumDaysTotal,
  onStartInterview,
  onViewDossier,
  animationDelay = 0,
}: CandidateCard3DProps) {
  const cardRef  = useRef<HTMLDivElement>(null);
  const [tilt, setTilt]       = useState({ x: 0, y: 0 });
  const [hovered, setHovered] = useState(false);

  const palette = useMemo(() => getPalette(candidate.id, candidate.role), [candidate.id, candidate.role]);
  const envLabel = useMemo(() => getEnvLabel(candidate.role), [candidate.role]);

  // Real candidate data
  const completedDays  = candidate.completedDays  ?? [];
  const skippedDays    = candidate.skippedDays    ?? [];
  const failedDays     = candidate.failedDays     ?? [];
  const completedTopics = candidate.completedTopics ?? [];
  const passed = candidate.missionsCompleted ?? completedDays.length;

  // Readiness calculation
  const readinessPct = Math.min(100, Math.round((passed / Math.max(curriculumDaysTotal, 1)) * 100));

  const readiness = useMemo(() => {
    if (readinessPct >= 75) return { label: "Interview Ready", color: "#22c55e", bg: "rgba(34,197,94,0.12)", border: "rgba(34,197,94,0.25)" };
    if (readinessPct >= 45) return { label: "Developing",      color: "#f59e0b", bg: "rgba(245,158,11,0.12)",  border: "rgba(245,158,11,0.22)" };
    return                         { label: "Needs Practice",  color: "#fb7185", bg: "rgba(251,113,133,0.12)", border: "rgba(251,113,133,0.22)" };
  }, [readinessPct]);

  // Timeline: milestone days on the cohort track, each tagged with the
  // candidate's real per-day outcome.
  const timeline = useMemo(() => {
    const milestones = [1, 7, 12, 16, 22, 27, 31];
    return milestones.map((day) => {
      const done    = completedDays.includes(day);
      const skipped = skippedDays.includes(day);
      const failed  = failedDays.includes(day);
      return { day, done, skipped, failed };
    });
  }, [completedDays, skippedDays, failedDays]);

  // Topics to show on card
  const visibleTopics = completedTopics.slice(0, 3);

  // 3D tilt handlers
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const { left, top, width, height } = cardRef.current.getBoundingClientRect();
    setTilt({
      x: -((e.clientY - top  - height / 2) / height) * 8,
      y:  ((e.clientX - left - width  / 2) / width)  * 8,
    });
  }, []);
  const handleLeave  = useCallback(() => { setHovered(false); setTilt({ x:0, y:0 }); }, []);
  const handleEnter  = useCallback(() => setHovered(true), []);

  return (
    <div
      className="perspective-1000 w-full animate-fade-up"
      style={{ animationDelay: `${animationDelay}ms` }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleLeave}
      onMouseEnter={handleEnter}
    >
      {/* Outer glow that appears on hover */}
      <div
        className="absolute inset-0 rounded-[20px] pointer-events-none transition-opacity duration-300"
        style={{
          opacity: hovered ? 1 : 0,
          background: `radial-gradient(ellipse at 50% 0%, ${palette.ring} 0%, transparent 65%)`,
          filter: "blur(16px)",
          transform: "translateY(-4px) scaleX(0.85)",
        }}
      />

      <div
        ref={cardRef}
        className="candidate-card preserve-3d relative"
        style={{
          transform: hovered
            ? `rotateX(${tilt.x}deg) rotateY(${tilt.y}deg) translateZ(6px) translateY(-6px)`
            : "rotateX(0deg) rotateY(0deg) translateZ(0)",
          boxShadow: hovered
            ? `0 32px 64px -20px rgba(0,0,0,0.85), 0 0 0 1px rgba(255,255,255,0.08), inset 0 1px 0 rgba(255,255,255,0.06)`
            : `0 4px 24px -8px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.04)`,
          borderColor: hovered ? `${palette.p}30` : "rgba(255,255,255,0.06)",
          transition: "transform 280ms cubic-bezier(0.25,0.8,0.25,1), box-shadow 280ms cubic-bezier(0.25,0.8,0.25,1), border-color 280ms ease",
        }}
      >
        {/* Mouse-tracking highlight */}
        <div
          className="absolute inset-0 rounded-[20px] pointer-events-none z-[1]"
          style={{
            opacity: hovered ? 1 : 0,
            background: `radial-gradient(circle at ${50 + tilt.y * 4}% ${50 - tilt.x * 4}%, rgba(255,255,255,0.05) 0%, transparent 55%)`,
            transition: "opacity 200ms ease",
          }}
        />

        {/* ─── CHARACTER STAGE ────────────────────────────────── */}
        <div
          className="relative w-full overflow-hidden"
          style={{ height: "260px", borderRadius: "20px 20px 0 0" }}
        >
          {/* Atmospheric background */}
          <div
            className="absolute inset-0"
            style={{ background: "linear-gradient(160deg, var(--ink-850) 0%, var(--ink-800) 100%)" }}
          />

          {/* Candidate-specific color bloom */}
          <div
            className="absolute inset-0"
            style={{ background: `linear-gradient(${palette.env})` }}
          />

          {/* Environment pattern SVG */}
          <EnvPattern role={candidate.role} palette={palette} />

          {/* Subtle grid texture */}
          <div
            className="absolute inset-0 opacity-[0.06]"
            style={{
              backgroundImage: `
                linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)
              `,
              backgroundSize: "32px 32px",
            }}
          />

          {/* Vertical fade at bottom — blends stage into card body */}
          <div
            className="absolute bottom-0 left-0 w-full"
            style={{
              height: "100px",
              background: "linear-gradient(to top, var(--ink-900) 0%, transparent 100%)",
              zIndex: 3,
            }}
          />

          {/* Ambient light source */}
          <div
            className="absolute"
            style={{
              inset: 0,
              background: `radial-gradient(ellipse 70% 55% at 50% 25%, ${palette.glow} 0%, transparent 70%)`,
              opacity: hovered ? 0.8 : 0.5,
              transition: "opacity 300ms ease",
              zIndex: 2,
            }}
          />

          {/* Rim light from behind character */}
          <div
            className="absolute bottom-8 left-1/2 -translate-x-1/2"
            style={{
              width: "120px",
              height: "50px",
              background: palette.p,
              filter: "blur(28px)",
              opacity: hovered ? 0.35 : 0.2,
              transition: "opacity 300ms ease",
              zIndex: 2,
            }}
          />

          {/* Character — pops forward on hover */}
          <div
            className="absolute bottom-0 left-1/2"
            style={{
              width: "200px",
              height: "255px",
              zIndex: 4,
              transition: "transform 300ms cubic-bezier(0.25,0.8,0.25,1), filter 300ms ease",
              transform: hovered
                ? "translateX(-50%) translateY(-8px) scale(1.04)"
                : "translateX(-50%) translateY(0) scale(1)",
              filter: hovered
                ? `drop-shadow(0 16px 32px ${palette.glow})`
                : "drop-shadow(0 8px 16px rgba(0,0,0,0.5))",
            }}
          >
            <div className="w-full h-full mask-avatar">
              <RealisticAvatar name={candidate.name} id={candidate.id} />
            </div>
          </div>

          {/* Readiness badge — top right */}
          <div className="absolute top-3 right-3 z-10">
            <div
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold"
              style={{
                background: readiness.bg,
                border: `1px solid ${readiness.border}`,
                color: readiness.color,
                backdropFilter: "blur(6px)",
              }}
            >
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ background: readiness.color, boxShadow: `0 0 5px ${readiness.color}` }}
              />
              {readiness.label}
            </div>
          </div>

          {/* Environment label — top left */}
          <div className="absolute top-3 left-3 z-10">
            <div
              className="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-[0.14em]"
              style={{
                background: `${palette.p}18`,
                border: `1px solid ${palette.p}30`,
                color: palette.p,
                backdropFilter: "blur(6px)",
              }}
            >
              {envLabel}
            </div>
          </div>
        </div>

        {/* ─── CARD BODY ──────────────────────────────────────── */}
        <div className="px-5 pb-5 flex flex-col gap-4">

          {/* Identity */}
          <div className="pt-3">
            <h2
              className="text-[20px] font-bold text-white leading-tight tracking-tight truncate"
              title={candidate.name}
            >
              {candidate.name || candidate.id}
            </h2>
            <p
              className="text-[11px] font-semibold uppercase tracking-[0.13em] mt-1"
              style={{ color: palette.p }}
            >
              {candidate.role}
            </p>
            {candidate.experience !== undefined && (
              <p className="text-[11px] text-slate-500 mt-0.5">
                {candidate.experience > 0 ? `${candidate.experience} yrs exp` : "Entry level"}
                {candidate.education ? ` · ${candidate.education}` : ""}
              </p>
            )}
          </div>

          {/* Stats row — distinct real signals, no duplicated cells */}
          <div
            className="grid grid-cols-3 text-center rounded-[12px] overflow-hidden"
            style={{ border: "1px solid rgba(255,255,255,0.06)" }}
          >
            {[
              { label: "Missions",   value: `${passed}`, color: "#fff" },
              { label: "First-try",  value: `${candidate.missionsFirstTry ?? 0}`, color: "#34d399" },
              { label: "Readiness",  value: `${readinessPct}%`, color: readiness.color },
            ].map((s, i) => (
              <div
                key={i}
                className={`py-3 flex flex-col items-center ${i === 1 ? "border-x" : ""}`}
                style={{ borderColor: "rgba(255,255,255,0.06)", background: "rgba(255,255,255,0.025)" }}
              >
                <span className="text-[9px] font-bold uppercase tracking-[0.14em] text-slate-500 mb-1">{s.label}</span>
                <span className="stat-number text-lg font-bold" style={{ color: s.color }}>
                  {s.value}
                </span>
              </div>
            ))}
          </div>

          {/* Cohort Journey — milestone track with real per-day outcomes */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[9px] font-bold uppercase tracking-[0.14em] text-slate-500">Cohort Journey</span>
              <span className="text-[10px] font-semibold text-slate-400">
                {passed}/{curriculumDaysTotal}
                {(candidate.skipped ?? 0) > 0 && (
                  <span className="ml-1 text-slate-600">· {candidate.skipped} skipped</span>
                )}
              </span>
            </div>

            {/* Progress bar */}
            <div
              className="relative h-[4px] w-full rounded-full mb-4"
              style={{ background: "rgba(255,255,255,0.07)" }}
            >
              <div
                className="absolute top-0 left-0 h-full rounded-full progress-animated"
                style={{
                  width: `${readinessPct}%`,
                  background: `linear-gradient(90deg, ${palette.bar})`,
                  boxShadow: `0 0 8px ${palette.p}60`,
                }}
              />
            </div>

            {/* Journey track — nodes connected by a continuous line */}
            <div className="journey-track">
              {timeline.map(({ day, done, skipped, failed }) => {
                const state = done ? "passed" : (skipped ? "skipped" : (failed ? "failed" : "upcoming"));
                const isCurrent = !done && !skipped && !failed && day === (passed + 1 <= 31 ? passed + 1 : -1);
                return (
                  <div
                    key={day}
                    className="journey-node"
                    title={`Day ${day}${done ? " ✓ passed" : skipped ? " (skipped)" : failed ? " ✗ failed" : " — upcoming"}`}
                    style={{
                      "--node-color": palette.p,
                      "--node-glow": palette.ring,
                    } as React.CSSProperties}
                  >
                    <span
                      className={`node-dot ${state === "passed" ? "passed" : ""} ${isCurrent ? "current" : ""}`}
                      style={
                        state === "skipped"
                          ? { borderColor: "rgba(245,158,11,0.6)" }
                          : state === "failed"
                            ? { borderColor: "rgba(251,113,133,0.6)" }
                            : undefined
                      }
                    />
                    <span className={`node-label ${done ? "lit" : ""}`}>D{String(day).padStart(2, "0")}</span>
                  </div>
                );
              })}
            </div>

            {/* Outcome legend — distinct real signals, no duplicated counts */}
            {(candidate.struggles ?? 0) > 0 || (candidate.failed ?? 0) > 0 || (candidate.skipped ?? 0) > 0 || (candidate.missionsFirstTry ?? 0) > 0 ? (
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2.5 pt-2 border-t" style={{ borderColor: "rgba(255,255,255,0.05)" }}>
                {(candidate.struggles ?? 0) > 0 && (
                  <span className="flex items-center gap-1 text-[9.5px] text-amber-400/90">
                    <AlertCircle className="w-3 h-3" /> {candidate.struggles} struggled
                  </span>
                )}
                {(candidate.failed ?? 0) > 0 && (
                  <span className="flex items-center gap-1 text-[9.5px] text-rose-400/90">
                    <AlertCircle className="w-3 h-3" /> {candidate.failed} failed
                  </span>
                )}
                {(candidate.skipped ?? 0) > 0 && (
                  <span className="flex items-center gap-1 text-[9.5px] text-slate-400/90">
                    <SkipForward className="w-3 h-3" /> {candidate.skipped} skipped
                  </span>
                )}
                {(candidate.missionsFirstTry ?? 0) > 0 && (
                  <span className="flex items-center gap-1 text-[9.5px] text-emerald-400/90">
                    <Sparkles className="w-3 h-3" /> {candidate.missionsFirstTry} first-try
                  </span>
                )}
              </div>
            ) : null}
          </div>

          {/* Interviewable topics — REAL data from backend */}
          {visibleTopics.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <BookOpen className="w-3 h-3 text-slate-500" />
                <span className="text-[9px] font-bold uppercase tracking-[0.14em] text-slate-500">
                  Interviewable Topics
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {visibleTopics.map((t, i) => (
                  <span
                    key={i}
                    className="topic-chip"
                    style={{
                      background: `${palette.p}14`,
                      borderColor: `${palette.p}28`,
                      color: palette.p,
                    }}
                  >
                    {t}
                  </span>
                ))}
                {completedTopics.length > 3 && (
                  <span
                    className="topic-chip text-slate-500"
                    style={{ background: "rgba(255,255,255,0.04)", borderColor: "rgba(255,255,255,0.07)" }}
                  >
                    +{completedTopics.length - 3}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* ─── ACTIONS ────────────────────────────────────── */}
          <div className="flex items-center gap-2 pt-1">
            {/* Secondary: Dossier */}
            <button
              onClick={() => onViewDossier?.(candidate.id)}
              className="btn btn-secondary flex-1 !py-2.5 text-[12px]"
            >
              <BookOpen className="w-3.5 h-3.5" />
              Dossier
            </button>

            {/* Primary: Start Interview */}
            <button
              onClick={(e) => { e.stopPropagation(); onStartInterview(candidate.id); }}
              className="btn flex-1 !py-2.5 text-[13px] group/ibtn"
              style={{
                color: "#fff",
                background: `linear-gradient(135deg, ${palette.bar})`,
                boxShadow: hovered
                  ? `0 8px 24px -6px ${palette.glow}, inset 0 1px 0 rgba(255,255,255,0.15)`
                  : `0 4px 12px -4px ${palette.glow}, inset 0 1px 0 rgba(255,255,255,0.10)`,
                border: "1px solid rgba(255,255,255,0.12)",
              }}
            >
              Start Interview
              <ArrowRight className="w-3.5 h-3.5 transition-transform duration-200 group-hover/ibtn:translate-x-1" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
