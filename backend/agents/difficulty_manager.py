"""Difficulty manager.

Single-responsibility module for every difficulty decision in the
interview:

* baseline difficulty derived from the candidate profile (seniority,
  experience, pass rates),
* per-question difficulty progression along the easy -> medium -> advanced
  ramp for a given question index,
* difficulty for a follow-up based on the chosen follow-up strategy.

Centralising these rules keeps the planner, the evaluator and the
follow-up generator consistent.
"""
from __future__ import annotations

from models.candidate_profile import CandidateProfile
from models.enums import Difficulty, FollowUpStrategy

#: Candidate seniority -> baseline difficulty.
_SENIORITY_BASELINE: dict[str, Difficulty] = {
    "intern": Difficulty.EASY,
    "junior": Difficulty.EASY,
    "mid": Difficulty.MEDIUM,
    "senior": Difficulty.ADVANCED,
    "staff": Difficulty.ADVANCED,
}

#: Follow-up strategy -> target difficulty of the follow-up question.
_STRATEGY_DIFFICULTY: dict[FollowUpStrategy, Difficulty] = {
    FollowUpStrategy.DEEPER: Difficulty.ADVANCED,
    FollowUpStrategy.SIMPLIFY: Difficulty.EASY,
    FollowUpStrategy.RECOVERY: Difficulty.EASY,
    FollowUpStrategy.VERIFY: Difficulty.MEDIUM,
    FollowUpStrategy.PROBE: Difficulty.MEDIUM,
    FollowUpStrategy.NEXT_TOPIC: Difficulty.MEDIUM,
}


class DifficultyManager:
    """Owns all difficulty decisions."""

    def __init__(self) -> None:
        pass

    def baseline_for(self, profile: CandidateProfile) -> Difficulty:
        """Base difficulty for a candidate profile.

        Starts from the seniority mapping, then:

        * lowers one step when the historical pass rate is low (many
          failed attempts),
        * raises one step when first-try successes dominate,
        * nudges up for very high cohort engagement and down for very low
          engagement.
        """
        difficulty = _SENIORITY_BASELINE.get(
            profile.seniority, Difficulty.MEDIUM
        )
        # Pass rate is computed over *attempted* missions only: skipped
        # missions carry no attempt evidence and must not penalise the
        # candidate's difficulty.
        attempted = [s for s in profile.topic_signals if s.attempts > 0]
        total_attempts = sum(s.attempts for s in attempted)
        if total_attempts > 0:
            passed = sum(s.passed for s in attempted)
            pass_rate = passed / total_attempts
            if pass_rate < 0.4:
                difficulty = Difficulty.from_rank(difficulty.rank - 1)
            elif pass_rate > 0.8:
                difficulty = Difficulty.from_rank(difficulty.rank + 1)
        if profile.engagement_score >= 80:
            difficulty = Difficulty.from_rank(difficulty.rank + 1)
        elif profile.engagement_score <= 30:
            difficulty = Difficulty.from_rank(difficulty.rank - 1)
        return difficulty

    def question_difficulty(
        self,
        baseline: Difficulty,
        index: int,
        total: int,
    ) -> Difficulty:
        """Difficulty of the ``index``-th planned question.

        Progresses linearly from easy to advanced across the interview,
        offset by the candidate's baseline so a senior starts higher.
        """
        ramp = index / max(1, total - 1)
        raw_rank = baseline.rank + (2 * ramp - 0.5)
        return Difficulty.from_rank(round(raw_rank))

    def follow_up_difficulty(self, strategy: FollowUpStrategy) -> Difficulty:
        """Difficulty for a follow-up based on the chosen strategy."""
        return _STRATEGY_DIFFICULTY.get(strategy, Difficulty.MEDIUM)
