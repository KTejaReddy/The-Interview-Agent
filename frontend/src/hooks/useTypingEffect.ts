import { useEffect, useState } from "react";

/**
 * Reveals `text` character by character. Returns the visible substring.
 * Pass `active: false` to show the whole text immediately (e.g. on resume).
 */
export function useTypingEffect(text: string, active: boolean, speed = 14): string {
  const [visible, setVisible] = useState(active ? "" : text);

  useEffect(() => {
    if (!active) {
      setVisible(text);
      return;
    }
    setVisible("");
    let index = 0;
    const interval = window.setInterval(() => {
      index += 1;
      setVisible(text.slice(0, index));
      if (index >= text.length) {
        window.clearInterval(interval);
      }
    }, speed);
    return () => window.clearInterval(interval);
  }, [text, active, speed]);

  return visible;
}
