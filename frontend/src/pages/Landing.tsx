import { useState, useMemo } from "react";
import { useInterview } from "../context/InterviewContext";
import type { Page, CandidateSummary } from "../types";
import { ErrorBanner } from "../components/ErrorBanner";
import { Brand } from "../components/Brand";
import { CandidateCharacter } from "../components/CandidateCharacter";
import { CandidateDrawer } from "../components/CandidateDrawer";
import { Search, ChevronRight, UserCircle, Briefcase, BookOpen, Presentation } from "lucide-react";

interface LandingProps {
  onNavigate: (page: Page) => void;
}

export function Landing({ onNavigate }: LandingProps) {
  const { candidates, candidatesLoading, health, error, dismissError, startInterview } = useInterview();
  
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateSummary | null>(null);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"all" | "strong" | "developing">("all");
  const [hoveredCandidate, setHoveredCandidate] = useState<string | null>(null);

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

  return (
    <div className="relative min-h-screen bg-background selection:bg-accent-500/20">
      {/* Navbar */}
      <nav className="relative z-50 flex items-center justify-between px-8 py-6 w-full max-w-7xl mx-auto border-b border-surface-200">
        <Brand />
        <div className="hidden md:flex items-center gap-10 text-sm font-medium text-base-700">
          <a href="#how-it-works" className="hover:text-base-900 transition-colors">How it works</a>
          <a href="#candidates" className="hover:text-base-900 transition-colors">Candidates</a>
          <a href="#" className="hover:text-base-900 transition-colors">The Interview</a>
        </div>
        <a href="#candidates" className="px-5 py-2.5 rounded-full bg-base-900 text-white text-sm font-semibold hover:bg-base-800 transition-colors">
          Start an Interview
        </a>
      </nav>

      <main className="relative z-10 mx-auto max-w-7xl px-6 pb-32">
        {error && (
          <div className="mt-8">
            <ErrorBanner message={error} onDismiss={dismissError} />
          </div>
        )}
        
        {/* Editorial Hero */}
        <section className="pt-32 pb-24 flex flex-col lg:flex-row items-center justify-between gap-16">
          <div className="lg:w-1/2">
            <h1 className="font-serif text-6xl md:text-7xl font-black text-base-950 leading-[1.1] mb-8">
              Every candidate <br />
              <span className="text-base-600">has a different story.</span>
            </h1>
            <h2 className="text-2xl font-medium text-base-800 mb-6">
              The interviewer should know it.
            </h2>
            <p className="text-lg text-base-600 leading-relaxed mb-10 max-w-lg">
              AI Interview Agent turns a candidate's actual learning journey into a technical conversation — adapting questions, difficulty and follow-ups as the interview unfolds.
            </p>
            <div className="flex items-center gap-6">
              <a href="#candidates" className="inline-flex items-center gap-2 px-8 py-4 bg-accent-500 text-white rounded-xl font-bold hover:bg-accent-600 transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5">
                Meet the candidates <ChevronRight className="w-4 h-4" />
              </a>
              <a href="#how-it-works" className="font-semibold text-base-700 hover:text-base-900 transition-colors">
                How it works
              </a>
            </div>
          </div>
          
          <div className="lg:w-1/2 flex justify-center">
            {/* Hero Character Illustration */}
            <div className="w-[400px] h-[400px] relative editorial-card bg-surface-100 flex items-center justify-center p-8 overflow-hidden">
              <div className="absolute inset-0 bg-paper-texture opacity-50" />
              <CandidateCharacter name="Hero Example" role="AI Engineer" readiness={90} isHovered={true} />
            </div>
          </div>
        </section>

        {/* How It Works (Horizontal Story) */}
        <section id="how-it-works" className="py-24 border-t border-surface-200">
          <div className="grid md:grid-cols-4 gap-12">
            {[
              { num: "01", title: "Understand the journey", icon: BookOpen },
              { num: "02", title: "Meet the candidate", icon: UserCircle },
              { num: "03", title: "Have the conversation", icon: Presentation },
              { num: "04", title: "Read the report", icon: Briefcase },
            ].map((step, i) => (
              <div key={i} className="flex flex-col gap-4">
                <span className="font-serif text-5xl text-base-300 font-black">{step.num}</span>
                <step.icon className="w-8 h-8 text-accent-500" />
                <h3 className="font-serif text-xl font-bold text-base-900">{step.title}</h3>
              </div>
            ))}
          </div>
        </section>

        {/* Candidate Selection */}
        <section id="candidates" className="py-24 border-t border-surface-200">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-16">
            <div>
              <h2 className="font-serif text-4xl font-bold text-base-900 mb-3">Who's ready?</h2>
              <p className="text-base-600">Select a candidate to review their dossier and start an interview.</p>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-base-500" />
                <input 
                  type="text" 
                  placeholder="Search candidates..." 
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  className="w-full md:w-64 pl-12 pr-4 py-3 bg-white border border-surface-200 rounded-xl text-sm text-base-900 placeholder:text-base-400 focus:outline-none focus:border-accent-500 focus:ring-1 focus:ring-accent-500 transition-all editorial-shadow"
                />
              </div>
              <select 
                value={filter}
                onChange={e => setFilter(e.target.value as any)}
                className="bg-white border border-surface-200 rounded-xl px-5 py-3 text-sm text-base-700 focus:outline-none focus:border-accent-500 editorial-shadow appearance-none cursor-pointer"
              >
                <option value="all">All Profiles</option>
                <option value="strong">Interview Ready</option>
                <option value="developing">Needs Practice</option>
              </select>
            </div>
          </div>

          {candidatesLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-[400px] rounded-2xl bg-surface-100 animate-pulse border border-surface-200" />
              ))}
            </div>
          ) : filteredCandidates.length === 0 ? (
            <div className="text-center py-24 editorial-card">
              <p className="text-base-500">No candidates match your criteria.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {filteredCandidates.map(candidate => {
                const readiness = candidate.missionsCompleted ? Math.round((candidate.missionsCompleted / (health?.curriculumDays || 31)) * 100) : 0;
                const isHovered = hoveredCandidate === candidate.id;
                
                return (
                  <div 
                    key={candidate.id}
                    onMouseEnter={() => setHoveredCandidate(candidate.id)}
                    onMouseLeave={() => setHoveredCandidate(null)}
                    onClick={() => setSelectedCandidate(candidate)}
                    className="editorial-card p-6 flex flex-col cursor-pointer transition-all duration-300 hover:shadow-xl hover:-translate-y-1 bg-white relative overflow-hidden group"
                  >
                    {/* Character Area */}
                    <div className="h-48 w-full bg-surface-50 rounded-xl mb-6 relative border border-surface-200 flex items-center justify-center overflow-hidden">
                      <div className="absolute inset-0 bg-paper-texture opacity-30" />
                      <div className="w-40 h-40">
                        <CandidateCharacter 
                          name={candidate.name} 
                          role={candidate.role} 
                          readiness={readiness} 
                          isHovered={isHovered}
                        />
                      </div>
                    </div>

                    {/* Info Area */}
                    <div className="mb-6 flex-1">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h4 className="font-serif text-xl font-bold text-base-900 truncate">{candidate.name || candidate.id}</h4>
                          <p className="text-xs font-medium text-base-500 mt-1 uppercase tracking-wider">{candidate.role}</p>
                        </div>
                        <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-widest ${readiness >= 70 ? 'bg-mint-500/10 text-mint-500' : 'bg-amber-500/10 text-amber-500'}`}>
                          {readiness}% Ready
                        </span>
                      </div>
                      
                      {/* Skill Journey Mini */}
                      <div className="mt-5">
                        <div className="flex justify-between text-[10px] uppercase tracking-widest font-bold text-base-400 mb-2">
                          <span>Cohort Journey</span>
                          <span>{candidate.missionsCompleted || 0} / {health?.curriculumDays || 31}</span>
                        </div>
                        <div className="flex items-center gap-1 w-full h-2">
                          {[...Array(10)].map((_, i) => {
                            const isFilled = i < Math.floor((readiness / 100) * 10);
                            return (
                              <div key={i} className={`h-full flex-1 rounded-full ${isFilled ? (readiness >= 70 ? 'bg-accent-500' : 'bg-amber-400') : 'bg-surface-200'}`} />
                            )
                          })}
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-3 mt-auto">
                      <button 
                        onClick={(e) => { e.stopPropagation(); handleStart(candidate.id); }}
                        className="flex-1 py-3 bg-base-900 hover:bg-base-800 text-white rounded-xl text-sm font-semibold transition-colors flex items-center justify-center gap-2"
                      >
                        Interview {candidate.name.split(' ')[0]}
                      </button>
                      <button 
                        onClick={(e) => { e.stopPropagation(); setSelectedCandidate(candidate); }}
                        className="px-4 py-3 bg-surface-100 hover:bg-surface-200 text-base-700 rounded-xl text-sm font-medium transition-colors"
                      >
                        Dossier
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </main>

      <CandidateDrawer 
        candidate={selectedCandidate} 
        isOpen={selectedCandidate !== null} 
        onClose={() => setSelectedCandidate(null)}
        onStartInterview={(id) => handleStart(id)}
        curriculumDays={health?.curriculumDays || 31}
      />
    </div>
  );
}
