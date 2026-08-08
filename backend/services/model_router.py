"""Quota-aware multi-model routing over the Groq model family.

One ``GROQ_API_KEY`` serves every model below.  The router picks ONE model
per call, weighing task fitness against live per-model quota, latency and
health, so:

* simple conversational turns use the fast models,
* medium reasoning uses the balanced/technical models,
* deep reasoning uses the 70B / 120B / compound models,
* security models *classify* candidate input — they never generate
  interviewer language.

Unlike a plain fallback chain, this router is **proactive**: each model's
usage (requests / tokens, minute and daily) is tracked against the limits
shown in the Groq account, and when a model approaches a limit the router
reduces its priority and shifts work to a suitable peer BEFORE the provider
returns 429.  A small reservation system keeps concurrent interview
sessions from oversubscribing one model.

Quotas are PER MODEL: a 429 on one model never blocks another, and the
router never serialises the whole fleet for a single turn.  The normal
path stays at one generation call per turn.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

#: Every supported model and its internal role.  ``security_only`` models
#: classify untrusted input; they are never asked to generate interviewer
#: text and never appear in a generation pool.
MODEL_REGISTRY: dict[str, dict] = {
    "llama-3.1-8b-instant": {"role": "fast_conversation"},
    "allam-2-7b": {"role": "lightweight_fallback"},
    "openai/gpt-oss-20b": {"role": "balanced_reasoning"},
    # Reasoning model: rejects ``response_format: json_object``, so JSON
    # mode is skipped and its JSON is extracted after stripping <think>.
    "qwen/qwen3.6-27b": {"role": "technical_reasoning", "json_mode": False},
    "groq/compound-mini": {"role": "fast_complex_reasoning"},
    "llama-3.3-70b-versatile": {"role": "deep_reasoning"},
    "openai/gpt-oss-120b": {"role": "advanced_reasoning"},
    "groq/compound": {"role": "complex_agentic"},
    "meta-llama/llama-prompt-guard-2-22m": {"role": "guard_light", "security_only": True},
    "meta-llama/llama-prompt-guard-2-86m": {"role": "guard_strong", "security_only": True},
    "openai/gpt-oss-safeguard-20b": {"role": "safeguard", "security_only": True},
}

#: Models that classify and must never generate interviewer language.
SECURITY_MODELS: set[str] = {
    model
    for model, meta in MODEL_REGISTRY.items()
    if meta.get("security_only")
}

#: Per-model quota limits exactly as shown in the Groq account table.
#: ``None`` means "no displayed limit" (unlimited).  These are runtime
#: configuration, not promises — a 429 from the provider always wins and is
#: recorded immediately.
MODEL_QUOTAS: dict[str, dict] = {
    "allam-2-7b": {"rpm": 30, "rpd": 7000, "tpm": 6000, "tpd": 500_000},
    "groq/compound": {"rpm": 30, "rpd": 250, "tpm": 70_000, "tpd": None},
    "groq/compound-mini": {"rpm": 30, "rpd": 250, "tpm": 70_000, "tpd": None},
    "llama-3.1-8b-instant": {"rpm": 30, "rpd": 14_400, "tpm": 6_000, "tpd": 500_000},
    "llama-3.3-70b-versatile": {"rpm": 30, "rpd": 1_000, "tpm": 12_000, "tpd": 100_000},
    "meta-llama/llama-prompt-guard-2-22m": {"rpm": 30, "rpd": 14_400, "tpm": 15_000, "tpd": 500_000},
    "meta-llama/llama-prompt-guard-2-86m": {"rpm": 30, "rpd": 14_400, "tpm": 15_000, "tpd": 500_000},
    "openai/gpt-oss-120b": {"rpm": 30, "rpd": 1_000, "tpm": 8_000, "tpd": 200_000},
    "openai/gpt-oss-20b": {"rpm": 30, "rpd": 1_000, "tpm": 8_000, "tpd": 200_000},
    "openai/gpt-oss-safeguard-20b": {"rpm": 30, "rpd": 1_000, "tpm": 8_000, "tpd": 200_000},
    "qwen/qwen3.6-27b": {"rpm": 30, "rpd": 1_000, "tpm": 8_000, "tpd": 200_000},
}


def quotas_for(model: str) -> dict:
    """Quota limits for a model; unknown models get conservative defaults."""
    return MODEL_QUOTAS.get(
        model, {"rpm": 30, "rpd": 1_000, "tpm": 6_000, "tpd": 200_000}
    )


#: Task pools — ordered by capability fitness; the weighted router re-ranks
#: this base order with live quota/latency/health signals.  The pools
#: encode the specialization the router is asked to provide:
#:
#: * ``simple``     — non-substantive follow-ups / transitions: fast first.
#: * ``medium``     — everyday evaluation & adaptation: balanced 20B first.
#: * ``strong``     — deep technical reasoning: 70B first.
#: * ``advanced``   — escalation tier: 120B / compound first.
#: * ``question``   — new-topic question generation: 70B leads (creative
#:   core), 20B / qwen as health-based alternates.
#: * ``feedback``   — final evidence-based feedback: 70B / 120B / qwen.
#: * guard pools    — security classification only.
TASK_POOLS: dict[str, tuple[str, ...]] = {
    "simple": (
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
    ),
    "medium": (
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ),
    "strong": (
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ),
    "advanced": (
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ),
    "question": (
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ),
    "feedback": (
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ),
    "guard_light": (
        "meta-llama/llama-prompt-guard-2-22m",
        "meta-llama/llama-prompt-guard-2-86m",
    ),
    "guard_strong": (
        "meta-llama/llama-prompt-guard-2-86m",
        "meta-llama/llama-prompt-guard-2-22m",
    ),
    "safeguard": (
        "openai/gpt-oss-safeguard-20b",
    ),
}

#: Words that hint at a *deeper* technical answer (longer than the medium
#: tier warrants).  Pure heuristics — the actual judgment still happens in
#: the model; this only picks which model does the judging.
_STRONG_HINTS = (
    "trade-off", "tradeoff", "architecture", "production", "scalab",
    "latency", "throughput", "caching", "rerank", "monitor", "deploy",
    "fault", "concurr", "distributed", "evaluation", "evals", "cost",
    "security", "guardrails", "fallback", "replicat", "sharding",
)

#: Follow-up strategies that stay on the cheap tier: the candidate did not
#: demonstrate depth, so a short, simpler probe needs no 70B reasoning.
_SIMPLE_FOLLOW_UP_MARKERS = (
    "- Follow-up strategy: simplify",
    "- Follow-up strategy: verify",
    "- Follow-up strategy: recovery",
)

#: Cooldown for hard failures (404 model not found, JSON validation) — a
#: broken model is not worth retrying for a while.
_HARD_FAIL_COOLDOWN_S = 300
#: Cooldown after repeated transient failures (503 / timeout / capacity).
_TRANSIENT_MAX_FAILURES = 2
_TRANSIENT_COOLDOWN_S = 120
#: Default rate-limit wait when the provider does not say how long.
_RATE_LIMIT_DEFAULT_S = 60

#: Usage-fraction at which a model is demoted for a limit (kept 20% in
#: reserve by default).  Overridden by Settings when the router is built.
_DEFAULT_USAGE_THRESHOLDS = {
    "tpm": 0.75,
    "tpd": 0.80,
    "rpm": 0.75,
    "rpd": 0.80,
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ModelHealth:
    """Per-model runtime health + quota — quotas are independent per model."""

    model: str
    available: bool = True
    consecutive_failures: int = 0
    success_rate: float = 1.0
    rate_limited_until: datetime | None = None
    cooldown_until: datetime | None = None
    recent_latency_ms: float = 0.0
    requests_estimate: int = 0
    tokens_estimate: int = 0
    last_error: str = ""

    # --- quota accounting (rolling windows) --------------------------------
    requests_this_minute: int = 0
    tokens_this_minute: int = 0
    requests_today: int = 0
    tokens_today: int = 0
    #: Tokens reserved by in-flight requests (not yet reconciled).
    pending_tokens: int = 0
    #: Minute/day window anchors — counters reset when these roll over.
    minute_key: int = 0
    day_key: date = field(default_factory=lambda: _now().date())
    #: Selection stats for diagnostics / load-balancing signal.
    selection_count: int = 0
    last_selected_at: datetime | None = None

    @property
    def healthy(self) -> bool:
        """True when the router may select this model right now."""
        if not self.available:
            return False
        if self.rate_limited_until and self.rate_limited_until > _now():
            return False
        if self.cooldown_until and self.cooldown_until > _now():
            return False
        return True

    # ------------------------------------------------------------------ quota

    def roll_windows(self) -> None:
        """Reset minute counters on the minute boundary, daily on date roll."""
        now = _now()
        minute = int(now.timestamp()) // 60
        if minute != self.minute_key:
            self.minute_key = minute
            self.requests_this_minute = 0
            self.tokens_this_minute = 0
        today = now.date()
        if today != self.day_key:
            self.day_key = today
            self.requests_today = 0
            self.tokens_today = 0

    def usage_fractions(self) -> dict[str, float]:
        """Current usage as a fraction of each limit (0 = none, 1 = full)."""
        q = quotas_for(self.model)
        self.roll_windows()
        return {
            "tpm": self.tokens_this_minute / q["tpm"] if q["tpm"] else 0.0,
            "tpd": (
                self.tokens_today / q["tpd"]
                if q.get("tpd")
                else 0.0
            ),
            "rpm": self.requests_this_minute / q["rpm"] if q["rpm"] else 0.0,
            "rpd": self.requests_today / q["rpd"] if q["rpd"] else 0.0,
        }

    def max_usage_fraction(self) -> float:
        """Worst (highest) usage across all limits — the binding constraint."""
        fracs = self.usage_fractions()
        return max(fracs.values()) if fracs else 0.0

    def quota_state(self, thresholds: dict[str, float] | None = None) -> str:
        """One of AVAILABLE / HEALTHY / BUSY / NEAR_*_LIMIT / RATE_LIMITED /
        COOLDOWN / DAILY_EXHAUSTED / UNAVAILABLE."""
        if not self.available:
            return "UNAVAILABLE"
        if self.rate_limited_until and self.rate_limited_until > _now():
            return "RATE_LIMITED"
        if self.cooldown_until and self.cooldown_until > _now():
            return "COOLDOWN"
        thr = thresholds or _DEFAULT_USAGE_THRESHOLDS
        fracs = self.usage_fractions()
        if (
            (q := quotas_for(self.model).get("tpd"))
            and fracs["tpd"] >= 1.0
        ):
            return "DAILY_EXHAUSTED"
        near: list[str] = []
        for key in ("tpm", "tpd", "rpm", "rpd"):
            if fracs[key] >= thr.get(key, 0.8):
                near.append(key.upper())
        if near:
            return "NEAR_" + "_".join(near)
        if self.selection_count == 0:
            return "AVAILABLE"
        if self.max_usage_fraction() > 0.5:
            return "BUSY"
        return "HEALTHY"


class ModelHealthTracker:
    """Independent per-model state: a 429 on one model never blocks another.
    Also performs quota reservation so concurrent sessions cannot
    oversubscribe a single model's TPM/TPD window."""

    def __init__(
        self,
        usage_thresholds: dict[str, float] | None = None,
    ) -> None:
        self._states: dict[str, ModelHealth] = {
            model: ModelHealth(model=model) for model in MODEL_REGISTRY
        }
        self._thresholds = dict(_DEFAULT_USAGE_THRESHOLDS)
        if usage_thresholds:
            self._thresholds.update(
                {k: v for k, v in usage_thresholds.items() if v is not None}
            )

    @property
    def usage_thresholds(self) -> dict[str, float]:
        return dict(self._thresholds)

    def get(self, model: str) -> ModelHealth:
        return self._states.setdefault(model, ModelHealth(model=model))

    def healthy(self, model: str) -> bool:
        return self.get(model).healthy

    def record_success(self, model: str, latency_ms: float, tokens: int) -> None:
        """Health bookkeeping after a successful call.

        Window counters (requests/tokens, minute/day) are updated by
        ``reconcile_capacity`` so usage is never double-counted — this
        method only refreshes health signals.
        """
        state = self.get(model)
        state.roll_windows()
        state.consecutive_failures = 0
        state.available = True
        state.rate_limited_until = None
        state.cooldown_until = None
        state.last_error = ""
        # Exponentially-weighted moving average for recent latency.
        if state.recent_latency_ms <= 0:
            state.recent_latency_ms = latency_ms
        else:
            state.recent_latency_ms = (
                0.7 * state.recent_latency_ms + 0.3 * latency_ms
            )
        state.success_rate = min(
            1.0, state.success_rate * 0.95 + 0.05
        )
        state.requests_estimate += 1
        state.tokens_estimate += tokens
        state.selection_count += 1
        state.last_selected_at = _now()

    def record_rate_limited(
        self, model: str, retry_after_s: float | None = None
    ) -> None:
        """Mark a model rate-limited.  Only that model is blocked — the rest
        of the fleet stays available (independent quotas)."""
        state = self.get(model)
        state.roll_windows()
        wait = (
            retry_after_s
            if retry_after_s and retry_after_s > 0
            else _RATE_LIMIT_DEFAULT_S
        )
        state.rate_limited_until = _now() + timedelta(seconds=wait)
        state.last_error = "rate_limited"

    def record_failure(self, model: str, error: str, *, hard: bool) -> None:
        """Record a failed call.  ``hard`` failures (404 / JSON) cool the
        model down after a single occurrence; transient failures need a few
        in a row before the model is taken out of rotation."""
        state = self.get(model)
        state.roll_windows()
        state.consecutive_failures += 1
        state.last_error = error[:160]
        state.success_rate = max(
            0.0, state.success_rate * 0.95
        )
        if hard:
            state.cooldown_until = _now() + timedelta(
                seconds=_HARD_FAIL_COOLDOWN_S
            )
            state.available = True  # a 404 is model-specific, not service-wide
        elif state.consecutive_failures >= _TRANSIENT_MAX_FAILURES:
            state.cooldown_until = _now() + timedelta(
                seconds=_TRANSIENT_COOLDOWN_S
            )

    # ---------------------------------------------------------------- reserve

    def reserve_capacity(self, model: str, estimated_tokens: int) -> bool:
        """Atomically reserve estimated tokens on a model BEFORE the call.

        Fails (returns False) when the model is unhealthy or when reserving
        would push the TPM or TPD window past its limit — in which case the
        caller picks another model without making the request.  Called from
        async code with no await between check and increment, so it is
        race-free within the event loop.
        """
        if estimated_tokens <= 0:
            return True
        state = self.get(model)
        state.roll_windows()
        if not state.healthy:
            return False
        q = quotas_for(model)
        remaining_tpm = q["tpm"] - state.tokens_this_minute - state.pending_tokens
        if q.get("tpd") is not None:
            remaining_tpd = (
                q["tpd"] - state.tokens_today - state.pending_tokens
            )
        else:
            remaining_tpd = math.inf
        if estimated_tokens > remaining_tpm or estimated_tokens > remaining_tpd:
            return False
        state.pending_tokens += estimated_tokens
        return True

    def reconcile_capacity(
        self, model: str, estimated_tokens: int, actual_tokens: int
    ) -> None:
        """After a successful call: release the reservation and record actual
        usage (actual tokens reported by the provider estimate) plus one
        request against the RPM/RPD windows."""
        state = self.get(model)
        state.roll_windows()
        state.pending_tokens = max(0, state.pending_tokens - estimated_tokens)
        state.tokens_this_minute += actual_tokens
        state.tokens_today += actual_tokens
        state.requests_this_minute += 1
        state.requests_today += 1

    def release_reservation(self, model: str, estimated_tokens: int) -> None:
        """After a failed call: give the reserved tokens back."""
        state = self.get(model)
        state.pending_tokens = max(0, state.pending_tokens - estimated_tokens)

    # -------------------------------------------------------------- simulate

    def simulate_usage(
        self,
        model: str,
        *,
        tpm_pct: float = 0.0,
        tpd_pct: float = 0.0,
        rpm_pct: float = 0.0,
        rpd_pct: float = 0.0,
    ) -> None:
        """Set usage levels directly (test/diagnostic mode only) so the
        load-balancing behaviour can be verified without burning real quota.
        Percentages are 0..1 fractions of the model's limits."""
        state = self.get(model)
        state.roll_windows()
        q = quotas_for(model)
        state.tokens_this_minute = int(q["tpm"] * tpm_pct)
        state.tokens_today = int((q.get("tpd") or 0) * tpd_pct)
        state.requests_this_minute = int(q["rpm"] * rpm_pct)
        state.requests_today = int(q["rpd"] * rpd_pct)

    # ------------------------------------------------------------- diagnostics

    def summary(self) -> dict[str, dict]:
        """Compact health + quota snapshot for logs / debugging (no secrets)."""
        out: dict[str, dict] = {}
        for model, state in self._states.items():
            state.roll_windows()
            q = quotas_for(model)
            fracs = state.usage_fractions()
            out[model] = {
                "healthy": state.healthy,
                "quota_state": state.quota_state(self._thresholds),
                "failures": state.consecutive_failures,
                "latency_ms": round(state.recent_latency_ms, 1),
                "rate_limited": bool(
                    state.rate_limited_until and state.rate_limited_until > _now()
                ),
                "tpm_used": state.tokens_this_minute,
                "tpm_limit": q["tpm"],
                "tpm_pct": round(fracs["tpm"], 3),
                "tpd_used": state.tokens_today,
                "tpd_limit": q.get("tpd"),
                "tpd_pct": round(fracs["tpd"], 3),
                "rpm_used": state.requests_this_minute,
                "rpd_used": state.requests_today,
                "selection_count": state.selection_count,
                "pending_tokens": state.pending_tokens,
            }
        return out


def estimate_answer_complexity(answer: str) -> str:
    """Deterministic complexity tier for a substantive candidate answer.

    ``simple`` → too short / non-substantive (should normally have been
    classified before reaching the router); ``medium`` → everyday technical
    answer; ``strong`` → long or architecture/trade-off-flavoured answer.
    """
    if not answer or len(answer.strip()) < 20:
        return "simple"
    lower = answer.lower()
    if len(answer) >= 240 or any(hint in lower for hint in _STRONG_HINTS):
        return "strong"
    return "medium"


def task_for_call(call_type: str, user_prompt: str) -> str:
    """Map an LLM call to the router task pool, using the prompt itself
    (the same markers the mock provider dispatches on)."""
    if call_type == "follow_up":
        if any(marker in user_prompt for marker in _SIMPLE_FOLLOW_UP_MARKERS):
            return "simple"
        return "strong"  # deeper follow-ups on demonstrated depth
    if call_type == "evaluate":
        # Evaluating an answer is always a judgment call — the deterministic
        # fast path already handled "I don't know"-style non-answers, so an
        # evaluation never drops to the cheapest tier.  Long / architecture-
        # flavoured answers escalate to the strong pool.
        answer = _extract_answer(user_prompt)
        tier = estimate_answer_complexity(answer)
        return "strong" if tier == "strong" else "medium"
    if call_type == "question":
        return "question"
    if call_type == "feedback":
        return "feedback"
    return "strong"


def _extract_answer(user_prompt: str) -> str:
    match = re.search(
        r"CANDIDATE'S ANSWER\n(.*?)\n\n(?:CANDIDATE PROFILE|EVALUATION|CURRICULUM)",
        user_prompt,
        re.DOTALL,
    )
    if not match:
        match = re.search(r"CANDIDATE'S ANSWER\n(.*)$", user_prompt, re.DOTALL)
    return match.group(1).strip() if match else ""


#: Weighting of the router's selection score.  Capability (task fitness)
#: dominates; quota headroom and load balance decide among suitable peers.
_W_CAPABILITY = 0.40
_W_QUOTA = 0.30
_W_LATENCY = 0.10
_W_HEALTH = 0.10
_W_BALANCE = 0.10


class ModelRouter:
    """Selects the single best model for a task given live health + quota.

    ``ordered_candidates`` returns the task pool re-ranked by a weighted
    score (capability + quota headroom + latency + health + load balance)
    so traffic naturally spreads across suitable models and shifts away
    from a model approaching its limits — without waiting for a 429.
    """

    def __init__(
        self,
        tracker: ModelHealthTracker,
        fast_model_override: str | None = None,
    ) -> None:
        self._tracker = tracker
        self._fast_override = fast_model_override

    # ---------------------------------------------------------------- scoring

    def _score(self, model: str, pool: tuple[str, ...]) -> float:
        """Weighted suitability score for ``model`` within ``pool``."""
        state = self._tracker.get(model)
        try:
            rank = pool.index(model)
        except ValueError:
            rank = len(pool)  # outside the pool -> worst capability

        # Capability: earlier pool position = better task fit.
        capability = (len(pool) - rank) / max(1, len(pool))

        # Quota headroom: full marks while comfortably below the switch
        # threshold; decisive demotion once a limit is approached.
        fracs = state.usage_fractions()
        thresholds = self._tracker.usage_thresholds
        worst = 0.0
        for key, frac in fracs.items():
            thr = thresholds.get(key, 0.8)
            if frac >= thr:
                worst = max(worst, frac)
        if worst >= 0.5:
            quota = max(0.0, 1.0 - worst)
        else:
            quota = 1.0

        # Latency: faster is better (1.0 for no data yet).
        latency_ms = state.recent_latency_ms
        latency = 1.0 if latency_ms <= 0 else max(0.0, 1.0 - latency_ms / 5000.0)

        # Health: full marks when healthy, otherwise heavily penalised.
        health = 1.0 if state.healthy else 0.1

        # Load balance: prefer the less-used suitable peer.
        usage = state.max_usage_fraction()
        balance = 1.0 - min(1.0, usage)

        return (
            _W_CAPABILITY * capability
            + _W_QUOTA * quota
            + _W_LATENCY * latency
            + _W_HEALTH * health
            + _W_BALANCE * balance
        )

    # ----------------------------------------------------------------- public

    def ordered_candidates(
        self,
        task: str,
        *,
        preferred: str | None = None,
    ) -> tuple[tuple[str, ...], str]:
        """Return (candidates, routing_reason) for ``task``.

        The task pool is re-ranked by the weighted score; unhealthy models
        are excluded (the full pool returns only as a best-effort last
        resort).  The session's current model is kept first when it is
        healthy AND fits the task (conversational continuity without
        sacrificing fitness).
        """
        pool = TASK_POOLS.get(task, TASK_POOLS["strong"])
        if task == "simple" and self._fast_override:
            pool = (self._fast_override,) + tuple(
                m for m in pool if m != self._fast_override
            )

        healthy = [m for m in pool if self._tracker.healthy(m)]
        if preferred and preferred in healthy:
            index = pool.index(preferred)
            # Only keep continuity when the preferred model is a *fits the
            # task* choice (first half of the pool), so a 70B session does
            # not drag 70B into cheap simple turns.
            if index < max(1, len(pool) // 2 + 1):
                healthy.remove(preferred)
                healthy.insert(0, preferred)

        if not healthy:
            healthy = list(pool)
            reason = f"task={task} pool-exhausted (all unhealthy) — best effort"
        else:
            # Weighted re-rank: capability leads, quota/latency/health/load
            # decide among suitable peers.
            healthy.sort(key=lambda m: self._score(m, pool), reverse=True)
            reason = f"task={task} preferred={preferred or 'none'}"

        return tuple(healthy), reason
