"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { Candidate, FeedbackReport, InterviewMessage } from "@/types";

interface InterviewStore {
  selectedCandidate: Candidate | null;
  sessionId: string | null;
  sessionStartedAt: number | null;
  messages: InterviewMessage[];
  isLoading: boolean;
  questionsAsked: number;
  daysCovered: number[];
  isComplete: boolean;
  feedback: FeedbackReport | null;
  /** Bumped to re-trigger the interview-start effect after a failed start */
  retrySignal: number;

  // actions
  setCandidate: (c: Candidate) => void;
  setSessionId: (id: string) => void;
  setSessionStartedAt: (ts: number) => void;
  addMessage: (m: InterviewMessage) => void;
  setLoading: (v: boolean) => void;
  incrementQuestions: () => void;
  addDay: (day: number) => void;
  setDaysCovered: (days: number[]) => void;
  setComplete: (feedback: FeedbackReport) => void;
  retryStart: () => void;
  reset: () => void;
}

const initialState = {
  selectedCandidate: null,
  sessionId: null,
  sessionStartedAt: null,
  messages: [],
  isLoading: false,
  questionsAsked: 0,
  daysCovered: [],
  isComplete: false,
  feedback: null,
  retrySignal: 0,
};

export const useInterviewStore = create<InterviewStore>()(
  persist(
    (set) => ({
      ...initialState,

      setCandidate: (c) => set({ selectedCandidate: c }),

      setSessionId: (id) => set({ sessionId: id }),

      setSessionStartedAt: (ts) => set({ sessionStartedAt: ts }),

      retryStart: () => set((s) => ({ retrySignal: s.retrySignal + 1 })),

      addMessage: (m) =>
        set((s) => ({ messages: [...s.messages, m] })),

      setLoading: (v) => set({ isLoading: v }),

      incrementQuestions: () =>
        set((s) => ({ questionsAsked: s.questionsAsked + 1 })),

      addDay: (day) =>
        set((s) =>
          s.daysCovered.includes(day)
            ? s
            : { daysCovered: [...s.daysCovered, day] }
        ),

      setDaysCovered: (days) => set({ daysCovered: days }),

      setComplete: (feedback) =>
        set({ feedback, isComplete: true }),

      reset: () => set({ ...initialState }),
    }),
    {
      // Survive page refreshes — an in-progress interview is never lost.
      name: "ai-interview-store",
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({
        selectedCandidate: s.selectedCandidate,
        sessionId: s.sessionId,
        sessionStartedAt: s.sessionStartedAt,
        messages: s.messages,
        questionsAsked: s.questionsAsked,
        daysCovered: s.daysCovered,
        isComplete: s.isComplete,
        feedback: s.feedback,
      }),
    }
  )
);
