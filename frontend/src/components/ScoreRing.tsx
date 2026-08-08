import { useEffect, useState } from "react";

interface ScoreRingProps {
  score: number; // 0..100
  size?: number;
}

function scoreTone(score: number): string {
  if (score >= 85) return "#34d399"; // emerald
  if (score >= 70) return "#818cf8"; // indigo
  if (score >= 50) return "#fbbf24"; // amber
  return "#f87171"; // red
}

/**
 * Animated circular score display used on the feedback page.  Animates from
 * 0 to the final score on mount.
 */
export function ScoreRing({ score, size = 120 }: ScoreRingProps) {
  const [progress, setProgress] = useState(0);
  const radius = size / 2 - 10;
  const circumference = 2 * Math.PI * radius;
  const color = scoreTone(score);

  useEffect(() => {
    const start = performance.now();
    const duration = 900;
    let frame = 0;
    const tick = (now: number) => {
      const elapsed = now - start;
      const t = Math.min(1, elapsed / duration);
      // ease-out cubic
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
          stroke="rgba(148,163,184,0.15)"
          strokeWidth="10"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          style={{ transition: "stroke-dashoffset 60ms linear" }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-3xl font-extrabold tracking-tight text-white">
          {progress}
        </span>
        <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-500">
          / 100
        </span>
      </div>
    </div>
  );
}
