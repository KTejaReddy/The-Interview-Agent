"""Question planner.

Builds the interview plan dynamically based on the candidate's evolving assessment.
"""
from __future__ import annotations

import random

from agents.difficulty_manager import DifficultyManager
from memory.context_manager import InterviewContext
from models.candidate_profile import CandidateProfile
from models.enums import Difficulty, QuestionType
from models.plan import InterviewPlan, PlannedQuestion, AssessmentState
from retrieval.curriculum_retriever import CurriculumRetriever
from schemas.llm import QuestionDraft
from services.llm_service import LLMService
from services.prompt_builder import PromptBuilder
from utils.logging import get_logger

logger = get_logger(__name__)

_ALL_QUESTION_TYPES = list(QuestionType)


class QuestionPlanner:
    """Determines the next topic dynamically and generates question text."""

    def __init__(
        self,
        llm: LLMService,
        prompts: PromptBuilder,
        retriever: CurriculumRetriever,
        *,
        min_questions: int = 8,
        min_days: int = 4,
        total_questions: int = 12,
        difficulty_manager: DifficultyManager | None = None,
    ) -> None:
        self._llm = llm
        self._prompts = prompts
        self._retriever = retriever
        self._min_questions = min_questions
        self._min_days = min_days
        self._total_questions = total_questions
        self._difficulty = difficulty_manager or DifficultyManager()

    def build_plan(self, profile: CandidateProfile) -> InterviewPlan:
        """Initialize an empty dynamic plan skeleton."""
        if not self._retriever.available:
            from utils.errors import CurriculumUnavailableError

            raise CurriculumUnavailableError(
                "curriculum.json is unavailable — cannot plan the interview. "
                "Place the dataset in the configured data directory."
            )

        return InterviewPlan()
        
    async def generate_next_question(
        self,
        context: InterviewContext,
        profile: CandidateProfile,
        plan: InterviewPlan,
        index: int,
    ) -> PlannedQuestion:
        """Determine the next best topic and generate a question."""
        
        day_index, topic = self._determine_next_topic(profile, plan)
        
        # Difficulty adjusts dynamically based on the assessment for this topic
        baseline = profile.baseline_difficulty
        difficulty = self._difficulty.question_difficulty(
            baseline, index, self._total_questions
        )
        
        # Adjust difficulty based on assessment state
        topic_assessment = plan.assessment.get_topic(topic)
        if topic_assessment.consecutive_failures > 0 or topic_assessment.confidence == "low":
            if difficulty == Difficulty.ADVANCED:
                difficulty = Difficulty.MEDIUM
            elif difficulty == Difficulty.MEDIUM:
                difficulty = Difficulty.EASY
        elif topic_assessment.confidence == "high":
            if difficulty == Difficulty.EASY:
                difficulty = Difficulty.MEDIUM
            elif difficulty == Difficulty.MEDIUM:
                difficulty = Difficulty.ADVANCED

        question_type = self._next_type(_ALL_QUESTION_TYPES, plan, index)
        
        curriculum = self._retriever.ground_context(day_index)
        
        prompt = self._prompts.question_prompt(
            context,
            topic=topic,
            question_type=question_type.value,
            difficulty=difficulty.value,
            curriculum=curriculum,
        )
        
        draft = await self._llm.structured_completion(
            system_prompt=self._prompts.system_prompt(),
            user_prompt=prompt,
            schema=QuestionDraft,
        )
        
        day_title = f"Day {day_index + 1}"
        day_obj = self._retriever.get_day(day_index)
        if day_obj:
            day_title = day_obj.title
            
        entry = PlannedQuestion(
            day_index=day_index,
            day_title=day_title,
            topic=draft.topic or topic,
            question_type=question_type,
            difficulty=difficulty,
            question=draft.question,
            intent=draft.intent
        )
        
        return entry

    def _determine_next_topic(self, profile: CandidateProfile, plan: InterviewPlan) -> tuple[int, str]:
        """Find the best next topic based on profile and assessment state."""
        # 1. Prefer completed missions/topics
        completed_topics = profile.strong_topics + profile.knowledge_gaps + profile.weak_topics
        
        # 2. Prefer topics we haven't asked about yet, or topics we need more signal on
        asked_topics = {q.topic for q in plan.questions}
        
        # 3. Prefer days we haven't covered if we need to reach min_days
        days_covered = set(plan.days_covered)
        need_new_day = len(days_covered) < self._min_days
        
        candidates = []
        for day_index in range(self._retriever.day_count):
            day = self._retriever.get_day(day_index)
            if not day:
                continue
                
            for topic in day.topics:
                if topic in asked_topics:
                    # If we already assessed this and confidence is known, skip it
                    assessment = plan.assessment.get_topic(topic)
                    if assessment.confidence != "unknown" or assessment.consecutive_failures >= 2:
                        continue
                
                # Score the topic
                score = 0
                if topic in completed_topics:
                    score += 10
                    
                if need_new_day and day_index not in days_covered:
                    score += 5
                elif not need_new_day and day_index in days_covered:
                    # Prefer staying on same day to connect topics if we don't need a new day
                    score += 5
                    
                if len(plan.questions) > 0 and plan.questions[-1].day_index == day_index:
                    score += 3 # Slight bonus for related topics
                
                candidates.append((score, day_index, topic))
                
        if not candidates:
            # Fallback to random unseen
            for day_index in range(self._retriever.day_count):
                day = self._retriever.get_day(day_index)
                if not day: continue
                for topic in day.topics:
                    if topic not in asked_topics:
                        candidates.append((1, day_index, topic))
                        
        if not candidates:
            # Absolute fallback
            return 0, "General Concepts"
            
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1], candidates[0][2]

    def _next_type(self, pool: list[QuestionType], plan: InterviewPlan, index: int) -> QuestionType:
        """Rotate styles, never repeating the previous type."""
        previous = plan.questions[-1].question_type if plan.questions else None
        
        if index % len(pool) == 0:
            random.shuffle(pool)
            
        for candidate in pool:
            if candidate != previous:
                return candidate
                
        return pool[0]
