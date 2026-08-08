"use client";

import { useEffect, useState } from "react";

interface ScoreRingProps {
  score: number; // 0–100
  size?: number;
  strokeWidth?: number;
  label?: string;
}

export default function ScoreRing({
  score,
  size = 160,
  strokeWidth = 12,
  label,
}: ScoreRingProps) {
  const [progress, setProgress] = useState(0);
  const [display, setDisplay] = useState(0);

  const clamped = Math.max(0, Math.min(100, Math.round(score)));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  // Decide color band: >=75 emerald, 60–74 cyan, <60 rose
  const color =
    clamped >= 75 ? "#10B981" : clamped >= 60 ? "#06B6D4" : "#F43F5E";

  // Animate ring + count-up number in parallel
  useEffect(() => {
    const duration = 1200;
    const start = performance.now();
    let raf: number;

    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3); // easeOutCubic
      setProgress(eased);
      setDisplay(Math.round(clamped * eased));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [clamped]);

  return (
    <div
      className="relative inline-flex flex-col items-center gap-3"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - progress)}
          style={{
            transition: "stroke-dashoffset 60ms linear",
            filter: `drop-shadow(0 0 8px ${color}66)`,
          }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className="font-mono text-4xl font-bold tabular-nums"
          style={{ color }}
        >
          {display}
        </span>
        {label && (
          <span className="mt-1 text-[11px] uppercase tracking-widest text-ink-secondary">
            {label}
          </span>
        )}
      </div>
    </div>
  );
}
