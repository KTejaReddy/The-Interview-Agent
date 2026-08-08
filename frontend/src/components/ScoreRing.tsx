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
      <div 
        className="absolute inset-0 rounded-full" 
        style={{ 
          background: `radial-gradient(circle, ${color}20 0%, transparent 60%)`,
          filter: "blur(8px)" 
        }} 
      />
      <svg width={size} height={size} className="-rotate-90 drop-shadow-2xl relative z-10">
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
          style={{ 
            transition: "stroke-dashoffset 60ms linear",
            filter: `drop-shadow(0 0 6px ${color}80)`
          }}
        />
      </svg>
      <div className="absolute flex flex-col items-center z-20">
        <span className="text-3xl font-black tracking-tighter text-white drop-shadow-md">
          {progress}
        </span>
        <span className="text-[9px] font-bold uppercase tracking-widest text-slate-400 mt-0.5">
          / 100
        </span>
      </div>
    </div>
  );
}
