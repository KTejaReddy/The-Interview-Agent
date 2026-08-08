import { Brand } from "./Brand";

export function Navigation() {
  return (
    <nav className="relative z-50 flex items-center justify-between px-6 py-4 w-full max-w-[1440px] mx-auto">
      <div className="flex-1">
        <Brand size="sm" />
      </div>
      
      <div className="hidden lg:flex flex-1 items-center justify-center gap-10 text-[13px] font-medium text-base-400">
        <a href="#candidates" className="text-white relative after:absolute after:-bottom-5 after:left-1/2 after:-translate-x-1/2 after:w-1/2 after:h-[2px] after:bg-accent-500 after:rounded-full">Candidates</a>
        <a href="#how-it-works" className="hover:text-white transition-colors">How it works</a>
        <a href="#" className="hover:text-white transition-colors">Reports</a>
        <a href="#" className="hover:text-white transition-colors">About</a>
      </div>
      
      <div className="flex-1 flex justify-end items-center gap-4">
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-100 border border-white/5">
          <div className="w-1.5 h-1.5 rounded-full bg-mint-500" />
          <span className="text-[11px] text-base-300 font-medium">20 Candidates</span>
        </div>
        <button className="px-5 py-2 bg-accent-600 hover:bg-accent-500 text-white rounded-lg text-xs font-bold transition-all shadow-lg shadow-accent-600/20">
          Start an Interview →
        </button>
      </div>
    </nav>
  );
}
