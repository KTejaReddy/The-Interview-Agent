import { useState, useMemo } from "react";
import { useInterview } from "../context/InterviewContext";
import type { Page } from "../types";
import { ErrorBanner } from "../components/ErrorBanner";
import { 
  Bot, 
  Search, 
  ChevronRight, 
  BrainCircuit, 
  MessageSquare, 
  LineChart, 
  Activity, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle 
} from "lucide-react";

interface LandingProps {
  onNavigate: (page: Page) => void;
}

const FEATURES = [
  {
    title: "Real conversations",
    text: "Every answer shapes the next question — deeper, simpler, or a recovery prompt — just like a real interviewer.",
    icon: <MessageSquare className="h-6 w-6 text-accent-cyan" />,
  },
  {
    title: "Curriculum-grounded",
    text: "Questions come only from your curriculum.json: objectives, tools, learning goals and topics — never hallucinated.",
    icon: <BrainCircuit className="h-6 w-6 text-accent-purple" />,
  },
  {
    title: "Adaptive difficulty",
    text: "The interviewer calibrates easy → medium → advanced from the candidate's profile inside candidate.json.",
    icon: <Activity className="h-6 w-6 text-mint-400" />,
  },
  {
    title: "Structured feedback",
    text: "When it's done you get summary, strengths, gaps and next steps — exactly the fields in technical-spec.md.",
    icon: <LineChart className="h-6 w-6 text-amber-400" />,
  },
];

export function Landing({ onNavigate }: LandingProps) {
  const { candidates, candidatesLoading, health, error, dismissError, startInterview, loading } = useInterview();
  
  const [selected, setSelected] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"all" | "strong" | "developing">("all");

  const filteredCandidates = useMemo(() => {
    return candidates.filter(c => {
      if (search && !c.name.toLowerCase().includes(search.toLowerCase()) && !c.role.toLowerCase().includes(search.toLowerCase())) {
        return false;
      }
      const readiness = c.missionsCompleted ? (c.missionsCompleted / 31) * 100 : 0;
      if (filter === "strong" && readiness < 70) return false;
      if (filter === "developing" && readiness >= 70) return false;
      return true;
    });
  }, [candidates, search, filter]);

  const handleStart = async () => {
    if (!selected) return;
    await startInterview(selected, "Hi! I'm ready to start.");
    onNavigate("interview");
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      {/* Premium Atmospheric Gradients */}
      <div className="bg-orb-1 top-[-20%] left-[-10%] w-[800px] h-[800px]" />
      <div className="bg-orb-2 bottom-[-20%] right-[-10%] w-[900px] h-[900px]" />
      <div className="bg-orb-3 top-[30%] left-[40%] w-[600px] h-[600px]" />
      
      {/* Navbar */}
      <nav className="relative z-50 flex items-center justify-between px-8 py-6 w-full max-w-7xl mx-auto backdrop-blur-sm border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-premium-gradient flex items-center justify-center shadow-lg shadow-accent-600/20">
            <Bot className="h-5 w-5 text-white" />
          </div>
          <span className="text-xl font-bold tracking-tight text-white">Interview Agent</span>
        </div>
        
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
          <a href="#how-it-works" className="hover:text-white transition-colors">How it works</a>
          <a href="#candidates" className="hover:text-white transition-colors">Candidates</a>
        </div>
        
        <div className="flex items-center gap-4">
          {health && (
            <div className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium border backdrop-blur-md ${
              health.status === "ok" ? "border-mint-500/20 bg-mint-500/10 text-mint-400" : "border-amber-500/20 bg-amber-500/10 text-amber-400"
            }`}>
              <span className={`h-2 w-2 rounded-full ${health.status === "ok" ? "bg-mint-400 animate-pulse-dot" : "bg-amber-400"}`} />
              {health.status === "ok" ? "System Online" : "Degraded"}
            </div>
          )}
        </div>
      </nav>

      <main className="relative z-10 mx-auto max-w-7xl px-6 pb-32">
        {error && (
          <div className="mt-8 animate-fade-in">
            <ErrorBanner message={error} onDismiss={dismissError} />
          </div>
        )}
        
        {/* Hero Section */}
        <section className="pt-32 pb-24 text-center flex flex-col items-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-surface-100/50 px-4 py-1.5 text-xs font-semibold tracking-widest text-slate-300 uppercase mb-8 animate-fade-up backdrop-blur-md shadow-xl">
            <span className="h-1.5 w-1.5 rounded-full bg-accent-cyan animate-pulse" />
            AI Cohort • Technical Assessment
          </div>
          
          <h1 className="max-w-4xl text-6xl md:text-7xl font-extrabold tracking-tight text-white leading-[1.1] animate-fade-up" style={{ animationDelay: '100ms' }}>
            The interview that <br />
            <span className="text-gradient premium-glow">already understands</span> your journey.
          </h1>
          
          <p className="mt-8 max-w-2xl text-lg text-slate-400 leading-relaxed animate-fade-up" style={{ animationDelay: '200ms' }}>
            Meet Alex — an AI interviewer who asks about the missions each candidate actually completed, probes the topics they struggled with, and closes with a structured, score-backed report.
          </p>

          <div className="mt-12 flex flex-col sm:flex-row items-center gap-6 animate-fade-up" style={{ animationDelay: '300ms' }}>
            <a href="#candidates" className="group relative inline-flex items-center justify-center gap-2 rounded-xl bg-white px-8 py-4 text-sm font-semibold text-background transition-all hover:scale-[1.02] active:scale-[0.98]">
              Start an Interview
              <ChevronRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
            </a>
            <a href="#how-it-works" className="text-sm font-semibold text-slate-300 hover:text-white transition-colors">
              See how it works →
            </a>
          </div>

          {/* Premium Stats Bar */}
          <div className="mt-24 grid grid-cols-2 md:grid-cols-4 gap-4 w-full max-w-4xl animate-fade-up" style={{ animationDelay: '400ms' }}>
            {[
              { label: "Candidate Profiles", value: health?.candidates || 20 },
              { label: "Curriculum Days", value: health?.curriculumDays || 31 },
              { label: "Questions per Interview", value: "8-12" },
              { label: "Latency Target", value: "<1s" },
            ].map((stat, i) => (
              <div key={i} className="glass-card rounded-2xl p-6 text-center border-white/5">
                <div className="text-3xl font-bold text-white mb-1">{stat.value}</div>
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{stat.label}</div>
              </div>
            ))}
          </div>
        </section>

        {/* How It Works */}
        <section id="how-it-works" className="py-24">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-white mb-4">How it works</h2>
            <p className="text-slate-400">Three steps from profile to verdict — running at Groq speed.</p>
          </div>
          
          <div className="grid md:grid-cols-4 gap-6">
            {FEATURES.map((feature, i) => (
              <div key={i} className="glass-card glass-card-hover rounded-2xl p-8 relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-6 text-8xl font-black text-white/[0.02] group-hover:text-white/[0.04] transition-colors pointer-events-none select-none">
                  0{i + 1}
                </div>
                <div className="w-12 h-12 rounded-xl bg-surface-200/50 border border-white/5 flex items-center justify-center mb-6 shadow-inner">
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold text-white mb-3">{feature.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{feature.text}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Candidate Selection */}
        <section id="candidates" className="py-24">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
            <div>
              <h2 className="text-3xl font-bold text-white mb-3">Select a Candidate Profile</h2>
              <p className="text-slate-400">Pick a journey — the interview adapts to what they actually built.</p>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <input 
                  type="text" 
                  placeholder="Search candidates..." 
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  className="w-full md:w-64 pl-10 pr-4 py-2.5 bg-surface-100/50 border border-white/10 rounded-xl text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-accent-500/50 focus:ring-1 focus:ring-accent-500/50 transition-all backdrop-blur-md"
                />
              </div>
              <select 
                value={filter}
                onChange={e => setFilter(e.target.value as any)}
                className="bg-surface-100/50 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-slate-300 focus:outline-none focus:border-accent-500/50 backdrop-blur-md appearance-none"
              >
                <option value="all">All Profiles</option>
                <option value="strong">Strong Progress</option>
                <option value="developing">Developing</option>
              </select>
            </div>
          </div>

          {candidatesLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="h-[280px] rounded-2xl bg-surface-100/50 border border-white/5 animate-pulse" />
              ))}
            </div>
          ) : filteredCandidates.length === 0 ? (
            <div className="text-center py-24 glass-card rounded-3xl border-dashed border-white/10">
              <p className="text-slate-400">No candidates match your criteria.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {filteredCandidates.map(candidate => {
                const isActive = selected === candidate.id;
                const readiness = candidate.missionsCompleted ? Math.round((candidate.missionsCompleted / (health?.curriculumDays || 31)) * 100) : 0;
                
                return (
                  <div 
                    key={candidate.id}
                    onClick={() => setSelected(candidate.id)}
                    className={`glass-card rounded-2xl p-5 flex flex-col cursor-pointer transition-all duration-300 border-2 ${isActive ? 'border-accent-500 bg-surface-200/80 shadow-lg shadow-accent-500/20 scale-[1.02] -translate-y-1' : 'border-white/5 hover:border-white/20 hover:bg-surface-100/80 hover:-translate-y-1'}`}
                  >
                    {/* Header */}
                    <div className="flex items-start justify-between mb-5">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-surface-300 to-surface-100 flex items-center justify-center border border-white/10 shadow-inner flex-shrink-0">
                          <span className="font-bold text-white text-sm">{candidate.name.charAt(0) || "U"}</span>
                        </div>
                        <div className="min-w-0">
                          <h4 className="font-bold text-white text-sm truncate" title={candidate.name}>{candidate.name || candidate.id}</h4>
                          <p className="text-xs text-slate-400 truncate" title={candidate.role}>{candidate.role || "Candidate"}</p>
                        </div>
                      </div>
                      <div className={`flex flex-shrink-0 items-center gap-1 px-2 py-1 rounded-md text-[10px] font-bold ${readiness >= 70 ? 'bg-mint-500/10 text-mint-400 border border-mint-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'}`}>
                        {readiness}% READY
                      </div>
                    </div>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 gap-2 mb-4">
                      <div className="bg-surface-50/50 rounded-lg p-2.5 border border-white/5">
                        <div className="text-[10px] font-semibold text-slate-500 uppercase mb-1">Missions</div>
                        <div className="text-sm font-bold text-white flex items-baseline gap-1">
                          {candidate.missionsCompleted || 0} <span className="text-[10px] text-slate-500 font-normal">/ {health?.curriculumDays || 31}</span>
                        </div>
                      </div>
                      <div className="bg-surface-50/50 rounded-lg p-2.5 border border-white/5">
                        <div className="text-[10px] font-semibold text-slate-500 uppercase mb-1">Experience</div>
                        <div className="text-sm font-bold text-white">
                          {candidate.experience ? `${candidate.experience}y` : '—'}
                        </div>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="mb-5">
                      <div className="flex justify-between text-[10px] font-semibold text-slate-400 mb-1.5">
                        <span>Cohort Progress</span>
                        <span>{readiness}%</span>
                      </div>
                      <div className="h-1.5 w-full bg-surface-300 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full transition-all duration-1000 ${readiness >= 70 ? 'bg-mint-400' : 'bg-amber-400'}`}
                          style={{ width: `${readiness}%` }}
                        />
                      </div>
                    </div>

                    {/* Mission Signals */}
                    <div className="flex flex-wrap gap-1.5 mb-5 flex-grow">
                      {candidate.missionsFirstTry != null && candidate.missionsFirstTry > 0 && (
                        <span className="inline-flex items-center gap-1 rounded bg-mint-500/10 px-1.5 py-0.5 text-[9px] font-medium text-mint-400 border border-mint-500/20">
                          <CheckCircle2 className="w-3 h-3" /> {candidate.missionsFirstTry} 1st try
                        </span>
                      )}
                      {candidate.struggles != null && candidate.struggles > 0 && (
                        <span className="inline-flex items-center gap-1 rounded bg-amber-500/10 px-1.5 py-0.5 text-[9px] font-medium text-amber-400 border border-amber-500/20">
                          <AlertTriangle className="w-3 h-3" /> {candidate.struggles} struggled
                        </span>
                      )}
                      {candidate.failed != null && candidate.failed > 0 && (
                        <span className="inline-flex items-center gap-1 rounded bg-red-500/10 px-1.5 py-0.5 text-[9px] font-medium text-red-400 border border-red-500/20">
                          <XCircle className="w-3 h-3" /> {candidate.failed} failed
                        </span>
                      )}
                    </div>

                    {/* Start CTA */}
                    <div className="mt-auto">
                      <button 
                        onClick={(e) => { e.stopPropagation(); setSelected(candidate.id); handleStart(); }}
                        className={`w-full py-2.5 rounded-xl text-sm font-semibold transition-all flex items-center justify-center gap-2 ${isActive ? 'bg-accent-600 hover:bg-accent-500 text-white shadow-md' : 'bg-surface-200 text-slate-300 hover:bg-surface-300 hover:text-white border border-white/5'}`}
                      >
                        {isActive && loading ? (
                          <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2.5" opacity="0.25" /><path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" /></svg>
                        ) : (
                          'Start Interview'
                        )}
                        {!loading && <ChevronRight className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
