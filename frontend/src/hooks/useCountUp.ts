import { useEffect, useRef, useState } from "react";

/**
 * Animates a number from 0 to `target` with an ease-out curve.
 * Respects `prefers-reduced-motion` (jumps straight to the target).
 * Optionally starts when `start` becomes true (e.g. element scrolled into view).
 */
export function useCountUp(
  target: number,
  { duration = 1100, start = true, decimals = 0 }: { duration?: number; start?: boolean; decimals?: number } = {}
): string {
  const [value, setValue] = useState(start ? 0 : target);
  const frameRef = useRef<number | null>(null);
  const previousTarget = useRef(target);

  useEffect(() => {
    if (!start) {
      setValue(target);
      return;
    }
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion) {
      setValue(target);
      return;
    }

    const begin = performance.now();
    const from = previousTarget.current === target ? 0 : value;
    const delta = target - from;
    if (delta === 0) return;

    const tick = (now: number) => {
      const elapsed = Math.min(1, (now - begin) / duration);
      const eased = 1 - Math.pow(1 - elapsed, 3);
      setValue(from + delta * eased);
      if (elapsed < 1) {
        frameRef.current = requestAnimationFrame(tick);
      } else {
        previousTarget.current = target;
      }
    };
    frameRef.current = requestAnimationFrame(tick);
    return () => {
      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
      previousTarget.current = target;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target, start, duration]);

  return value.toFixed(decimals);
}
