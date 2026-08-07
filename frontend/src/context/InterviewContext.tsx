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
} from "../services/api";
import type {
  CandidateSummary,
  ChatMessage,
  Feedback,
  HealthResponse,
  InterviewResponse,
  Page,
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
  const [interviewComplete, setInterviewComplete] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);

  const [interviewerTyping, setInterviewerTyping] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resumedPage, setResumedPage] = useState<Page | null>(null);

  const sessionIdRef = useRef<string | null>(null);
  const candidateIdRef = useRef<string | null>(null);

  const applyResponse = useCallback(
    (response: InterviewResponse) => {
      setSessionId(response.sessionId);
      sessionIdRef.current = response.sessionId;
      setState(response.state);
      setQuestionNumber(response.questionNumber);
      setTotalQuestions(response.totalQuestions);
      setCurrentDay(response.currentDay);
      setCurrentTopic(response.currentTopic);
      setInterviewComplete(response.interviewComplete);
      if (response.feedback) setFeedback(response.feedback);

      setMessages((previous) => [
        ...previous,
        {
          id: nextId(),
          role: "interviewer",
          text: response.message,
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
    []
  );

  const runTurn = useCallback(
    async (text: string, start: boolean) => {
      setError(null);
      setInterviewerTyping(true);
      setMessages((previous) => [
        ...previous,
        { id: nextId(), role: "candidate", text },
      ]);
      try {
        const response = await sendInterviewTurn({
          sessionId: start ? null : sessionIdRef.current,
          candidateId: candidateIdRef.current ?? "",
          message: text,
        });
        applyResponse(response);
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
      setMessages(
        snapshot.messages.map((message) => ({
          id: nextId(),
          role: message.role,
          text: message.text,
        }))
      );
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
              role: msg.role,
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
