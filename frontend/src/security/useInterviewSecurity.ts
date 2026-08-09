import { useEffect, useRef, useCallback } from 'react';

export type SecurityEventType = 
  | 'TAB_SWITCH' 
  | 'WINDOW_BLUR' 
  | 'COPY_ATTEMPT' 
  | 'CUT_ATTEMPT' 
  | 'PASTE_ATTEMPT' 
  | 'CONTEXT_MENU_ATTEMPT' 
  | 'DEVTOOLS_SHORTCUT_ATTEMPT' 
  | 'FULLSCREEN_EXIT' 
  | 'PRINT_ATTEMPT';

export interface SecurityEvent {
  type: SecurityEventType;
  timestamp: string;
  metadata?: any;
}

interface UseInterviewSecurityProps {
  enabled: boolean;
  onWarning: (message: string) => void;
  onSecurityEvent?: (event: SecurityEvent) => void;
}

export function useInterviewSecurity({ enabled, onWarning, onSecurityEvent }: UseInterviewSecurityProps) {
  const tabSwitchCount = useRef(0);
  const blurTimeoutRef = useRef<number | null>(null);

  const logEvent = useCallback((type: SecurityEventType, metadata?: any) => {
    if (onSecurityEvent) {
      onSecurityEvent({ type, timestamp: new Date().toISOString(), metadata });
    }
  }, [onSecurityEvent]);

  // Handle focus loss
  const handleVisibilityChange = useCallback(() => {
    if (document.visibilityState === 'hidden') {
      logEvent('TAB_SWITCH');
      tabSwitchCount.current += 1;
      
      if (tabSwitchCount.current === 1) {
        onWarning("Please stay focused on the interview. Leaving the interview window has been recorded.");
      } else if (tabSwitchCount.current === 2) {
        onWarning("Leaving the interview window again has been recorded.");
      } else {
        onWarning("Multiple focus changes have been detected.");
      }
    }
  }, [logEvent, onWarning]);

  const handleBlur = useCallback(() => {
    if (blurTimeoutRef.current !== null) {
      window.clearTimeout(blurTimeoutRef.current);
    }
    blurTimeoutRef.current = window.setTimeout(() => {
      // If still not focused after 500ms
      if (!document.hasFocus()) {
        logEvent('WINDOW_BLUR');
      }
    }, 500);
  }, [logEvent]);

  const handleFocus = useCallback(() => {
    if (blurTimeoutRef.current !== null) {
      window.clearTimeout(blurTimeoutRef.current);
      blurTimeoutRef.current = null;
    }
  }, []);

  // Handle prevention of specific events
  const preventCheating = useCallback((e: Event, type: SecurityEventType, warningMsg?: string) => {
    const target = e.target as HTMLElement;
    const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable;
    
    // We allow pasting in inputs ONLY if it's explicitly allowed, but here we block paste everywhere for security
    if (type === 'PASTE_ATTEMPT' && isInput) {
      e.preventDefault();
      logEvent(type);
      if (warningMsg) onWarning(warningMsg);
      return false;
    }

    if (!isInput) {
      e.preventDefault();
      logEvent(type);
      if (warningMsg) onWarning(warningMsg);
      return false;
    }
    return true;
  }, [logEvent, onWarning]);

  useEffect(() => {
    if (!enabled) return;

    const onCopy = (e: ClipboardEvent) => preventCheating(e, 'COPY_ATTEMPT');
    const onCut = (e: ClipboardEvent) => preventCheating(e, 'CUT_ATTEMPT');
    const onPaste = (e: ClipboardEvent) => preventCheating(e, 'PASTE_ATTEMPT', "Paste is disabled during the interview.");
    const onContextMenu = (e: MouseEvent) => preventCheating(e, 'CONTEXT_MENU_ATTEMPT', "Context menu is disabled during the interview.");
    const onSelectStart = (e: Event) => preventCheating(e, 'CONTEXT_MENU_ATTEMPT'); // Block selection unless input
    const onDragStart = (e: DragEvent) => preventCheating(e, 'CONTEXT_MENU_ATTEMPT'); // Block drag unless input
    
    const onKeyDown = (e: KeyboardEvent) => {
      // Block F12
      if (e.key === 'F12') {
        e.preventDefault();
        logEvent('DEVTOOLS_SHORTCUT_ATTEMPT');
      }
      
      // Block Ctrl+Shift+I, Ctrl+Shift+J, Ctrl+Shift+C
      if (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'J' || e.key === 'C' || e.key === 'i' || e.key === 'j' || e.key === 'c')) {
        e.preventDefault();
        logEvent('DEVTOOLS_SHORTCUT_ATTEMPT');
      }
      // Mac equivalents: Cmd+Option+I, Cmd+Option+J, Cmd+Option+C
      if (e.metaKey && e.altKey && (e.key === 'I' || e.key === 'J' || e.key === 'C' || e.key === 'i' || e.key === 'j' || e.key === 'c')) {
        e.preventDefault();
        logEvent('DEVTOOLS_SHORTCUT_ATTEMPT');
      }

      // Block Ctrl+U (View Source)
      if ((e.ctrlKey || e.metaKey) && (e.key === 'u' || e.key === 'U')) {
        e.preventDefault();
        logEvent('DEVTOOLS_SHORTCUT_ATTEMPT');
      }

      // Block Ctrl+S (Save)
      if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'S')) {
        e.preventDefault();
        logEvent('CONTEXT_MENU_ATTEMPT');
      }

      // Block Ctrl+P (Print)
      if ((e.ctrlKey || e.metaKey) && (e.key === 'p' || e.key === 'P')) {
        e.preventDefault();
        logEvent('PRINT_ATTEMPT');
      }
    };

    const onFullscreenChange = () => {
      if (!document.fullscreenElement) {
        logEvent('FULLSCREEN_EXIT');
        onWarning("Please return to the interview window.");
      }
    };

    // Attach listeners
    document.addEventListener('copy', onCopy);
    document.addEventListener('cut', onCut);
    document.addEventListener('paste', onPaste);
    document.addEventListener('contextmenu', onContextMenu);
    document.addEventListener('selectstart', onSelectStart);
    document.addEventListener('dragstart', onDragStart);
    document.addEventListener('keydown', onKeyDown);
    document.addEventListener('visibilitychange', handleVisibilityChange);
    document.addEventListener('fullscreenchange', onFullscreenChange);
    window.addEventListener('blur', handleBlur);
    window.addEventListener('focus', handleFocus);

    return () => {
      // Cleanup listeners
      document.removeEventListener('copy', onCopy);
      document.removeEventListener('cut', onCut);
      document.removeEventListener('paste', onPaste);
      document.removeEventListener('contextmenu', onContextMenu);
      document.removeEventListener('selectstart', onSelectStart);
      document.removeEventListener('dragstart', onDragStart);
      document.removeEventListener('keydown', onKeyDown);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      document.removeEventListener('fullscreenchange', onFullscreenChange);
      window.removeEventListener('blur', handleBlur);
      window.removeEventListener('focus', handleFocus);
      if (blurTimeoutRef.current !== null) {
        window.clearTimeout(blurTimeoutRef.current);
      }
    };
  }, [enabled, handleVisibilityChange, handleBlur, handleFocus, preventCheating, logEvent, onWarning]);

  // Provide a function to trigger fullscreen
  const requestFullscreen = useCallback(() => {
    if (document.documentElement.requestFullscreen) {
      document.documentElement.requestFullscreen().catch(err => {
        console.warn("Fullscreen request denied", err);
      });
    }
  }, []);

  return { requestFullscreen, tabSwitchCount: tabSwitchCount.current };
}
