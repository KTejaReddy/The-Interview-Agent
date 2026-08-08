import { Brand } from "./Brand";
import { ArrowRight } from "lucide-react";

export function Navigation() {
  return (
    <nav
      className="relative z-50 flex items-center justify-between px-6 py-3.5 w-full max-w-[1500px] mx-auto"
    >
      {/* Brand */}
      <div className="flex-1">
        <Brand size="sm" />
      </div>

      {/* Center links */}
      <div className="hidden lg:flex flex-1 items-center justify-center gap-8">
        <a href="#candidates" className="nav-link active">Candidates</a>
        <a href="#how-it-works" className="nav-link">How it works</a>
        <a href="#" className="nav-link">Reports</a>
        <a href="#" className="nav-link">About</a>
      </div>

      {/* Right side */}
      <div className="flex-1 flex justify-end items-center gap-3">
        {/* Live indicator */}
        <div
          className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full text-[11px] font-semibold"
          style={{
            background: "rgba(16,185,129,0.1)",
            border: "1px solid rgba(16,185,129,0.2)",
            color: "rgba(52,211,153,0.9)",
          }}
        >
          <span
            className="w-1.5 h-1.5 rounded-full"
            style={{ background: "#34d399", boxShadow: "0 0 6px #34d399", animation: "node-pulse 2s ease-in-out infinite" }}
          />
          Live · 20 Candidates
        </div>

        {/* CTA */}
        <button className="cta-btn">
          Start Interview
          <ArrowRight className="arrow w-3.5 h-3.5" />
        </button>
      </div>
    </nav>
  );
}
