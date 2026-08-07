export function Brand({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const textSize = size === "lg" ? "text-2xl" : size === "sm" ? "text-sm" : "text-lg";
  return (
    <div className="flex items-center gap-2.5 select-none">
      <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-accent-500 to-mint-500 shadow-lg shadow-accent-500/30">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
          <rect x="4" y="4" width="16" height="12" rx="3" fill="#0a0c1a" />
          <circle cx="9" cy="10" r="1.4" fill="#818cf8" />
          <circle cx="12" cy="10" r="1.4" fill="#818cf8" />
          <circle cx="15" cy="10" r="1.4" fill="#818cf8" />
          <path d="M4 19h16" stroke="#34d399" strokeWidth="2" strokeLinecap="round" />
        </svg>
      </div>
      <div className="leading-tight">
        <p className={`font-bold tracking-tight text-white ${textSize}`}>
          AI Interview Agent
        </p>
        {size !== "sm" && (
          <p className="text-[11px] font-medium text-slate-400">
            Senior Staff Engineer · live technical interview
          </p>
        )}
      </div>
    </div>
  );
}
