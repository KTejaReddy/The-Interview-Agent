import { useEffect, type RefObject } from "react";

/**
 * Scrolls the referenced element to the bottom whenever `dependencies`
 * change. Used to keep the interview transcript pinned to the newest
 * message (auto-scroll requirement).
 */
export function useAutoScroll<T extends HTMLElement>(
  ref: RefObject<T>,
  dependencies: unknown[]
): void {
  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    element.scrollTo({
      top: element.scrollHeight,
      behavior: dependencies.length ? "smooth" : "auto",
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);
}
