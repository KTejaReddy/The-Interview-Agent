import { useEffect, useState } from "react";

interface ScoreRingProps {
  score: number; // 0..100
  size?: number;
}

function scoreTone(score: number): string {
  if (score >= 85) return "#00F0FF"; // accent-cyan
  if (score >= 70) return "#A07CFE"; // accent-purple
  if (score >= 50) return "#F59E0B"; // amber-500
  return "#F26457"; // coral (red)
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
      <svg width={size} height={size} className="-rotate-90 drop-shadow-[0_0_15px_rgba(255,255,255,0.1)]">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.05)"
          strokeWidth="8"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          style={{ transition: "stroke-dashoffset 60ms linear", filter: `drop-shadow(0 0 10px ${color}80)` }}
        />
      </svg>
      <div className="absolute flex flex-col items-center z-20">
        <span className="text-3xl font-black text-white" style={{ textShadow: `0 0 20px ${color}80` }}>
          {progress}
        </span>
        <span className="text-[9px] font-bold uppercase tracking-widest text-base-500 mt-0.5">
          / 100
        </span>
      </div>
    </div>
  );
}
