import { useRef, useState, useMemo, useCallback } from "react";
import type { CandidateSummary } from "../types";
import { RealisticAvatar } from "./CandidateCharacter";
import { ArrowRight, BookOpen, CheckCircle, AlertCircle, SkipForward } from "lucide-react";

interface CandidateCard3DProps {
  candidate: CandidateSummary;
  curriculumDaysTotal: number;
  onStartInterview: (id: string) => void;
  onViewDossier?: (id: string) => void;
  animationDelay?: number;
}

// ─── 20-PALETTE DETERMINISTIC SYSTEM ────────────────────────
// Each palette has: primary color, secondary color, environment gradient,
// glow color, progress gradient, and environment label.
const PALETTES = [
  // 0 — Cyan + Indigo (Data / Analytics)
  { p:"#22d3ee", s:"#6366f1", env:"135deg,rgba(34,211,238,0.18) 0%,rgba(99,102,241,0.12) 60%,transparent 100%", glow:"rgba(34,211,238,0.3)", bar:"#22d3ee,#6366f1", ring:"rgba(34,211,238,0.35)" },
  // 1 — Violet + Magenta (AI / ML)
  { p:"#a78bfa", s:"#e879f9", env:"135deg,rgba(167,139,250,0.18) 0%,rgba(232,121,249,0.10) 60%,transparent 100%", glow:"rgba(167,139,250,0.3)", bar:"#a78bfa,#e879f9", ring:"rgba(167,139,250,0.35)" },
  // 2 — Emerald + Cyan (DevOps / Cloud)
  { p:"#34d399", s:"#22d3ee", env:"135deg,rgba(52,211,153,0.18) 0%,rgba(34,211,238,0.10) 60%,transparent 100%", glow:"rgba(52,211,153,0.3)", bar:"#34d399,#22d3ee", ring:"rgba(52,211,153,0.35)" },
  // 3 — Amber + Orange (Business / Analyst)
  { p:"#fbbf24", s:"#fb923c", env:"135deg,rgba(251,191,36,0.18) 0%,rgba(251,146,60,0.10) 60%,transparent 100%", glow:"rgba(251,191,36,0.28)", bar:"#fbbf24,#fb923c", ring:"rgba(251,191,36,0.35)" },
  // 4 — Rose + Coral (HR / Marketing)
  { p:"#fb7185", s:"#f97316", env:"135deg,rgba(251,113,133,0.18) 0%,rgba(249,115,22,0.10) 60%,transparent 100%", glow:"rgba(251,113,133,0.28)", bar:"#fb7185,#f97316", ring:"rgba(251,113,133,0.32)" },
  // 5 — Indigo + Sky (Software / Backend)
  { p:"#818cf8", s:"#38bdf8", env:"135deg,rgba(129,140,248,0.18) 0%,rgba(56,189,248,0.10) 60%,transparent 100%", glow:"rgba(129,140,248,0.3)", bar:"#818cf8,#38bdf8", ring:"rgba(129,140,248,0.35)" },
  // 6 — Teal + Lime (Full-stack / Engineer)
  { p:"#2dd4bf", s:"#a3e635", env:"135deg,rgba(45,212,191,0.18) 0%,rgba(163,230,53,0.10) 60%,transparent 100%", glow:"rgba(45,212,191,0.28)", bar:"#2dd4bf,#a3e635", ring:"rgba(45,212,191,0.32)" },
  // 7 — Coral + Violet (UX / Creative)
  { p:"#f43f5e", s:"#8b5cf6", env:"135deg,rgba(244,63,94,0.18) 0%,rgba(139,92,246,0.10) 60%,transparent 100%", glow:"rgba(244,63,94,0.28)", bar:"#f43f5e,#8b5cf6", ring:"rgba(244,63,94,0.32)" },
  // 8 — Sky + Emerald (Architect / Principal)
  { p:"#38bdf8", s:"#34d399", env:"135deg,rgba(56,189,248,0.18) 0%,rgba(52,211,153,0.10) 60%,transparent 100%", glow:"rgba(56,189,248,0.28)", bar:"#38bdf8,#34d399", ring:"rgba(56,189,248,0.32)" },
  // 9 — Magenta + Amber (Legacy / Senior)
  { p:"#d946ef", s:"#fbbf24", env:"135deg,rgba(217,70,239,0.16) 0%,rgba(251,191,36,0.10) 60%,transparent 100%", glow:"rgba(217,70,239,0.26)", bar:"#d946ef,#fbbf24", ring:"rgba(217,70,239,0.32)" },
];

function getPalette(id: string, role: string) {
  const r = (role || "").toLowerCase();
  // Role-based primary mapping
  if (r.includes("data engineer") || r.includes("data scientist")) return PALETTES[0];
  if (r.includes("ai engineer") || r.includes("machine learning"))   return PALETTES[1];
  if (r.includes("devops") || r.includes("cloud") || r.includes("infrastructure")) return PALETTES[2];
  if (r.includes("business") || r.includes("analyst"))               return PALETTES[3];
  if (r.includes("hr") || r.includes("marketing") || r.includes("manager")) return PALETTES[4];
  if (r.includes("backend") || r.includes("server"))                 return PALETTES[5];
  if (r.includes("software") || r.includes("full"))                  return PALETTES[6];
  if (r.includes("ux") || r.includes("researcher") || r.includes("creative")) return PALETTES[7];
  if (r.includes("architect") || r.includes("principal") || r.includes("distinguished")) return PALETTES[8];
  if (r.includes("legacy") || r.includes("it support") || r.includes("senior")) return PALETTES[9];
  if (r.includes("mobile") || r.includes("frontend"))               return PALETTES[6];
  if (r.includes("junior") || r.includes("intern"))                 return PALETTES[5];
  // Deterministic fallback from id
  const n = id.split("").reduce((a, c) => a + c.charCodeAt(0), 0);
  return PALETTES[n % PALETTES.length];
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
function EnvPattern({ role, palette }: { role: string; palette: typeof PALETTES[0] }) {
  const r = (role || "").toLowerCase();
  const c = palette.p;

  if (r.includes("data") || r.includes("analyst")) {
    // Data grid / bar chart lines
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
    // Neural network nodes
    return (
      <svg className="absolute inset-0 w-full h-full opacity-[0.18]" viewBox="0 0 320 200" fill="none">
        {/* Layer connections */}
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
        {/* Nodes */}
        {[60,100,140].map(y => <circle key={y} cx="65" cy={y} r="5" fill={c} fillOpacity="0.5" stroke={c} strokeOpacity="0.8" strokeWidth="1"/>)}
        {[60,100,140,180].map(y => <circle key={y} cx="160" cy={y} r="5" fill={c} fillOpacity="0.4" stroke={c} strokeOpacity="0.7" strokeWidth="1"/>)}
        {[80,120,160].map(y => <circle key={y} cx="255" cy={y} r="5" fill={c} fillOpacity="0.6" stroke={c} strokeOpacity="0.9" strokeWidth="1"/>)}
      </svg>
    );
  }
  if (r.includes("devops") || r.includes("cloud")) {
    // Server rack grid
    return (
      <svg className="absolute inset-0 w-full h-full opacity-[0.18]" viewBox="0 0 320 200" fill="none">
        {[0,1,2,3,4,5].map(i => (
          <rect key={i} x="60" y={20 + i * 28} width="200" height="20" rx="3" stroke={c} strokeOpacity="0.4" strokeWidth="1" fill={c} fillOpacity={i === 2 ? 0.12 : 0.04}/>
        ))}
        {[0,1,2,3,4,5].map(i => (
          <circle key={i} cx="248" cy={30 + i * 28} r="4" fill={i === 2 ? c : "transparent"} stroke={c} strokeOpacity={i === 2 ? 0.9 : 0.3} strokeWidth="1.2"/>
        ))}
        {/* Connection lines */}
        <line x1="160" y1="188" x2="160" y2="168" stroke={c} strokeOpacity="0.4" strokeWidth="1" strokeDasharray="3 3"/>
        <line x1="100" y1="188" x2="220" y2="188" stroke={c} strokeOpacity="0.3" strokeWidth="1"/>
      </svg>
    );
  }
  if (r.includes("marketing") || r.includes("hr") || r.includes("ux") || r.includes("researcher")) {
    // Creative wave / flow
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
      {/* Cursor blink */}
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
    if (readinessPct >= 75) return { label: "Interview Ready", color: "#34d399", bg: "rgba(52,211,153,0.12)", border: "rgba(52,211,153,0.25)" };
    if (readinessPct >= 45) return { label: "Developing",      color: "#fbbf24", bg: "rgba(251,191,36,0.12)",  border: "rgba(251,191,36,0.22)" };
    return                         { label: "Needs Practice",  color: "#fb7185", bg: "rgba(251,113,133,0.12)", border: "rgba(251,113,133,0.22)" };
  }, [readinessPct]);

  // Timeline: show milestone days that have any event + key boundary days
  const timelineDays = useMemo(() => {
    const events = new Set([...completedDays, ...skippedDays, ...failedDays]);
    const milestones = [1, 7, 12, 16, 22, 27, 31];
    milestones.forEach(d => events.add(d));
    return Array.from(events).sort((a, b) => a - b).slice(0, 12);
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
          borderColor: hovered ? `${palette.p}30` : "rgba(255,255,255,0.055)",
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
            style={{
              background: `linear-gradient(160deg, #0a0d1a 0%, #0c1020 100%)`,
            }}
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
              background: `linear-gradient(to top, #090d18 0%, transparent 100%)`,
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
            className="absolute bottom-0 left-1/2 -translate-x-1/2"
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
                : `drop-shadow(0 8px 16px rgba(0,0,0,0.5))`,
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

          {/* Stats row */}
          <div
            className="grid grid-cols-3 text-center rounded-[12px] overflow-hidden"
            style={{ border: "1px solid rgba(255,255,255,0.06)" }}
          >
            {[
              { label: "Passed",   value: `${passed}` },
              { label: "Days",     value: `${passed}`, suffix: `/${curriculumDaysTotal}` },
              { label: "Readiness", value: `${readinessPct}%`, color: readiness.color },
            ].map((s, i) => (
              <div
                key={i}
                className={`py-3 flex flex-col items-center ${i === 1 ? "border-x" : ""}`}
                style={{ borderColor: "rgba(255,255,255,0.06)", background: "rgba(255,255,255,0.025)" }}
              >
                <span className="text-[9px] font-bold uppercase tracking-[0.14em] text-slate-500 mb-1">{s.label}</span>
                <span className="text-lg font-bold" style={{ color: s.color ?? "#fff" }}>
                  {s.value}
                  {s.suffix && <span className="text-[11px] font-medium text-slate-500">{s.suffix}</span>}
                </span>
              </div>
            ))}
          </div>

          {/* Cohort Journey */}
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
              className="relative h-[4px] w-full rounded-full mb-3"
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

            {/* Timeline nodes — derived from ACTUAL candidate data */}
            {timelineDays.length > 0 && (
              <div className="flex items-end gap-1.5 flex-wrap">
                {timelineDays.map((day) => {
                  const done    = completedDays.includes(day);
                  const skipped = skippedDays.includes(day);
                  const failed  = failedDays.includes(day);

                  return (
                    <div key={day} title={`Day ${day}${done?" ✓":skipped?" (skipped)":failed?" ✗":""}`}>
                      <div
                        className="w-[28px] h-[28px] rounded-[7px] flex items-center justify-center text-[9px] font-bold font-mono transition-all duration-200"
                        style={
                          done    ? { background: `${palette.p}22`, color: palette.p,  border: `1.5px solid ${palette.p}50`, boxShadow: hovered ? `0 0 8px ${palette.p}40` : "none" } :
                          skipped ? { background: "rgba(251,191,36,0.1)",  color:"#fbbf24", border:"1.5px solid rgba(251,191,36,0.3)" } :
                          failed  ? { background: "rgba(251,113,133,0.1)", color:"#fb7185", border:"1.5px solid rgba(251,113,133,0.3)" } :
                                    { background: "rgba(255,255,255,0.04)", color:"#4b5563", border:"1.5px solid rgba(255,255,255,0.06)" }
                        }
                      >
                        {skipped ? <SkipForward className="w-2.5 h-2.5" /> : failed ? <AlertCircle className="w-2.5 h-2.5" /> : day}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
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
                    className="text-[10px] font-medium px-2 py-0.5 rounded-md"
                    style={{
                      background: `${palette.p}14`,
                      border: `1px solid ${palette.p}28`,
                      color: palette.p,
                    }}
                  >
                    {t}
                  </span>
                ))}
                {completedTopics.length > 3 && (
                  <span
                    className="text-[10px] font-medium px-2 py-0.5 rounded-md text-slate-500"
                    style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
                  >
                    +{completedTopics.length - 3}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Signal row */}
          {((candidate.missionsFirstTry ?? 0) > 0 || (candidate.failed ?? 0) > 0) && (
            <div className="flex items-center gap-3 pt-1 border-t" style={{ borderColor: "rgba(255,255,255,0.05)" }}>
              {(candidate.missionsFirstTry ?? 0) > 0 && (
                <div className="flex items-center gap-1 text-[10px] text-emerald-400">
                  <CheckCircle className="w-3 h-3" />
                  <span>{candidate.missionsFirstTry} first-try</span>
                </div>
              )}
              {(candidate.struggles ?? 0) > 0 && (
                <div className="text-[10px] text-amber-400">
                  ⟳ {candidate.struggles} struggled
                </div>
              )}
              {(candidate.failed ?? 0) > 0 && (
                <div className="flex items-center gap-1 text-[10px] text-rose-400">
                  <AlertCircle className="w-3 h-3" />
                  <span>{candidate.failed} failed</span>
                </div>
              )}
            </div>
          )}

          {/* ─── ACTIONS ────────────────────────────────────── */}
          <div className="flex items-center gap-2 pt-1">
            {/* Secondary: Dossier */}
            <button
              onClick={() => onViewDossier?.(candidate.id)}
              className="flex items-center gap-1.5 px-3 py-2.5 rounded-[10px] text-[12px] font-semibold transition-all duration-200"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.07)",
                color: "rgba(148,163,184,0.8)",
              }}
              onMouseEnter={e => {
                (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.08)";
                (e.currentTarget as HTMLElement).style.color = "#fff";
              }}
              onMouseLeave={e => {
                (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.04)";
                (e.currentTarget as HTMLElement).style.color = "rgba(148,163,184,0.8)";
              }}
            >
              <BookOpen className="w-3.5 h-3.5" />
              Dossier
            </button>

            {/* Primary: Start Interview */}
            <button
              onClick={(e) => { e.stopPropagation(); onStartInterview(candidate.id); }}
              className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-[10px] text-[13px] font-bold text-white transition-all duration-220 group/ibtn"
              style={{
                background: `linear-gradient(135deg, ${palette.bar})`,
                boxShadow: hovered
                  ? `0 8px 24px -6px ${palette.glow}, inset 0 1px 0 rgba(255,255,255,0.15)`
                  : `0 4px 12px -4px ${palette.glow}, inset 0 1px 0 rgba(255,255,255,0.10)`,
                border: "1px solid rgba(255,255,255,0.12)",
              }}
            >
              Start Interview
              <ArrowRight
                className="w-3.5 h-3.5 transition-transform duration-200 group-hover/ibtn:translate-x-1"
              />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
