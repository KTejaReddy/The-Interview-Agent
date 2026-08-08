"""Interview manager.

The orchestrator of the whole interview.  It owns the state machine and
decides, for every candidate message, which agent runs next and which state
the conversation moves into.

Turn protocol
-------------
The candidate sends a message in every turn; the server replies with the
interviewer's next utterance.  State is carried entirely by ``sessionId``.

    START -> INTRODUCTION -> QUESTIONING -> FOLLOW_UP <-> ... -> FINAL_QUESTION
                                                             -> EVALUATION
                                                             -> FEEDBACK
                                                             -> DONE
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agents.candidate_analyzer import CandidateAnalyzer
from agents.feedback_generator import FeedbackGenerator
from agents.followup_generator import FollowUpGenerator
from agents.question_planner import QuestionPlanner
from agents.response_evaluator import ResponseEvaluator
from config import Settings
from memory.context_manager import ContextManager
from memory.conversation_memory import ConversationMemory
from models.interview_state import InterviewState
from models.plan import PlannedQuestion
from models.session import InterviewSession
from retrieval.candidate_loader import CandidateLoader
from retrieval.curriculum_retriever import CurriculumRetriever
from services.llm_service import LLMService
from services.prompt_builder import PromptBuilder
from services.session_manager import SessionManager
from utils.errors import AppError, InvalidStateTransitionError
from utils.logging import get_logger

logger = get_logger(__name__)

#: A message at least this long is treated as a self-introduction on the
#: very first turn, so the intro step can be skipped gracefully.
_INTRO_LENGTH_THRESHOLD = 60


@dataclass
class InterviewTurnResult:
    """The complete server response for one turn."""

    session_id: str
    state: str
    message: str
    question_number: int
    total_questions: int
    current_day: str | None
    current_topic: str | None
    interview_complete: bool
    feedback: dict[str, Any] | None = None

    def to_api(self) -> dict[str, Any]:
        return {
            "sessionId": self.session_id,
            "state": self.state,
            "message": self.message,
            "questionNumber": self.question_number,
            "totalQuestions": self.total_questions,
            "currentDay": self.current_day,
            "currentTopic": self.current_topic,
            "interviewComplete": self.interview_complete,
            "feedback": self.feedback,
        }


class InterviewManager:
    """Coordinates every module through the interview lifecycle."""

    def __init__(
        self,
        settings: Settings,
        sessions: SessionManager,
        llm: LLMService,
        prompts: PromptBuilder,
        retriever: CurriculumRetriever,
        candidates: CandidateLoader,
        analyzer: CandidateAnalyzer,
        planner: QuestionPlanner,
        evaluator: ResponseEvaluator,
        followups: FollowUpGenerator,
        feedback_generator: FeedbackGenerator,
        context_manager: ContextManager,
    ) -> None:
        self._settings = settings
        self._sessions = sessions
        self._llm = llm
        self._prompts = prompts
        self._retriever = retriever
        self._candidates = candidates
        self._analyzer = analyzer
        self._planner = planner
        self._evaluator = evaluator
        self._followups = followups
        self._feedback_generator = feedback_generator
        self._context = context_manager

    # ------------------------------------------------------------------ public

    async def start_session(
        self, candidate_id: str, first_message: str
    ) -> InterviewSession:
        """Create a session: analyze candidate, build the plan skeleton."""
        raw = self._candidates.get(candidate_id)
        profile = self._analyzer.analyze(raw)
        plan = self._planner.build_plan(profile)

        session = InterviewSession(
            session_id=self._sessions.new_session_id(),
            candidate_id=candidate_id,
            profile=profile,
            plan=plan,
            memory=ConversationMemory(
                max_history_turns=self._settings.max_history_turns
            ),
        )
        await self._sessions.create(session)
        logger.info(
            "Session %s started for candidate %s",
            session.session_id,
            candidate_id,
        )
        return session

    async def handle_message(
        self, session: InterviewSession, message: str
    ) -> InterviewTurnResult:
        """Advance the conversation one turn and return the server reply."""
        await self._sessions.sweep_expired()
        # Record the candidate's utterance before dispatching.
        self._append(session, "candidate", message)
        state = session.state_machine.current

        if state == InterviewState.START:
            return await self._begin(session, message)
        if state == InterviewState.INTRODUCTION:
            return await self._after_intro(session)
        if state in (InterviewState.QUESTIONING, InterviewState.FOLLOW_UP):
            return await self._handle_answer(session, message)
        if state == InterviewState.FINAL_QUESTION:
            return await self._finalize(session)
        if state == InterviewState.DONE:
            return self._final_result(session)

        raise InvalidStateTransitionError(
            f"Unhandled interview state: {state.value}"
        )

    # ------------------------------------------------------------------ phases

    async def _begin(self, session: InterviewSession, message: str) -> InterviewTurnResult:
        session.state_machine.transition(InterviewState.INTRODUCTION)

        # Skip generic introduction to immediately dive into contextual technical question
        return await self._after_intro(session, skipped_intro=True)

    async def _after_intro(self, session: InterviewSession, skipped_intro: bool = False) -> InterviewTurnResult:
        session.state_machine.transition(InterviewState.QUESTIONING)
        return await self._ask_question(session, 0, first=True)

    async def _handle_answer(
        self, session: InterviewSession, message: str
    ) -> InterviewTurnResult:
        was_follow_up = session.state_machine.current == InterviewState.FOLLOW_UP

        question = session.plan.question_at(session.current_question_index)
        if question is None:  # defensive: no pending question -> advance
            return await self._advance(session)

        asked_text = session.current_question_text or question.question
        asked_difficulty = session.current_difficulty or question.difficulty

        context = self._context.build(
            state=session.state_machine.current,
            candidate=session.profile,
            plan=session.plan,
            memory=session.memory,
            question_index=session.current_question_index,
            last_answer=message,
            is_follow_up=was_follow_up,
            follow_ups_used=session.follow_ups_used,
        )

        evaluation = await self._evaluator.evaluate(context, question, message)

        session.memory.add_turn(
            question=asked_text,
            topic=question.topic,
            day_index=question.day_index,
            question_type=question.question_type,
            difficulty=asked_difficulty,
            answer=message,
            score=evaluation.score,
            verdict=evaluation.verdict,
            follow_up=evaluation.strategy,
            notes=evaluation.notes,
            is_follow_up=was_follow_up,
        )
        session.last_question_day = question.day_index

        # --- decide: follow-up or move on --------------------------------
        wants_follow_up = evaluation.wants_follow_up and (
            session.follow_ups_used < self._settings.max_follow_ups_per_question
        )
        if wants_follow_up:
            return await self._ask_follow_up(session, question, message, context, evaluation)

        return await self._advance(session)

    async def _ask_follow_up(self, session, question, answer, context, evaluation) -> InterviewTurnResult:
        followup = await self._followups.generate(
            context,
            question,
            answer,
            evaluation.verdict,
            evaluation.score,
            evaluation.strategy,
            evaluation.notes,
        )
        session.follow_ups_used += 1
        session.state_machine.transition(InterviewState.FOLLOW_UP)
        session.current_question_text = followup.question
        session.current_difficulty = followup.difficulty

        text = followup.question
        self._append(session, "interviewer", text)
        await self._sessions.update(session)
        return self._result(
            session,
            InterviewState.FOLLOW_UP,
            text,
            question=question,
        )

    async def _advance(self, session: InterviewSession) -> InterviewTurnResult:
        """Move to the next dynamically planned question or to the final question."""
        machine = session.state_machine
        
        # We need at least 8 questions and 4 days. Let's aim for 10 if we can.
        questions_asked = session.plan.size
        days_covered = session.plan.distinct_days
        
        should_terminate = False
        if questions_asked >= 12:
            should_terminate = True
        elif questions_asked >= 8 and days_covered >= 4:
            # Random chance to stop between 8 and 12, or just stop
            should_terminate = True
            
        if should_terminate:
            machine.transition(InterviewState.NEXT_TOPIC)
            machine.transition(InterviewState.FINAL_QUESTION)
            text = self._prompts.final_question_message()
            self._append(session, "interviewer", text)
            await self._sessions.update(session)
            return self._result(session, InterviewState.FINAL_QUESTION, text)

        machine.transition(InterviewState.NEXT_TOPIC)
        machine.transition(InterviewState.QUESTIONING)
        return await self._ask_question(session, questions_asked, first=False)

    async def _finalize(self, session: InterviewSession) -> InterviewTurnResult:
        """Candidate replied to the final question -> feedback -> DONE."""
        # The reply to "any questions for us?" is conversational, not scored.
        session.state_machine.transition(InterviewState.EVALUATION)
        context = self._context.build(
            state=InterviewState.EVALUATION,
            candidate=session.profile,
            plan=session.plan,
            memory=session.memory,
            question_index=session.current_question_index,
        )
        session.feedback = await self._feedback_generator.generate(context)

        session.state_machine.transition(InterviewState.FEEDBACK)
        session.state_machine.transition(InterviewState.DONE)

        text = self._prompts.wrap_up_message(session.profile.name)
        self._append(session, "interviewer", text)
        await self._sessions.update(session)
        return self._final_result(session)

    # ------------------------------------------------------------------ helpers

    async def _ask_question(
        self,
        session: InterviewSession,
        index: int,
        *,
        first: bool,
    ) -> InterviewTurnResult:
        
        context = self._context.build(
            state=InterviewState.QUESTIONING,
            candidate=session.profile,
            plan=session.plan,
            memory=session.memory,
            question_index=index,
        )
        
        question = await self._planner.generate_next_question(
            context, session.profile, session.plan, index
        )
        
        session.plan.questions.append(question)
        if question.day_index not in session.plan.days_covered:
            session.plan.days_covered.append(question.day_index)
            
        session.current_question_index = index
        session.current_question_text = question.question
        session.current_difficulty = question.difficulty
        session.follow_ups_used = 0

        if first:
            text = self._prompts.first_question_bridge(
                session.profile.name, question.question
            )
        else:
            previous_topic = session.plan.questions[-2].topic if len(session.plan.questions) > 1 else "Unknown"
            # We must pass kwargs if the PromptBuilder supports it, but PromptBuilder in `_prompts.next_question_bridge` currently only takes 1 argument.
            # I will need to modify `PromptBuilder` to pass `previous_topic` and `next_topic`.
            text = self._prompts.next_question_bridge(question.question, previous_topic, question.topic)

        self._append(session, "interviewer", text)
        await self._sessions.update(session)
        return self._result(
            session, InterviewState.QUESTIONING, text, question=question
        )

    def _result(
        self,
        session: InterviewSession,
        state: InterviewState,
        text: str,
        *,
        question: PlannedQuestion | None = None,
        complete: bool = False,
        feedback: dict[str, Any] | None = None,
    ) -> InterviewTurnResult:
        # Avoid showing "Day X" since we are not going linearly day-by-day necessarily. 
        # But for UI to work we pass it back.
        total_q = max(session.plan.size, 8) 
        
        return InterviewTurnResult(
            session_id=session.session_id,
            state=state.value,
            message=text,
            question_number=session.current_question_index + 1,
            total_questions=total_q,
            current_day=question.day_title if question else None,
            current_topic=question.topic if question else None,
            interview_complete=complete,
            feedback=feedback,
        )

    def _final_result(self, session: InterviewSession) -> InterviewTurnResult:
        feedback = (
            session.feedback.to_api_payload() if session.feedback else None
        )
        total_q = max(session.plan.size, 8)
        return InterviewTurnResult(
            session_id=session.session_id,
            state=InterviewState.DONE.value,
            message=self._prompts.wrap_up_message(session.profile.name),
            question_number=session.current_question_index + 1,
            total_questions=total_q,
            current_day=None,
            current_topic=None,
            interview_complete=True,
            feedback=feedback,
        )

    @staticmethod
    def _append(
        session: InterviewSession, role: str, text: str
    ) -> None:
        session.transcript.append({"role": role, "text": text})
