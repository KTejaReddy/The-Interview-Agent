import { Brand } from "./Brand";
import { ArrowRight } from "lucide-react";
import { useInterview } from "../context/InterviewContext";

export function Navigation() {
  const { candidates, health } = useInterview();
  const count = health?.candidates ?? candidates.length;

  return (
    <nav className="relative z-50 flex items-center justify-between px-6 py-3.5 w-full max-w-[1500px] mx-auto">
      {/* Brand */}
      <div className="flex-1">
        <Brand size="sm" />
      </div>

      {/* Center links */}
      <div className="hidden lg:flex flex-1 items-center justify-center gap-8">
        <a href="#candidates" className="nav-link active">Candidates</a>
        <a href="#how-it-works" className="nav-link">How it works</a>
        <a href="#reports" className="nav-link">Reports</a>
        <a href="#about" className="nav-link">About</a>
      </div>

      {/* Right side */}
      <div className="flex-1 flex justify-end items-center gap-3">
        {/* Live indicator with real count */}
        <div
          className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full text-[11px] font-semibold"
          style={{
            background: "rgba(34,197,94,0.10)",
            border: "1px solid rgba(34,197,94,0.22)",
            color: "rgba(74,222,128,0.9)",
          }}
        >
          <span
            className="w-1.5 h-1.5 rounded-full"
            style={{ background: "#22c55e", boxShadow: "0 0 6px #22c55e", animation: "node-pulse 2s ease-in-out infinite" }}
          />
          Live · {count} Candidates
        </div>

        {/* CTA */}
        <a href="#candidates" className="cta-btn">
          Start Interview
          <ArrowRight className="arrow w-3.5 h-3.5" />
        </a>
      </div>
    </nav>
  );
}
