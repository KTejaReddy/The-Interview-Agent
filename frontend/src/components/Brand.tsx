import { UserSquare2 } from "lucide-react";

export function Brand({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const iconSize = size === "lg" ? "h-8 w-8" : size === "sm" ? "h-5 w-5" : "h-6 w-6";
  const textSize = size === "lg" ? "text-2xl" : size === "sm" ? "text-sm" : "text-xl";
  
  return (
    <div className="flex items-center gap-3 select-none">
      <div className={`flex shrink-0 items-center justify-center text-accent-500`}>
        <UserSquare2 className={iconSize} strokeWidth={2} />
      </div>
      <div className="leading-none">
        <p className={`font-serif font-semibold tracking-tight text-base-900 ${textSize}`}>
          Interview Agent
        </p>
        {size !== "sm" && (
          <p className="text-[10px] font-sans font-medium text-base-600 uppercase tracking-widest mt-1">
            Technical Assessment
          </p>
        )}
      </div>
    </div>
  );
}
