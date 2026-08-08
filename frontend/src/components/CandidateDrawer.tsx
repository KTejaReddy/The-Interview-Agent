import { X } from "lucide-react";
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
  if (!isOpen || !candidate) return null;

  const readiness = candidate.missionsCompleted ? Math.round((candidate.missionsCompleted / curriculumDays) * 100) : 0;
  
  // Dummy signal generation based on metrics for the editorial view
  const signals = [];
  if (readiness >= 80) signals.push("Interview Ready");
  else if (readiness >= 50) signals.push("Growing Fast");
  else signals.push("Needs Practice");
  
  if (candidate.missionsFirstTry && candidate.missionsFirstTry > 15) signals.push("Confident Builder");
  if (candidate.struggles && candidate.struggles > 5) signals.push("Shows Perseverance");

  // Derive mock topics from ID for visual flavor, as requested in prompt
  const topics = ["RAG", "Embeddings", "Agents", "MCP"];

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-base-950/20 backdrop-blur-sm z-50 transition-opacity animate-fade-in"
        onClick={onClose}
      />
      
      {/* Drawer */}
      <div className="fixed top-0 right-0 h-full w-full max-w-md bg-surface-50 border-l border-surface-200 shadow-2xl z-50 overflow-y-auto animate-slide-in-right">
        <div className="p-6">
          <button 
            onClick={onClose}
            className="absolute top-6 right-6 p-2 rounded-full hover:bg-surface-100 text-base-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="flex flex-col items-center text-center mt-8 mb-10">
            <div className="w-48 h-48 mb-6">
              <RealisticAvatar name={candidate.name} id={candidate.id} />
            </div>
            
            <h2 className="font-serif text-3xl font-bold text-base-900 mb-2">{candidate.name || candidate.id}</h2>
            <p className="text-base-600 font-medium mb-4">{candidate.role || "Candidate"}</p>
            
            <div className="flex flex-wrap justify-center gap-2">
              {signals.map((signal, idx) => (
                <span key={idx} className="px-3 py-1 bg-surface-100 text-base-700 text-xs font-semibold rounded-full border border-surface-200">
                  {signal}
                </span>
              ))}
            </div>
          </div>

          <div className="space-y-8">
            {/* Progress Section */}
            <section>
              <h3 className="font-serif text-lg font-semibold text-base-900 mb-4 border-b border-surface-200 pb-2">Cohort Progress</h3>
              
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="p-4 bg-surface-100 rounded-xl border border-surface-200">
                  <p className="text-[10px] uppercase tracking-widest font-bold text-base-600 mb-1">Missions</p>
                  <p className="text-2xl font-serif text-base-900">{candidate.missionsCompleted || 0} <span className="text-sm text-base-600 font-sans">/ {curriculumDays}</span></p>
                </div>
                <div className="p-4 bg-surface-100 rounded-xl border border-surface-200">
                  <p className="text-[10px] uppercase tracking-widest font-bold text-base-600 mb-1">Readiness</p>
                  <p className="text-2xl font-serif text-base-900">{readiness}%</p>
                </div>
              </div>

              {/* Journey Visualization */}
              <div className="mt-6">
                <p className="text-[10px] uppercase tracking-widest font-bold text-base-600 mb-3">Skill Journey</p>
                <div className="flex items-center justify-between relative">
                  <div className="absolute top-1/2 -translate-y-1/2 left-0 w-full h-0.5 bg-surface-200" />
                  {[1, 7, 12, 16, 22, 31].map((day, idx) => {
                    const isPassed = (candidate.missionsCompleted || 0) >= day;
                    return (
                      <div key={idx} className="relative z-10 flex flex-col items-center gap-2 bg-surface-50 px-1">
                        <div className={`w-3 h-3 rounded-full border-2 ${isPassed ? 'bg-accent-500 border-accent-500' : 'bg-surface-50 border-surface-300'}`} />
                        <span className="text-[9px] font-bold text-base-600">D{day.toString().padStart(2, '0')}</span>
                      </div>
                    )
                  })}
                </div>
              </div>
            </section>

            {/* Topics Section */}
            <section>
              <h3 className="font-serif text-lg font-semibold text-base-900 mb-4 border-b border-surface-200 pb-2">Interviewable Topics</h3>
              <div className="flex flex-wrap gap-2">
                {topics.map(t => (
                  <span key={t} className="px-3 py-1.5 bg-accent-500/10 text-accent-600 text-xs font-semibold rounded-lg">
                    {t}
                  </span>
                ))}
              </div>
            </section>
          </div>
        </div>

        {/* Sticky Footer */}
        <div className="sticky bottom-0 p-6 bg-surface-50/90 backdrop-blur border-t border-surface-200">
          <button 
            onClick={() => onStartInterview(candidate.id)}
            className="w-full py-4 bg-base-900 text-white rounded-xl font-semibold shadow-lg hover:bg-base-800 transition-colors flex items-center justify-center gap-2"
          >
            Start Interview
            <span className="font-serif">→</span>
          </button>
        </div>
      </div>
    </>
  );
}
