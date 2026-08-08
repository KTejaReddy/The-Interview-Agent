import { Bot } from "lucide-react";

export function Brand({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const iconSize = size === "lg" ? "h-6 w-6" : size === "sm" ? "h-4 w-4" : "h-5 w-5";
  const textSize = size === "lg" ? "text-xl" : size === "sm" ? "text-sm" : "text-base";
  
  return (
    <div className="flex items-center gap-3 select-none">
      <div className={`flex shrink-0 items-center justify-center rounded-xl bg-premium-gradient shadow-lg shadow-accent-600/30 ${size === "lg" ? "w-10 h-10" : size === "sm" ? "w-7 h-7" : "w-8 h-8"}`}>
        <Bot className={`${iconSize} text-white`} strokeWidth={2.5} />
      </div>
      <div className="leading-tight">
        <p className={`font-sans font-bold tracking-tight text-white ${textSize}`}>
          Interview Agent
        </p>
        {size !== "sm" && (
          <p className="text-[9px] font-medium text-accent-400 uppercase tracking-widest mt-0.5">
            Technical Assessment
          </p>
        )}
      </div>
    </div>
  );
}
