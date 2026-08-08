"use client";

import { useEffect, useState } from "react";

interface ProgressBarProps {
  value: number;
  max: number;
  className?: string;
  /** Tailwind gradient classes for the fill (defaults to brand gradient) */
  fillClassName?: string;
  /** Show a small label with value/max */
  showLabel?: boolean;
  /** Color used by the glow shadow */
  glowColor?: string;
}

export default function ProgressBar({
  value,
  max,
  className = "",
  fillClassName = "bg-gradient-to-r from-brand-violet to-brand-cyan",
  showLabel = false,
  glowColor = "rgba(124, 58, 237, 0.5)",
}: ProgressBarProps) {
  const [fillWidth, setFillWidth] = useState(0);
  const pct = Math.max(0, Math.min(100, (value / Math.max(max, 1)) * 100));

  // Animate the fill after mount so the bar visibly "fills" from 0
  useEffect(() => {
    const t = setTimeout(() => setFillWidth(pct), 60);
    return () => clearTimeout(t);
  }, [pct]);

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className="relative h-2 flex-1 overflow-hidden rounded-full bg-white/5">
        <div
          className={`relative h-full rounded-full ${fillClassName} transition-[width] duration-700 ease-out`}
          style={{
            width: `${fillWidth}%`,
            boxShadow: `0 0 12px ${glowColor}`,
          }}
        >
          <span className="absolute right-0 top-1/2 h-full w-3 -translate-y-1/2 rounded-full bg-white/40 blur-[3px]" />
        </div>
      </div>
      {showLabel && (
        <span className="font-mono text-xs text-ink-secondary tabular-nums">
          {value}/{max}
        </span>
      )}
    </div>
  );
}
