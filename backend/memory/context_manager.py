"""Context manager.

Builds the exact snapshot of the conversation that each prompt needs:
candidate profile summary, memory aggregates (topics, days, mistakes, strong
answers), the last few turns, the current state and the next planned
question.  Keeping this in one place prevents prompt drift across agents.
"""
from __future__ import annotations

from dataclasses import dataclass

from memory.conversation_memory import ConversationMemory
from models.candidate_profile import CandidateProfile
from models.interview_state import InterviewState
from models.plan import InterviewPlan, PlannedQuestion


@dataclass
class InterviewContext:
    """Everything a prompt might need about the current turn."""

    state: InterviewState
    candidate: CandidateProfile
    plan: InterviewPlan
    current_question_index: int
    memory: ConversationMemory
    pending_question: PlannedQuestion | None = None
    last_answer: str = ""
    is_follow_up: bool = False
    follow_ups_used: int = 0

    # --- convenience projections ------------------------------------------

    @property
    def transcript_excerpt(self) -> str:
        return self.memory.format_transcript()

    @property
    def candidate_mentions(self) -> str:
        """Curriculum concepts the candidate raised, for cross-referencing."""
        mentions = self.memory.mentions
        return ", ".join(mentions) if mentions else "none yet"

    @property
    def aggregate_summary(self) -> str:
        mem = self.memory
        contradictions = (
            "; ".join(mem.contradictions) if mem.contradictions else "none detected"
        )
        return (
            f"Questions asked: {mem.count}\n"
            f"Topics covered: {', '.join(mem.topics_covered) or 'none yet'}\n"
            f"Curriculum days covered: {len(mem.days_covered)} "
            f"({', '.join(map(str, mem.days_covered)) or 'none'})\n"
            f"Mistakes: {len(mem.mistakes)} | Strong answers: {len(mem.strong_answers)}\n"
            f"Average score: {mem.average_score:.1f}/10\n"
            f"Concepts the candidate mentioned: {self.candidate_mentions}\n"
            f"Contradictions noticed: {contradictions}\n"
            f"Consecutive weak answers: {mem.consecutive_weak}\n"
            f"Interviewer state: emotion={mem.interviewer_emotion}, "
            f"firmness={mem.firmness}/3"
        )


class ContextManager:
    """Factory for :class:`InterviewContext` snapshots."""

    def build(
        self,
        state: InterviewState,
        candidate: CandidateProfile,
        plan: InterviewPlan,
        memory: ConversationMemory,
        question_index: int,
        pending_question: PlannedQuestion | None = None,
        last_answer: str = "",
        is_follow_up: bool = False,
        follow_ups_used: int = 0,
    ) -> InterviewContext:
        return InterviewContext(
            state=state,
            candidate=candidate,
            plan=plan,
            current_question_index=question_index,
            memory=memory,
            pending_question=pending_question,
            last_answer=last_answer,
            is_follow_up=is_follow_up,
            follow_ups_used=follow_ups_used,
        )
