export function LoadingOverlay({ label = "Preparing your interview…" }: { label?: string }) {
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-5 bg-base-950/90 backdrop-blur-sm animate-fade-in">
      <div className="relative h-14 w-14">
        <div className="absolute inset-0 animate-ping rounded-2xl bg-accent-500/40" />
        <div className="absolute inset-0 flex items-center justify-center rounded-2xl bg-gradient-to-br from-accent-500 to-mint-500 shadow-xl shadow-accent-500/40">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
            <rect x="4" y="4" width="16" height="12" rx="3" fill="#0a0c1a" />
            <circle cx="9" cy="10" r="1.4" fill="#818cf8" />
            <circle cx="12" cy="10" r="1.4" fill="#818cf8" />
            <circle cx="15" cy="10" r="1.4" fill="#818cf8" />
            <path d="M4 19h16" stroke="#34d399" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </div>
      </div>
      <p className="animate-pulse text-sm font-medium text-slate-300">{label}</p>
    </div>
  );
}
