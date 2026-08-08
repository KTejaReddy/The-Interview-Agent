import { useEffect, useState } from "react";

interface ScoreRingProps {
  score: number; // 0..100
  size?: number;
}

function scoreTone(score: number): string {
  if (score >= 85) return "#22C55E"; // mint-500
  if (score >= 70) return "#3B82F6"; // accent-400 (cobalt)
  if (score >= 50) return "#F59E0B"; // amber-500
  return "#F26457"; // coral
}

export function ScoreRing({ score, size = 120 }: ScoreRingProps) {
  const [progress, setProgress] = useState(0);
  const radius = size / 2 - 12;
  const circumference = 2 * Math.PI * radius;
  const color = scoreTone(score);

  useEffect(() => {
    const start = performance.now();
    const duration = 1200;
    let frame = 0;
    const tick = (now: number) => {
      const elapsed = now - start;
      const t = Math.min(1, elapsed / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setProgress(Math.round(eased * score));
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [score]);

  const dashOffset = circumference * (1 - progress / 100);

  return (
    <div
      className="relative flex items-center justify-center"
      style={{ width: size, height: size }}
      aria-label={`Overall score ${progress} out of 100`}
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(0,0,0,0.05)"
          strokeWidth="6"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          style={{ transition: "stroke-dashoffset 60ms linear" }}
        />
      </svg>
      <div className="absolute flex flex-col items-center z-20">
        <span className="text-3xl font-serif font-black text-base-900">
          {progress}
        </span>
        <span className="text-[9px] font-bold uppercase tracking-widest text-base-400 mt-0.5">
          / 100
        </span>
      </div>
    </div>
  );
}
