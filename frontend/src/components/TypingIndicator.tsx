export function TypingIndicator() {
  return (
    <div className="flex items-start gap-4 animate-fade-in">
      <div className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-200 border border-white/10 shadow-lg shadow-black/20">
        <div className="w-full h-full rounded-full bg-gradient-to-br from-accent-600/20 to-accent-purple/20 flex items-center justify-center">
          <span className="font-bold text-accent-400 text-sm">A</span>
        </div>
      </div>
      
      <div className="flex flex-col gap-1 max-w-[85%]">
        <div className="flex items-center gap-2 pl-1 mb-0.5">
          <span className="text-xs font-semibold text-white">Alex</span>
          <span className="text-[10px] text-slate-500 font-medium">is thinking</span>
        </div>
        
        <div className="rounded-2xl rounded-tl-sm border border-white/5 bg-surface-100/80 px-5 py-4 shadow-lg backdrop-blur-sm w-fit">
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 animate-pulse-dot rounded-full bg-accent-400" style={{ animationDelay: "0ms" }} />
            <span className="h-2 w-2 animate-pulse-dot rounded-full bg-accent-400" style={{ animationDelay: "150ms" }} />
            <span className="h-2 w-2 animate-pulse-dot rounded-full bg-accent-400" style={{ animationDelay: "300ms" }} />
          </div>
        </div>
      </div>
    </div>
  );
}
