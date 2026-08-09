import { useEffect, type RefObject } from "react";

/**
 * Adds the `revealed` class to every `.reveal` element inside `rootRef`
 * the first time it enters the viewport (IntersectionObserver). Respects
 * `prefers-reduced-motion` by revealing everything immediately.
 */
export function useReveal<T extends HTMLElement>(rootRef: RefObject<T>, deps: unknown[] = []): void {
  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      root.querySelectorAll(".reveal").forEach((el) => el.classList.add("revealed"));
      return;
    }

    const elements = Array.from(root.querySelectorAll<HTMLElement>(".reveal"));
    if (elements.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("revealed");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    elements.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}
