export function TypingIndicator() {
  return (
    <div className="flex items-start gap-3 animate-fade-in">
      <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-accent-500 to-mint-500 shadow-md shadow-accent-500/25">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <rect x="5" y="5" width="14" height="10" rx="2.5" fill="#0a0c1a" />
          <circle cx="9.5" cy="10" r="1.1" fill="#818cf8" />
          <circle cx="12" cy="10" r="1.1" fill="#818cf8" />
          <circle cx="14.5" cy="10" r="1.1" fill="#818cf8" />
          <path d="M5 18h14" stroke="#34d399" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      </div>
      <div className="rounded-2xl rounded-tl-sm border border-base-700 bg-base-800 px-4 py-3">
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 animate-pulse-dot rounded-full bg-accent-400" style={{ animationDelay: "0ms" }} />
          <span className="h-2 w-2 animate-pulse-dot rounded-full bg-accent-400" style={{ animationDelay: "150ms" }} />
          <span className="h-2 w-2 animate-pulse-dot rounded-full bg-accent-400" style={{ animationDelay: "300ms" }} />
        </div>
      </div>
    </div>
  );
}
