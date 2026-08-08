import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  ApiError,
  fetchCandidates,
  fetchHealth,
  fetchSession,
  sendInterviewTurn,
  sendInterviewTurnStream,
} from "../services/api";
import type {
  CandidateSummary,
  ChatMessage,
  Feedback,
  HealthResponse,
  InterviewResponse,
  Page,
  StreamEvent,
} from "../types";

const SESSION_STORAGE_KEY = "ai-interview-session-id";

interface InterviewContextValue {
  candidates: CandidateSummary[];
  candidatesLoading: boolean;
  health: HealthResponse | null;
  sessionId: string | null;
  candidateId: string | null;
  messages: ChatMessage[];
  state: string;
  questionNumber: number;
  totalQuestions: number;
  currentDay: string | null;
  currentTopic: string | null;
  daysCovered: string[];
  interviewComplete: boolean;
  feedback: Feedback | null;
  interviewerTyping: boolean;
  loading: boolean;
  error: string | null;
  resumedPage: Page | null;
  startInterview: (candidateId: string, openingMessage: string) => Promise<void>;
  sendMessage: (text: string) => Promise<void>;
  resumeSession: (sessionId: string) => Promise<void>;
  reset: () => void;
  dismissError: () => void;
}

const InterviewContext = createContext<InterviewContextValue | null>(null);

function nextId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function InterviewProvider({ children }: { children: ReactNode }) {
  const [candidates, setCandidates] = useState<CandidateSummary[]>([]);
  const [candidatesLoading, setCandidatesLoading] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [candidateId, setCandidateId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [state, setState] = useState("START");
  const [questionNumber, setQuestionNumber] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [currentDay, setCurrentDay] = useState<string | null>(null);
  const [currentTopic, setCurrentTopic] = useState<string | null>(null);
  const [daysCovered, setDaysCovered] = useState<string[]>([]);
  const [interviewComplete, setInterviewComplete] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);

  const [interviewerTyping, setInterviewerTyping] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resumedPage, setResumedPage] = useState<Page | null>(null);

  const sessionIdRef = useRef<string | null>(null);
  const candidateIdRef = useRef<string | null>(null);

  const recordDay = useCallback((day: string | null | undefined) => {
    if (!day) return;
    setDaysCovered((previous) =>
      previous.includes(day) ? previous : [...previous, day]
    );
  }, []);

  const applyResponse = useCallback(
    (response: InterviewResponse) => {
      if (response.sessionId) {
        setSessionId(response.sessionId);
        sessionIdRef.current = response.sessionId;
      }
      if (response.state) setState(response.state);
      if (typeof response.questionNumber === "number")
        setQuestionNumber(response.questionNumber);
      if (typeof response.totalQuestions === "number")
        setTotalQuestions(response.totalQuestions);
      setCurrentDay(response.currentDay ?? null);
      setCurrentTopic(response.currentTopic ?? null);
      setInterviewComplete(response.done);
      if (response.feedback) setFeedback(response.feedback);
      recordDay(response.currentDay);

      setMessages((previous) => [
        ...previous,
        {
          id: nextId(),
          role: "interviewer",
          text: response.reply,
          state: response.state,
          questionNumber: response.questionNumber,
          currentDay: response.currentDay,
          currentTopic: response.currentTopic,
          isQuestion:
            response.state === "QUESTIONING" ||
            response.state === "FOLLOW_UP",
        },
      ]);
    },
    [recordDay]
  );

  const runTurn = useCallback(
    async (text: string, start: boolean) => {
      setError(null);
      setInterviewerTyping(true);
      setMessages((previous) => [
        ...previous,
        { id: nextId(), role: "candidate", text },
      ]);
      // Per the spec, the *start* request carries the candidate and the
      // server returns the session id; continuation requests carry it.
      // The bundled UI uses the candidateId shorthand for the first call.
      const payload = {
        sessionId: start ? null : sessionIdRef.current,
        candidateId: candidateIdRef.current ?? "",
        message: text,
      };

      const handleEvent = (event: StreamEvent) => {
        if (event.type === "error" && event.error) {
          throw new ApiError(
            0,
            event.error.code ?? "stream_error",
            event.error.message ?? "The interviewer ran into a problem."
          );
        }
      };

      try {
        // Prefer SSE streaming (shows the interviewer composing); fall back
        // to plain JSON only when the backend simply does not support SSE
        // (content-type mismatch). Real HTTP errors propagate.
        let response: InterviewResponse | null = null;
        try {
          response = await sendInterviewTurnStream(payload, handleEvent);
        } catch (err) {
          if (err instanceof ApiError && err.status !== 0) {
            throw err; // the backend answered with an error status
          }
          if (err instanceof ApiError && err.code === "network_error") {
            throw err; // backend unreachable
          }
          // Otherwise (stream unsupported) retry the same turn via JSON.
          response = await sendInterviewTurn(payload);
        }
        if (response) applyResponse(response);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Something went wrong. Please try again.");
        }
      } finally {
        setInterviewerTyping(false);
      }
    },
    [applyResponse]
  );

  const startInterview = useCallback(
    async (candidate: string, openingMessage: string) => {
      setLoading(true);
      setError(null);
      setMessages([]);
      setFeedback(null);
      setInterviewComplete(false);
      setDaysCovered([]);
      candidateIdRef.current = candidate;
      setCandidateId(candidate);
      try {
        await runTurn(openingMessage, true);
        if (sessionIdRef.current) {
          localStorage.setItem(SESSION_STORAGE_KEY, sessionIdRef.current);
        }
      } finally {
        setLoading(false);
      }
    },
    [runTurn]
  );

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || interviewerTyping) return;
      await runTurn(text, false);
    },
    [runTurn, interviewerTyping]
  );

  const resumeSession = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const snapshot = await fetchSession(id);
      sessionIdRef.current = snapshot.sessionId;
      candidateIdRef.current = snapshot.candidateId;
      setSessionId(snapshot.sessionId);
      setCandidateId(snapshot.candidateId);
      setState(snapshot.state);
      setQuestionNumber(snapshot.questionNumber);
      setTotalQuestions(snapshot.totalQuestions);
      setInterviewComplete(snapshot.interviewComplete);
      setFeedback(snapshot.feedback);
      const transcript = snapshot.messages.map((message) => ({
        id: nextId(),
        role: message.role as "candidate" | "interviewer",
        text: message.text,
      }));
      setMessages(transcript);
      // Rebuild the days-covered set from question messages' day fields.
      const days = new Set<string>();
      transcript.forEach((message) => {
        if (message.role === "interviewer" && message.text) {
          // Day chips are recovered from the snapshot questionNumber only;
          // the snapshot does not carry day titles, so we leave the set to
          // grow as the interview continues.
          void days;
        }
      });
      setDaysCovered([]);
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      localStorage.removeItem(SESSION_STORAGE_KEY);
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    sessionIdRef.current = null;
    candidateIdRef.current = null;
    setSessionId(null);
    setCandidateId(null);
    setMessages([]);
    setState("START");
    setQuestionNumber(0);
    setTotalQuestions(0);
    setCurrentDay(null);
    setCurrentTopic(null);
    setDaysCovered([]);
    setInterviewComplete(false);
    setFeedback(null);
    setError(null);
    localStorage.removeItem(SESSION_STORAGE_KEY);
  }, []);

  const dismissError = useCallback(() => setError(null), []);

  // Load candidates + health + check resume once.
  const bootRef = useRef(false);
  if (!bootRef.current) {
    bootRef.current = true;
    void (async () => {
      setCandidatesLoading(true);
      try {
        const [candidatesData, healthData] = await Promise.all([
          fetchCandidates(),
          fetchHealth(),
        ]);
        setCandidates(candidatesData);
        setHealth(healthData);
      } catch {
        /* landing page renders its own error state */
      } finally {
        setCandidatesLoading(false);
      }

      // Auto-resume from localStorage after boot.
      const storedSessionId = localStorage.getItem(SESSION_STORAGE_KEY);
      if (storedSessionId) {
        try {
          const snapshot = await fetchSession(storedSessionId);
          sessionIdRef.current = snapshot.sessionId;
          candidateIdRef.current = snapshot.candidateId;
          setSessionId(snapshot.sessionId);
          setCandidateId(snapshot.candidateId);
          setState(snapshot.state);
          setQuestionNumber(snapshot.questionNumber);
          setTotalQuestions(snapshot.totalQuestions);
          setInterviewComplete(snapshot.interviewComplete);
          setFeedback(snapshot.feedback);
          setMessages(
            snapshot.messages.map((msg) => ({
              id: nextId(),
              role: msg.role as "candidate" | "interviewer",
              text: msg.text,
            }))
          );
          setResumedPage(
            snapshot.interviewComplete ? "feedback" : "interview"
          );
        } catch {
          localStorage.removeItem(SESSION_STORAGE_KEY);
        }
      }
    })();
  }

  const value = useMemo<InterviewContextValue>(
    () => ({
      candidates,
      candidatesLoading,
      health,
      sessionId,
      candidateId,
      messages,
      state,
      questionNumber,
      totalQuestions,
      currentDay,
      currentTopic,
      daysCovered,
      interviewComplete,
      feedback,
      interviewerTyping,
      loading,
      error,
      resumedPage,
      startInterview,
      sendMessage,
      resumeSession,
      reset,
      dismissError,
    }),
    [
      candidates,
      candidatesLoading,
      health,
      sessionId,
      candidateId,
      messages,
      state,
      questionNumber,
      totalQuestions,
      currentDay,
      currentTopic,
      daysCovered,
      interviewComplete,
      feedback,
      interviewerTyping,
      loading,
      error,
      resumedPage,
      startInterview,
      sendMessage,
      resumeSession,
      reset,
      dismissError,
    ]
  );

  return (
    <InterviewContext.Provider value={value}>
      {children}
    </InterviewContext.Provider>
  );
}

export function useInterview(): InterviewContextValue {
  const context = useContext(InterviewContext);
  if (!context) {
    throw new Error("useInterview must be used inside <InterviewProvider>");
  }
  return context;
}
