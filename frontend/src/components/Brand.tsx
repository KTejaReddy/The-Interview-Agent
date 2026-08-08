import { Bot } from "lucide-react";

export function Brand({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const textSize = size === "lg" ? "text-2xl" : size === "sm" ? "text-sm" : "text-lg";
  return (
    <div className="flex items-center gap-3 select-none">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-premium-gradient shadow-lg shadow-accent-600/30">
        <Bot className="h-5 w-5 text-white" />
      </div>
      <div className="leading-tight">
        <p className={`font-bold tracking-tight text-white ${textSize}`}>
          Interview Agent
        </p>
        {size !== "sm" && (
          <p className="text-[10px] font-medium text-slate-400 uppercase tracking-widest mt-0.5">
            Technical Assessment
          </p>
        )}
      </div>
    </div>
  );
}
