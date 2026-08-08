import candidatesData from "@/data/candidates.json";
import { Candidate, CandidatesFile, Mission } from "@/types";

const data = candidatesData as CandidatesFile;

export function getAllCandidates(): Candidate[] {
  return data.candidates;
}

export function getCandidateById(id: string): Candidate | undefined {
  return data.candidates.find((c) => c.member.id === id);
}

/**
 * Get only the missions where passed === true (exclude skipped and failed).
 * These are the ONLY missions we can interview about.
 */
export function getPassedMissions(candidate: Candidate): Mission[] {
  return candidate.missions.filter((m) => m.passed === true);
}

/**
 * Get missions that were difficult (high attempts) — these are
 * interesting topics to probe deeper on.
 */
export function getDifficultMissions(candidate: Candidate): Mission[] {
  return candidate.missions.filter(
    (m) => m.passed === true && (m.attempts ?? 1) >= 3
  );
}

/**
 * Get skipped or failed missions — do NOT interview about these.
 */
export function getExcludedDays(candidate: Candidate): number[] {
  return candidate.missions
    .filter((m) => m.skipped === true || m.passed === false)
    .map((m) => m.day);
}

/**
 * Derive a "difficulty" label for use in the system prompt.
 * missions with attempts >= 4 were clearly hard for the candidate.
 */
export function getMissionDifficultyLabel(mission: Mission): string {
  const a = mission.attempts ?? 1;
  if (a === 1) return "mastered on first try";
  if (a === 2) return "required one retry";
  if (a === 3) return "needed multiple attempts";
  if (a >= 4) return "very challenging — struggled significantly";
  return "completed";
}

/**
 * Compute overall engagement score from signals.
 */
export function computeEngagementScore(candidate: Candidate): number {
  const { commitDays, missionsCompleted, missionsFirstTry } = candidate.signals;
  return Math.round(
    (commitDays / 31) * 40 +
    (missionsCompleted / 31) * 40 +
    (missionsFirstTry / Math.max(missionsCompleted, 1)) * 20
  );
}
