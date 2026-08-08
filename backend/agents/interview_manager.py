"""Interview manager.

The orchestrator of the whole interview.  It owns the state machine and
decides, for every candidate message, which agent runs next and which state
the conversation moves into.

Turn protocol
-------------
The candidate sends a message in every turn; the server replies with the
interviewer's next utterance.  State is carried entirely by ``sessionId``
(the id the client supplied when starting the interview, per the spec).

    START -> INTRODUCTION -> QUESTIONING -> FOLLOW_UP <-> ... -> FINAL_QUESTION
                                                             -> EVALUATION
                                                             -> FEEDBACK
                                                             -> DONE

Completion is a *hard* engine decision, never an LLM suggestion: the
interview may only move to the final question once at least
``min_questions`` main questions were asked **and** at least ``min_days``
distinct curriculum days were covered.
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
from models.enums import FollowUpStrategy, Verdict
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
        """Spec-shaped payload: ``reply`` and ``done`` plus UI extras."""
        return {
            "reply": self.message,
            "done": self.interview_complete,
            "sessionId": self.session_id,
            "state": self.state,
            "questionNumber": self.question_number,
            "totalQuestions": self.total_questions,
            "currentDay": self.current_day,
            "currentTopic": self.current_topic,
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
        self,
        candidate_id: str,
        first_message: str,
        session_id: str | None = None,
    ) -> InterviewSession:
        """Create a session: analyze candidate, build the plan skeleton.

        ``session_id`` is the client-supplied id from the spec's start
        request; when omitted the server generates one.
        """
        raw = self._candidates.get(candidate_id)
        profile = self._analyzer.analyze(raw)
        plan = self._planner.build_plan(profile)

        session = InterviewSession(
            session_id=session_id or self._sessions.new_session_id(),
            candidate_id=candidate_id,
            profile=profile,
            plan=plan,
            memory=ConversationMemory(
                max_history_turns=self._settings.max_history_turns
            ),
        )
        await self._sessions.create(session)
        logger.info(
            "Session %s started for candidate %s (%s, %s)",
            session.session_id,
            candidate_id,
            profile.name,
            profile.role,
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
            return await self._begin(session)
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

    async def _begin(self, session: InterviewSession) -> InterviewTurnResult:
        session.state_machine.transition(InterviewState.INTRODUCTION)
        # The first reply doubles as the greeting + first question: a
        # personalized, contextual opening rather than a scripted intro.
        return await self._after_intro(session)

    async def _after_intro(self, session: InterviewSession) -> InterviewTurnResult:
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
        # Context retention: remember curriculum concepts the candidate
        # raised so later questions can reference their own words.
        mentions = self._retriever.find_mentions(message)
        if mentions:
            session.memory.add_mentions(mentions)
        session.last_question_day = question.day_index

        # --- decide: follow-up or move on --------------------------------
        # Evidence-driven follow-up budget: never more than the configured
        # per-question cap, and never once the topic is saturated (main +
        # follow-ups >= 3) — the interviewer stops probing a topic once it
        # has enough evidence and moves on.
        topic_assessment = context.plan.assessment.get_topic(question.topic)
        # Exception: a bare knowledge claim always gets its ONE verification
        # probe, even on an otherwise saturated topic (per the interview
        # rules "I know" is never accepted at face value).  A second claim
        # on the same topic still moves on.
        claim_verify = (
            evaluation.strategy == FollowUpStrategy.VERIFY
            and topic_assessment.bare_claims <= 1
        )
        wants_follow_up = evaluation.wants_follow_up and (
            session.follow_ups_used < self._settings.max_follow_ups_per_question
            and (not topic_assessment.saturated or claim_verify)
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
        # Track follow-up count on the topic assessment.
        context.plan.assessment.get_topic(question.topic).follow_ups += 1

        text = followup.question
        self._append(session, "interviewer", text)
        await self._sessions.update(session)
        return self._result(
            session,
            InterviewState.FOLLOW_UP,
            text,
            question=question,
        )

    def _coverage(self, session: InterviewSession) -> tuple[int, int]:
        """(main questions asked, distinct curriculum days covered)."""
        questions = session.plan.questions
        main_asked = len(questions)
        days = len({q.day_index for q in questions})
        return main_asked, days

    def _should_terminate(self, session: InterviewSession) -> bool:
        """Evidence-based completion gate.

        The hard minimums — 8+ ACTUAL interviewer questions (main questions
        AND follow-ups: per the interview rules a follow-up is also a
        question) across 4+ distinct curriculum days — are enforced by the
        engine, never by an LLM marker.  Once the minimums are met the
        interview ends when one of:

        * the soft budget (``total_questions``, 10 actual) is reached,
        * the absolute ceiling (``max_questions``, 12 actual) is hit, or
        * every topic that was asked about has a *settled* assessment —
          evidence is sufficient, so a decisive interview is not extended
          artificially.

        If the minimums are never met the interview keeps going until the
        main-question safety cap (12 mains — which already spans at least
        6 days), so an interview can never finish starved of coverage.
        """
        main_asked, days = self._coverage(session)
        follow_ups_asked = sum(
            assessment.follow_ups
            for assessment in session.plan.assessment.topics.values()
        )
        total_asked = main_asked + follow_ups_asked
        soft_target = self._settings.total_questions
        hard_cap = self._settings.max_questions

        # Main-question safety cap: 12 mains always ends the interview
        # (with the planner's 2-mains-per-day limit this already spans at
        # least 6 days, so it can never end below the 4-day minimum).
        if main_asked >= hard_cap:
            logger.warning(
                "Hard cap %d reached (mains=%d total=%d days=%d) — ending "
                "interview",
                hard_cap,
                main_asked,
                total_asked,
                days,
            )
            return True
        if not (
            total_asked >= self._settings.min_questions
            and days >= self._settings.min_days
        ):
            return False
        # The 12-question ceiling applies to ACTUAL questions shown (mains
        # + follow-ups), so a follow-up-dense interview cannot exceed it.
        if total_asked >= hard_cap:
            logger.warning(
                "Hard cap %d reached (total=%d days=%d) — ending interview",
                hard_cap,
                total_asked,
                days,
            )
            return True
        # Soft budget on ACTUAL questions: the usual 8-10 finish line.
        if total_asked >= soft_target:
            return True

        # Evidence-based early finish: every touched topic has a *settled*
        # assessment.  A topic is settled when either
        #
        # * it was exhausted — repeated failures or bare claims, so the
        #   interviewer already moved on and no further evidence is coming
        #   (an all-"I don't know" candidate must not be dragged past the
        #   minimum with topic revisits), or
        # * strong evidence was demonstrated (best score >= 7 with a
        #   medium/high confidence) and no failure/claim is open.
        #
        # Anything else — a mid-topic failure, an unverified claim, a
        # shallow (6/10) answer the interviewer would still probe, or an
        # unknown with no evidence — keeps the interview going.
        touched = [
            assessment
            for assessment in session.plan.assessment.topics.values()
            if assessment.touched
        ]
        if touched and all(
            assessment.consecutive_failures >= 2
            or assessment.bare_claims >= 2
            or (
                assessment.best_score >= 7
                and assessment.confidence in ("medium", "high")
                and assessment.consecutive_failures == 0
                and assessment.bare_claims == 0
            )
            for assessment in touched
        ):
            logger.info(
                "Evidence sufficient at %d questions / %d days — ending "
                "interview early",
                main_asked,
                days,
            )
            return True
        return False

    async def _advance(self, session: InterviewSession) -> InterviewTurnResult:
        """Move to the next dynamically planned question or wrap up."""
        machine = session.state_machine

        if self._should_terminate(session):
            machine.transition(InterviewState.NEXT_TOPIC)
            machine.transition(InterviewState.FINAL_QUESTION)
            text = self._prompts.final_question_message()
            self._append(session, "interviewer", text)
            await self._sessions.update(session)
            return self._result(session, InterviewState.FINAL_QUESTION, text)

        machine.transition(InterviewState.NEXT_TOPIC)
        machine.transition(InterviewState.QUESTIONING)
        return await self._ask_question(session, len(session.plan.questions), first=False)

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
            previous_question = (
                session.plan.questions[-2]
                if len(session.plan.questions) > 1
                else None
            )
            previous_topic = previous_question.topic if previous_question else ""
            last_turn = session.memory.last()
            # Emotional trajectory: the more consecutive weak / bare-claim
            # answers, the firmer the interviewer's reaction; a good answer
            # on a topic the candidate previously struggled with is a
            # recovery the interviewer acknowledges.
            consecutive_weak = session.memory.consecutive_weak
            recovered = session.memory.recovered
            related = bool(
                previous_question is not None
                and self._retriever.are_adjacent_days(
                    previous_question.day_index, question.day_index
                )
            )
            # The reaction is LLM-generated and content-aware (it references
            # what the candidate actually said); the deterministic pools are
            # only a fallback when it is empty or canned.  When a reaction
            # exists it carries the bridge, so no deterministic transition is
            # prepended on top of it.
            reaction = self._prompts.reaction_or_fallback(
                question.reaction,
                topic=question.topic,
                index=index,
                last_verdict=last_turn.verdict.value if last_turn else None,
                consecutive_weak=consecutive_weak,
                recovered=recovered,
            )
            if reaction:
                text = f"{reaction} {question.question}"
            else:
                text = self._prompts.next_question_bridge(
                    question.question,
                    previous_topic,
                    question.topic,
                    index=index,
                    last_verdict=last_turn.verdict.value if last_turn else None,
                    related=related,
                    same_topic=previous_topic == question.topic,
                    consecutive_weak=consecutive_weak,
                    recovered=recovered,
                )

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
        # The reported question number is the ACTUAL number of interviewer
        # questions asked so far — main questions AND follow-ups, plus the
        # one just asked — so the counter never understates the
        # conversation.  The total is only a floor for the progress UI.
        question_number = session.memory.count + 1
        total_q = max(question_number, self._settings.min_questions)
        return InterviewTurnResult(
            session_id=session.session_id,
            state=state.value,
            message=text,
            question_number=question_number,
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
        # Actual interviewer questions asked: mains + follow-ups (the
        # closing "any questions" turn is conversational, not scored).
        questions_asked = session.memory.count
        total_q = max(questions_asked, self._settings.min_questions)
        return InterviewTurnResult(
            session_id=session.session_id,
            state=InterviewState.DONE.value,
            message=self._prompts.wrap_up_message(session.profile.name),
            question_number=questions_asked,
            total_questions=total_q,
            current_day=None,
            current_topic=None,
            interview_complete=True,
            feedback=feedback,
        )

    @staticmethod
    def _append(session: InterviewSession, role: str, text: str) -> None:
        session.transcript.append({"role": role, "text": text})
