import { useState, useMemo } from "react";
import { useInterview } from "../context/InterviewContext";
import type { Page } from "../types";
import { ErrorBanner } from "../components/ErrorBanner";
import { Navigation } from "../components/Navigation";
import { RealisticAvatar } from "../components/CandidateCharacter";
import { Search, ArrowRight, CheckCircle2, Users, CalendarDays, MessageSquare, Zap, SlidersHorizontal, LayoutGrid, List } from "lucide-react";

interface LandingProps {
  onNavigate: (page: Page) => void;
}

export function Landing({ onNavigate }: LandingProps) {
  const { candidates, candidatesLoading, health, error, dismissError, startInterview } = useInterview();
  
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"all" | "strong" | "developing">("all");

  const filteredCandidates = useMemo(() => {
    return candidates.filter(c => {
      if (search && !c.name.toLowerCase().includes(search.toLowerCase()) && !c.role.toLowerCase().includes(search.toLowerCase())) {
        return false;
      }
      const readiness = c.missionsCompleted ? (c.missionsCompleted / (health?.curriculumDays || 31)) * 100 : 0;
      if (filter === "strong" && readiness < 70) return false;
      if (filter === "developing" && readiness >= 70) return false;
      return true;
    });
  }, [candidates, search, filter, health]);

  const handleStart = async (candidateId: string) => {
    await startInterview(candidateId, "Hi! I'm ready to start.");
    onNavigate("interview");
  };

  const curriculumDaysTotal = health?.curriculumDays || 31;

  return (
    <div className="relative min-h-screen bg-background selection:bg-accent-500/30 overflow-x-hidden text-gray-200">
      
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCI+PHBhdGggZD0iTTAgMGg0MHY0MEgwem0yMCAyMGMxLjEgMCAyLS45IDItMmMwLTEuMS0uOS0yLTItMnMtMiAuOS0yIDJjMCAxLjEuOSAyIDIgMnoiIGZpbGw9IiNmZmZmZmYiIGZpbGwtb3BhY2l0eT0iMC4wMiIgZmlsbC1ydWxlPSJldmVub2RkIi8+PC9zdmc+')] opacity-[0.15]" />
      <div className="bg-orb-1 top-[-10%] left-[-10%] w-[1000px] h-[1000px] mix-blend-screen" />
      <div className="bg-orb-2 bottom-[10%] right-[-10%] w-[800px] h-[800px] mix-blend-screen" />

      <Navigation />

      <main className="relative z-10 mx-auto max-w-[1440px] px-6 py-12">
        {error && (
          <div className="mb-6">
            <ErrorBanner message={error} onDismiss={dismissError} />
          </div>
        )}
        
        {/* Split Hero Section */}
        <section className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-12 mb-16">
          <div className="max-w-2xl">
            <h1 className="text-4xl md:text-[54px] font-bold text-white leading-[1.1] tracking-tight mb-4">
              Find the right candidate.<br />
              <span className="font-serif italic text-base-300">The interview already knows their journey.</span>
            </h1>
            <p className="text-sm md:text-[15px] text-base-400 leading-relaxed max-w-xl">
              Pick a journey — the interview adapts to what they actually built across the ABTalks AI Engineering Cohort.
            </p>
          </div>
          
          <div className="flex flex-wrap lg:flex-nowrap items-center gap-4">
            <MetricCard icon={<Users className="w-5 h-5 text-accent-400" />} value="20" label="Candidate Profiles" />
            <MetricCard icon={<CalendarDays className="w-5 h-5 text-accent-purple" />} value="31" label="Curriculum Days" />
            <MetricCard icon={<MessageSquare className="w-5 h-5 text-accent-cyan" />} value="8–14" label="Questions / Interview" />
            <MetricCard icon={<Zap className="w-5 h-5 text-amber-400" />} value="<1s" label="First Response" />
          </div>
        </section>

        {/* Toolbar */}
        <section className="flex flex-col md:flex-row items-center justify-between gap-4 mb-8 bg-surface-50/50 backdrop-blur-md border border-white/5 rounded-2xl p-2 pl-4">
          <div className="flex items-center gap-1 w-full md:w-auto overflow-x-auto no-scrollbar">
            <button onClick={() => setFilter("all")} className={`px-4 py-2 rounded-xl text-[13px] font-medium whitespace-nowrap transition-colors ${filter === "all" ? "bg-accent-600 text-white" : "text-base-400 hover:text-white hover:bg-surface-100"}`}>All</button>
            <button onClick={() => setFilter("strong")} className={`px-4 py-2 rounded-xl text-[13px] font-medium whitespace-nowrap transition-colors ${filter === "strong" ? "bg-accent-600 text-white" : "text-base-400 hover:text-white hover:bg-surface-100"}`}>Interview Ready</button>
            <button className="px-4 py-2 rounded-xl text-[13px] font-medium whitespace-nowrap text-base-400 hover:text-white hover:bg-surface-100">Most Complete</button>
            <button onClick={() => setFilter("developing")} className={`px-4 py-2 rounded-xl text-[13px] font-medium whitespace-nowrap transition-colors ${filter === "developing" ? "bg-accent-600 text-white" : "text-base-400 hover:text-white hover:bg-surface-100"}`}>Needs Practice</button>
          </div>
          
          <div className="flex items-center gap-4 ml-auto w-full md:w-auto">
            <div className="flex items-center gap-2 text-[13px] text-base-400 font-medium px-4 py-2 border-r border-white/10">
              <SlidersHorizontal className="w-4 h-4" />
              <span>Sort: Readiness</span>
            </div>
            <div className="relative w-full md:w-48 mr-2">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-base-500" />
              <input 
                type="text" 
                placeholder="Search candidates..." 
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-surface-100/50 border border-transparent rounded-lg text-[13px] text-white placeholder:text-base-500 focus:outline-none focus:border-accent-500 focus:bg-surface-200 transition-colors"
              />
            </div>
            <div className="hidden md:flex items-center gap-1 bg-surface-100 p-1 rounded-lg">
              <button className="p-1.5 bg-surface-300 rounded text-white shadow-sm"><LayoutGrid className="w-4 h-4" /></button>
              <button className="p-1.5 text-base-400 hover:text-white transition-colors"><List className="w-4 h-4" /></button>
            </div>
          </div>
        </section>

        {/* Grid */}
        <section id="candidates">
          {candidatesLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
              {[...Array(12)].map((_, i) => (
                <div key={i} className="h-72 rounded-2xl bg-surface-50 animate-pulse border border-white/5" />
              ))}
            </div>
          ) : filteredCandidates.length === 0 ? (
            <div className="text-center py-24 glass-card rounded-2xl">
              <p className="text-base-400 text-[15px]">No candidates match your search criteria.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
              {filteredCandidates.map(candidate => {
                const readiness = candidate.missionsCompleted ? Math.round((candidate.missionsCompleted / curriculumDaysTotal) * 100) : 0;
                const topics = [1, 7, 12, 16, 22, 27, 31].filter(d => d <= (candidate.missionsCompleted || 0) + 5);
                
                return (
                  <div 
                    key={candidate.id}
                    className="group bg-[rgba(20,24,35,0.7)] backdrop-blur-xl border border-white/5 rounded-[20px] p-5 flex flex-col transition-all duration-300 hover:bg-[rgba(25,30,42,0.8)] hover:border-white/10 hover:shadow-xl hover:shadow-accent-500/5 hover:-translate-y-1 relative overflow-hidden"
                  >
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-accent-600 to-accent-purple opacity-0 group-hover:opacity-100 transition-opacity" />
                    
                    {/* Header */}
                    <div className="flex items-start justify-between mb-5">
                      <div className="flex items-center gap-4">
                        <div className="w-[60px] h-[60px] shrink-0 border border-white/10 rounded-[14px] bg-surface-100 shadow-inner">
                          <RealisticAvatar name={candidate.name} id={candidate.id} />
                        </div>
                        <div className="min-w-0 flex flex-col justify-center">
                          <div className="flex items-center gap-1.5 mb-0.5">
                            <h4 className="text-[15px] font-bold text-white truncate w-32">
                              {candidate.name || candidate.id}
                            </h4>
                            <CheckCircle2 className="w-3.5 h-3.5 text-accent-cyan shrink-0" />
                          </div>
                          <p className="text-[10px] font-semibold text-base-400 uppercase tracking-widest truncate w-32">
                            {candidate.role}
                          </p>
                        </div>
                      </div>
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold flex shrink-0 border ${
                        readiness >= 80 ? 'bg-mint-500/10 text-mint-400 border-mint-500/20 shadow-[0_0_10px_rgba(52,211,153,0.1)]' : 
                        readiness >= 50 ? 'bg-amber-500/10 text-amber-400 border-amber-500/20 shadow-[0_0_10px_rgba(245,158,11,0.1)]' : 
                        'bg-red-500/10 text-red-400 border-red-500/20'
                      }`}>
                        {readiness}% READY
                      </span>
                    </div>

                    {/* Stats */}
                    <div className="grid grid-cols-3 gap-2 mb-5">
                      <div className="flex flex-col gap-1">
                        <span className="text-[9px] font-bold text-base-500 uppercase tracking-widest">Missions</span>
                        <span className="text-[17px] font-bold text-white">{candidate.missionsCompleted || 0}</span>
                      </div>
                      <div className="flex flex-col gap-1">
                        <span className="text-[9px] font-bold text-base-500 uppercase tracking-widest">Days</span>
                        <span className="text-[17px] font-bold text-white">{candidate.missionsCompleted || 0}<span className="text-[11px] text-base-500 font-semibold">/{curriculumDaysTotal}</span></span>
                      </div>
                      <div className="flex flex-col gap-1">
                        <span className="text-[9px] font-bold text-base-500 uppercase tracking-widest">Readiness</span>
                        <span className={`text-[17px] font-bold ${readiness >= 80 ? 'text-mint-400' : readiness >= 50 ? 'text-amber-400' : 'text-red-400'}`}>{readiness}%</span>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="mb-5">
                      <div className="flex items-center justify-between text-[9px] font-bold text-base-400 uppercase tracking-widest mb-2">
                        <span>Cohort Progress</span>
                        <span>{candidate.missionsCompleted || 0} / {curriculumDaysTotal}</span>
                      </div>
                      <div className="h-1.5 w-full bg-surface-200 rounded-full overflow-hidden flex">
                        <div 
                          className={`h-full rounded-full transition-all duration-1000 ${readiness >= 80 ? 'bg-mint-500' : readiness >= 50 ? 'bg-amber-400' : 'bg-red-400'}`}
                          style={{ width: `${readiness}%` }}
                        />
                      </div>
                    </div>

                    {/* Chips */}
                    <div className="mb-6 flex flex-wrap gap-1.5">
                      {topics.slice(0, 5).map(day => (
                        <span key={day} className={`text-[9px] px-2 py-0.5 rounded-md font-mono font-bold border ${
                          day <= (candidate.missionsCompleted || 0) 
                            ? 'bg-mint-500/10 text-mint-400 border-mint-500/20'
                            : 'bg-surface-100 text-base-500 border-white/5'
                        }`}>
                          D{day.toString().padStart(2, '0')}
                        </span>
                      ))}
                    </div>

                    {/* CTA */}
                    <div className="mt-auto flex items-center justify-between border-t border-white/5 pt-4">
                      <span className="text-[10px] font-medium text-base-500 flex items-center gap-1.5">
                        <MessageSquare className="w-3.5 h-3.5" />
                        {topics.length} topics
                      </span>
                      <button 
                        onClick={(e) => { e.stopPropagation(); handleStart(candidate.id); }}
                        className="px-4 py-2 bg-accent-600 hover:bg-accent-500 text-white rounded-lg text-[13px] font-bold transition-all flex items-center gap-2 shadow-[0_0_15px_rgba(79,70,229,0.2)] hover:shadow-[0_0_20px_rgba(79,70,229,0.4)] group/btn"
                      >
                        Start Interview <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover/btn:translate-x-0.5" />
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

function MetricCard({ icon, value, label }: { icon: React.ReactNode, value: string, label: string }) {
  return (
    <div className="bg-surface-50/60 backdrop-blur-md border border-white/5 rounded-2xl p-4 flex flex-col justify-center min-w-[130px]">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-8 h-8 rounded-lg bg-surface-100 flex items-center justify-center border border-white/5">
          {icon}
        </div>
        <span className="text-2xl font-bold text-white leading-none">{value}</span>
      </div>
      <span className="text-[10px] font-medium text-base-400 uppercase tracking-widest">{label}</span>
    </div>
  );
}
