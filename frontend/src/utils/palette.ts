/** Shared deterministic palette system for candidate identity colors. */

export interface CandidatePalette {
  p: string;   // primary
  s: string;   // secondary
  env: string; // environment gradient stops
  glow: string;
  bar: string; // progress gradient
  ring: string;
}

const PALETTES: CandidatePalette[] = [
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

export function getPalette(id: string, role: string): CandidatePalette {
  const r = (role || "").toLowerCase();
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
  const n = id.split("").reduce((a, c) => a + c.charCodeAt(0), 0);
  return PALETTES[n % PALETTES.length];
}
