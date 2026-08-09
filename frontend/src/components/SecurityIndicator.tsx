import { Shield } from "lucide-react";

export function SecurityIndicator() {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 backdrop-blur-md transition-all duration-300 group">
      <Shield className="w-3.5 h-3.5 text-emerald-400" />
      <span className="text-[11px] font-medium text-emerald-400/90 tracking-wide">
        Assessment mode
      </span>
      
      {/* Tooltip on hover */}
      <div className="absolute top-full mt-2 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-50">
        <div className="bg-surface-800/95 backdrop-blur-xl border border-white/10 px-3 py-2 rounded-lg whitespace-nowrap shadow-2xl">
          <p className="text-xs text-slate-300 text-center">Interview integrity protection is active.</p>
        </div>
      </div>
    </div>
  );
}
