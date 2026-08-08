import { Brain } from "lucide-react";

export function Brand({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const isLg = size === "lg";
  const isSm = size === "sm";

  return (
    <div className="flex items-center gap-2.5 select-none group">
      {/* Icon mark */}
      <div
        className={`relative flex shrink-0 items-center justify-center rounded-[10px] ${isLg ? "w-10 h-10" : isSm ? "w-7 h-7" : "w-8 h-8"}`}
        style={{
          background: "linear-gradient(135deg, #4f46e5 0%, #7c3aed 60%, #a78bfa 100%)",
          boxShadow: "0 4px 16px -4px rgba(99,102,241,0.6), inset 0 1px 0 rgba(255,255,255,0.15)",
        }}
      >
        <Brain
          className={`text-white ${isLg ? "w-5 h-5" : isSm ? "w-3.5 h-3.5" : "w-4 h-4"}`}
          strokeWidth={2}
        />
        {/* Subtle shine */}
        <div className="absolute inset-0 rounded-[10px] bg-gradient-to-b from-white/10 to-transparent" />
      </div>

      {/* Wordmark */}
      <div className="leading-none">
        <p
          className={`font-bold tracking-tight text-white ${isLg ? "text-xl" : isSm ? "text-[13px]" : "text-[15px]"}`}
          style={{ letterSpacing: "-0.02em" }}
        >
          Interview Agent
        </p>
        {!isSm && (
          <p className="text-[9px] font-semibold uppercase tracking-[0.18em] mt-0.5"
            style={{ color: "rgba(167,139,250,0.8)" }}>
            AI Technical Assessment
          </p>
        )}
      </div>
    </div>
  );
}
