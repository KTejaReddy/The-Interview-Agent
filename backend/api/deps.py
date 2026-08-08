"""Dependency injection.

Constructs the full object graph once and exposes FastAPI dependencies so
routes never instantiate services themselves.  The graph lives on
``app.state`` and is built during application startup (lifespan).
"""
from __future__ import annotations

from typing import Any

from agents.candidate_analyzer import CandidateAnalyzer
from agents.difficulty_manager import DifficultyManager
from agents.feedback_generator import FeedbackGenerator
from agents.followup_generator import FollowUpGenerator
from agents.interview_manager import InterviewManager
from agents.question_planner import QuestionPlanner
from agents.response_evaluator import ResponseEvaluator
from agents.security_guard import SecurityGuard
from config import Settings
from memory.context_manager import ContextManager
from retrieval.candidate_loader import CandidateLoader
from retrieval.curriculum_loader import CurriculumLoader
from retrieval.curriculum_retriever import CurriculumRetriever
from retrieval.technical_spec_loader import TechnicalSpecLoader
from services.llm_service import LLMService
from services.prompt_builder import PromptBuilder
from services.session_manager import SessionManager


class Container:
    """Composes every dependency exactly once."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        # --- retrieval -----------------------------------------------------
        self.candidate_loader = CandidateLoader(settings.data_dir)
        self.curriculum_loader = CurriculumLoader(settings.data_dir)
        self.spec_loader = TechnicalSpecLoader(settings.data_dir)
        self.curriculum_retriever = CurriculumRetriever(self.curriculum_loader)

        # --- services ------------------------------------------------------
        self.llm = LLMService(settings)
        self.prompts = PromptBuilder(settings)
        self.sessions = SessionManager(settings)

        # --- agents ----------------------------------------------------------
        self.difficulty = DifficultyManager()
        self.analyzer = CandidateAnalyzer()
        self.planner = QuestionPlanner(
            self.llm,
            self.prompts,
            self.curriculum_retriever,
            min_questions=settings.min_questions,
            min_days=settings.min_days,
            total_questions=settings.total_questions,
            difficulty_manager=self.difficulty,
        )
        self.evaluator = ResponseEvaluator(self.llm, self.prompts)
        self.followups = FollowUpGenerator(
            self.llm, self.prompts, self.curriculum_retriever,
            difficulty_manager=self.difficulty,
        )
        self.feedback_generator = FeedbackGenerator(self.llm, self.prompts)
        self.context = ContextManager(
            transcript_window=settings.transcript_window
        )
        self.security_guard = SecurityGuard(self.llm, self.prompts)
        self.manager = InterviewManager(
            settings,
            self.sessions,
            self.llm,
            self.prompts,
            self.curriculum_retriever,
            self.candidate_loader,
            self.analyzer,
            self.planner,
            self.evaluator,
            self.followups,
            self.feedback_generator,
            self.context,
            self.security_guard,
        )

    def load_datasets(self) -> None:
        """Load the three datasets on startup (read-only)."""
        self.curriculum_loader.load()
        self.candidate_loader.load()
        self.spec_loader.load()

    async def shutdown(self) -> None:
        """Release resources."""
        await self.llm.close()

    def as_dict(self) -> dict[str, Any]:
        """Expose resolved services for route dependencies."""
        return {
            "manager": self.manager,
            "sessions": self.sessions,
            "candidate_loader": self.candidate_loader,
            "curriculum_retriever": self.curriculum_retriever,
            "spec_loader": self.spec_loader,
            "settings": self.settings,
            "llm": self.llm,
        }
