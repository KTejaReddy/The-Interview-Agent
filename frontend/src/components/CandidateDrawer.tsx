import { X } from "lucide-react";
import { useEffect } from "react";
import { createPortal } from "react-dom";
import { CandidateSummary } from "../types";
import { RealisticAvatar } from "./CandidateCharacter";

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

  if (!isOpen || !candidate) return null;

  const readiness = candidate.missionsCompleted ? Math.round((candidate.missionsCompleted / curriculumDays) * 100) : 0;
  
  // Dummy signal generation based on metrics for the editorial view
  const signals = [];
  if (readiness >= 80) signals.push("Interview Ready");
  else if (readiness >= 50) signals.push("Growing Fast");
  else signals.push("Needs Practice");
  
  if (candidate.missionsFirstTry && candidate.missionsFirstTry > 15) signals.push("Confident Builder");
  if (candidate.struggles && candidate.struggles > 5) signals.push("Shows Perseverance");

  const topics = candidate.completedTopics && candidate.completedTopics.length > 0
    ? candidate.completedTopics
    : [];

  const drawerContent = (
    <div className="fixed inset-0 z-[1000] flex justify-end" aria-modal="true" role="dialog" aria-labelledby="dossier-title">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-[#03060f]/75 backdrop-blur-md transition-opacity duration-300 animate-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />
      
      {/* Drawer Surface */}
      <div className="relative w-[92vw] sm:w-[450px] md:w-[500px] h-full bg-[#0d111c] border-l border-white/10 shadow-[-20px_0_60px_rgba(0,0,0,0.35)] flex flex-col overflow-y-auto animate-slide-in-right transform transition-transform duration-300">
        
        {/* Header Section */}
        <div className="relative p-8 pb-6 border-b border-white/5 shrink-0">
          <button 
            onClick={onClose}
            aria-label="Close dossier"
            className="absolute top-6 right-6 p-2 rounded-full bg-surface-100/10 hover:bg-accent-500/20 hover:text-accent-400 text-base-400 transition-colors z-10"
          >
            <X className="w-5 h-5" />
          </button>
          
          <div className="flex flex-col items-start pt-4">
            <div className="w-24 h-24 mb-6 rounded-2xl border border-white/10 overflow-hidden shadow-[0_0_20px_rgba(0,240,255,0.15)] bg-[#101522]">
              <RealisticAvatar name={candidate.name} id={candidate.id} />
            </div>
            
            <h2 id="dossier-title" className="font-sans text-3xl font-black text-[#F8FAFC] tracking-tight mb-1">
              {candidate.name || candidate.id}
            </h2>
            <p className="text-[#A8B2C5] font-bold text-xs tracking-widest uppercase mb-4">
              {candidate.role || "Candidate"}
            </p>
            
            <div className="flex flex-wrap gap-2">
              {signals.map((signal, idx) => (
                <span key={idx} className="px-2.5 py-1 bg-white/5 text-[#7F8BA3] text-[10px] font-bold uppercase tracking-widest rounded-md border border-white/10">
                  {signal}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 p-8 space-y-10">
          
          {/* Summary Section */}
          <section>
            <h3 className="text-[#7F8BA3] text-[10px] font-bold uppercase tracking-widest mb-4">Profile Summary</h3>
            <div className="grid grid-cols-3 gap-3">
              <div className="p-4 bg-[#101522] rounded-xl border border-white/5 flex flex-col justify-center items-center">
                <span className="text-[#71809A] text-[9px] uppercase tracking-widest font-bold mb-1">Missions</span>
                <span className="text-[#F8FAFC] text-xl font-black">{candidate.missionsCompleted || 0}</span>
              </div>
              <div className="p-4 bg-[#101522] rounded-xl border border-white/5 flex flex-col justify-center items-center">
                <span className="text-[#71809A] text-[9px] uppercase tracking-widest font-bold mb-1">Days</span>
                <span className="text-[#F8FAFC] text-xl font-black">{candidate.missionsCompleted || 0}<span className="text-[#71809A] text-sm font-medium">/{curriculumDays}</span></span>
              </div>
              <div className="p-4 bg-[#101522] rounded-xl border border-white/5 flex flex-col justify-center items-center relative overflow-hidden">
                <div className="absolute inset-0 bg-accent-500/5" />
                <span className="text-accent-400 text-[9px] uppercase tracking-widest font-bold mb-1 relative z-10">Readiness</span>
                <span className="text-[#F8FAFC] text-xl font-black relative z-10">{readiness}%</span>
              </div>
            </div>
          </section>

          {/* Journey Section */}
          <section>
            <h3 className="text-[#7F8BA3] text-[10px] font-bold uppercase tracking-widest mb-4 flex justify-between items-center">
              <span>Cohort Journey</span>
              <span className="text-[#71809A]">{candidate.missionsCompleted || 0} / {curriculumDays}</span>
            </h3>
            <div className="relative pt-2">
              <div className="absolute top-4 left-0 w-full h-px bg-white/10" />
              <div className="flex justify-between relative z-10">
                {[1, 7, 12, 16, 22, 31].map((day, idx) => {
                  const isPassed = (candidate.missionsCompleted || 0) >= day;
                  const isCurrent = (candidate.missionsCompleted || 0) + 1 === day || (candidate.missionsCompleted || 0) === day;
                  return (
                    <div key={idx} className="flex flex-col items-center gap-2 bg-[#0d111c] px-2">
                      <div className={`w-4 h-4 rounded-full border-[3px] ${isPassed ? 'bg-accent-500 border-accent-500 shadow-[0_0_10px_rgba(0,240,255,0.4)]' : isCurrent ? 'bg-[#0d111c] border-accent-400' : 'bg-[#0d111c] border-white/20'}`} />
                      <span className={`text-[9px] font-bold ${isPassed || isCurrent ? 'text-[#F8FAFC]' : 'text-[#71809A]'}`}>D{day.toString().padStart(2, '0')}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </section>

          {/* Topics Section */}
          <section>
            <h3 className="text-[#7F8BA3] text-[10px] font-bold uppercase tracking-widest mb-4">Interviewable Topics</h3>
            {topics.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {topics.map(t => (
                  <span key={t} className="px-3 py-1.5 bg-accent-500/10 text-accent-400 text-xs font-semibold rounded-lg border border-accent-500/20">
                    {t}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-[#71809A] text-sm">No topics completed yet.</p>
            )}
          </section>
        </div>

        {/* Sticky Footer CTA */}
        <div className="sticky bottom-0 p-6 bg-[#0d111c]/95 backdrop-blur-md border-t border-white/5 shrink-0">
          <div className="mb-4">
            <h3 className="text-[#F8FAFC] text-sm font-bold mb-1">Interview Assessment</h3>
            <p className="text-[#71809A] text-xs">Ready to evaluate this candidate's technical skills?</p>
          </div>
          <button 
            onClick={() => onStartInterview(candidate.id)}
            className="group w-full py-4 bg-premium-gradient text-white rounded-xl font-bold shadow-glow-accent hover:-translate-y-0.5 hover:shadow-[0_0_30px_-5px_rgba(0,240,255,0.5)] transition-all flex items-center justify-center gap-3"
          >
            Start Interview
            <span className="font-serif group-hover:translate-x-1 transition-transform">→</span>
          </button>
        </div>
        
      </div>
    </div>
  );

  return createPortal(drawerContent, document.body);
}
