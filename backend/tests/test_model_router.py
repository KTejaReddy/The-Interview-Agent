"""Tests for the intelligent model router and per-model health tracking."""

from __future__ import annotations

from services.model_router import (
    MODEL_QUOTAS,
    MODEL_REGISTRY,
    ModelHealthTracker,
    ModelRouter,
    SECURITY_MODELS,
    TASK_POOLS,
    estimate_answer_complexity,
    task_for_call,
)


def test_registry_contains_all_eleven_models() -> None:
    """All supplied model identifiers are supported (exact names)."""
    expected = {
        "allam-2-7b",
        "groq/compound",
        "groq/compound-mini",
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        "meta-llama/llama-prompt-guard-2-22m",
        "meta-llama/llama-prompt-guard-2-86m",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "openai/gpt-oss-safeguard-20b",
        "qwen/qwen3.6-27b",
    }
    assert set(MODEL_REGISTRY) == expected


def test_security_models_never_generate() -> None:
    """Guard/safeguard models are security-only: they never appear in a
    generation pool, only in the dedicated guard pools."""
    generation_models = {
        model
        for pool in TASK_POOLS.values()
        if not pool[0].startswith("meta-llama/llama-prompt-guard")
        and pool[0] != "openai/gpt-oss-safeguard-20b"
        for model in pool
    }
    assert not (generation_models & SECURITY_MODELS)
    # Every security model exists in exactly one guard-style pool.
    guard_models = set()
    for name, pool in TASK_POOLS.items():
        if name in ("guard_light", "guard_strong", "safeguard"):
            guard_models |= set(pool)
    assert guard_models == SECURITY_MODELS


def test_router_selects_by_task_preference() -> None:
    """The first healthy model of the task pool wins — no randomness, no
    full-fleet serialisation."""
    tracker = ModelHealthTracker()
    router = ModelRouter(tracker)

    candidates, _ = router.ordered_candidates("simple")
    assert candidates[0] == TASK_POOLS["simple"][0] == "llama-3.1-8b-instant"

    candidates, _ = router.ordered_candidates("medium")
    assert candidates[0] == TASK_POOLS["medium"][0]

    candidates, _ = router.ordered_candidates("strong")
    assert candidates[0] == TASK_POOLS["strong"][0]

    candidates, _ = router.ordered_candidates("advanced")
    assert candidates[0] == TASK_POOLS["advanced"][0]

    candidates, _ = router.ordered_candidates("feedback")
    assert candidates[0] == TASK_POOLS["feedback"][0]


def test_qwen_rejects_json_mode_hook() -> None:
    """qwen is flagged json_mode=False so the provider skips
    response_format for it (Groq rejects the hook on reasoning models),
    while every other generation model keeps JSON mode."""
    from services.llm_service import _model_supports_json

    assert _model_supports_json("qwen/qwen3.6-27b") is False
    assert _model_supports_json("llama-3.1-8b-instant") is True
    assert _model_supports_json("openai/gpt-oss-20b") is True
    assert _model_supports_json("llama-3.3-70b-versatile") is True
    # Unknown models default to JSON mode (safe default).
    assert _model_supports_json("some/future-model") is True


def test_extract_json_strips_think_blocks() -> None:
    """Reasoning-model output wrapped in <think>...</think> must still
    yield the trailing JSON object."""
    from services.llm_service import _extract_json

    raw = (
        "<think>Let me plan the question carefully.</think>\n\n"
        '{"question": "What problem does RAG solve?", "topic": "RAG"}'
    )
    assert _extract_json(raw) == (
        '{"question": "What problem does RAG solve?", "topic": "RAG"}'
    )


def test_router_skips_unhealthy_model_without_blocking_others() -> None:
    """Independent quotas: a rate-limited model is skipped, the next
    suitable model in the SAME pool is selected."""
    tracker = ModelHealthTracker()
    router = ModelRouter(tracker)

    tracker.record_rate_limited("llama-3.3-70b-versatile", retry_after_s=600)
    candidates, reason = router.ordered_candidates("strong")
    assert "llama-3.3-70b-versatile" not in candidates[:3]
    assert candidates[0] == "qwen/qwen3.6-27b"  # next healthy in the pool

    # The fleet is NOT blocked: other pools still prefer their own models.
    candidates, _ = router.ordered_candidates("simple")
    assert candidates[0] == "llama-3.1-8b-instant"
    assert tracker.healthy("llama-3.1-8b-instant") is True


def test_router_respects_hard_failure_cooldown() -> None:
    """A hard failure (404 / JSON) cools the model down; a later success
    restores it."""
    tracker = ModelHealthTracker()
    router = ModelRouter(tracker)

    tracker.record_failure("openai/gpt-oss-20b", "model_not_found", hard=True)
    assert tracker.healthy("openai/gpt-oss-20b") is False
    candidates, _ = router.ordered_candidates("medium")
    assert candidates[0] == "qwen/qwen3.6-27b"

    tracker.record_success("openai/gpt-oss-20b", latency_ms=400, tokens=50)
    assert tracker.healthy("openai/gpt-oss-20b") is True


def test_preferred_model_keeps_continuity_within_task() -> None:
    """The session's preferred model is kept first when it fits the task
    (conversational continuity), but never dragged into a cheaper tier."""
    tracker = ModelHealthTracker()
    router = ModelRouter(tracker)

    # 70B fits the strong pool -> continuity keeps it first.
    candidates, _ = router.ordered_candidates(
        "strong", preferred="llama-3.3-70b-versatile"
    )
    assert candidates[0] == "llama-3.3-70b-versatile"

    # 70B does NOT fit the simple pool's cheap tier -> not forced.
    candidates, _ = router.ordered_candidates(
        "simple", preferred="llama-3.3-70b-versatile"
    )
    assert candidates[0] == "llama-3.1-8b-instant"


def test_complexity_estimation() -> None:
    assert estimate_answer_complexity("") == "simple"
    assert estimate_answer_complexity("short") == "simple"
    assert (
        estimate_answer_complexity(
            "Embeddings map text into a vector space so similar passages sit "
            "close together, which lets us rank them by similarity."
        )
        == "medium"
    )
    assert (
        estimate_answer_complexity(
            "I'd weigh the trade-off between semantic search and a fallback "
            "keyword index, then monitor latency and reranking quality in "
            "production before scaling out."
        )
        == "strong"
    )


def test_task_mapping_uses_prompt_markers() -> None:
    assert (
        task_for_call("follow_up", "- Follow-up strategy: simplify\nx")
        == "simple"
    )
    assert (
        task_for_call("follow_up", "- Follow-up strategy: deeper\nx")
        == "strong"
    )
    # Evaluation of a short answer stays medium (judgment), never simple.
    assert task_for_call("evaluate", "CANDIDATE'S ANSWER\nIt retrieves chunks.") == "medium"
    assert (
        task_for_call(
            "evaluate",
            "CANDIDATE'S ANSWER\n" + "architecture trade-offs " * 40,
        )
        == "strong"
    )
    assert task_for_call("question", "Generate ONE interview question") == "question"
    assert task_for_call("feedback", "The interview is finished") == "feedback"


# ---------------------------------------------------------------- quota state


def test_quota_state_transitions() -> None:
    """Usage fractions drive NEAR_*_LIMIT states before any provider 429."""
    tracker = ModelHealthTracker()
    q = MODEL_QUOTAS["llama-3.3-70b-versatile"]

    assert tracker.get("llama-3.3-70b-versatile").quota_state() == "AVAILABLE"

    # 90% of TPD -> NEAR_TPD_LIMIT (threshold 0.80)
    tracker.simulate_usage("llama-3.3-70b-versatile", tpd_pct=0.90)
    assert "TPD" in tracker.get("llama-3.3-70b-versatile").quota_state()

    # 100% of TPD -> DAILY_EXHAUSTED
    tracker.simulate_usage("llama-3.3-70b-versatile", tpd_pct=1.0)
    assert (
        tracker.get("llama-3.3-70b-versatile").quota_state()
        == "DAILY_EXHAUSTED"
    )

    # Fresh model is AVAILABLE again.
    tracker.simulate_usage("llama-3.3-70b-versatile")
    assert (
        tracker.get("llama-3.3-70b-versatile").quota_state() == "AVAILABLE"
    )

    # TPM approaching its limit.
    tracker.simulate_usage("llama-3.1-8b-instant", tpm_pct=0.85)
    assert "TPM" in tracker.get("llama-3.1-8b-instant").quota_state()


def test_rpm_rpd_states_are_tracked_independently() -> None:
    """RPM and RPD are separate buckets from the token limits."""
    tracker = ModelHealthTracker()
    tracker.simulate_usage("openai/gpt-oss-20b", rpm_pct=0.90)
    state = tracker.get("openai/gpt-oss-20b").quota_state()
    assert "RPM" in state
    # Token windows untouched.
    assert tracker.get("openai/gpt-oss-20b").tokens_this_minute == 0


# ----------------------------------------------------------------- reservation


def test_reservation_blocks_oversubscription() -> None:
    """Concurrent requests cannot push a model past its TPM window: the
    second reservation fails when the window is full."""
    tracker = ModelHealthTracker()
    q = MODEL_QUOTAS["llama-3.1-8b-instant"]

    assert tracker.reserve_capacity("llama-3.1-8b-instant", q["tpm"] - 500)
    # Remaining window is now ~500 tokens; a 1000-token request must fail.
    assert not tracker.reserve_capacity("llama-3.1-8b-instant", 1000)

    # Releasing the reservation frees the window again.
    tracker.release_reservation("llama-3.1-8b-instant", q["tpm"] - 500)
    assert tracker.reserve_capacity("llama-3.1-8b-instant", 1000)


def test_reconcile_records_actual_usage() -> None:
    tracker = ModelHealthTracker()
    tracker.reserve_capacity("llama-3.1-8b-instant", 2000)
    tracker.reconcile_capacity("llama-3.1-8b-instant", 2000, actual_tokens=1800)
    state = tracker.get("llama-3.1-8b-instant")
    assert state.pending_tokens == 0
    assert state.tokens_this_minute == 1800
    assert state.requests_this_minute == 1


def test_reservation_skips_window_exceeding_request() -> None:
    """A request that would push the daily window past its limit cannot be
    reserved, so the caller picks another model before a doomed request."""
    tracker = ModelHealthTracker()
    q = MODEL_QUOTAS["llama-3.3-70b-versatile"]
    # 95% of the 100K TPD leaves 5000 tokens; a 6000-token request exceeds it.
    tracker.simulate_usage("llama-3.3-70b-versatile", tpd_pct=0.95)
    assert not tracker.reserve_capacity("llama-3.3-70b-versatile", 6000)
    # A small request still fits (the window is not hard-closed).
    assert tracker.reserve_capacity("llama-3.3-70b-versatile", 2000)
    assert q["tpd"] is not None


# ----------------------------------------------------------- load balancing


def test_load_balance_prefers_fresh_model() -> None:
    """When capability is equal, the router prefers the model with more
    quota headroom — traffic spreads instead of one model being exhausted."""
    tracker = ModelHealthTracker()
    router = ModelRouter(tracker)

    # Simple pool: 8B is best-fit, then allam.  Push 8B near its TPM limit.
    tracker.simulate_usage("llama-3.1-8b-instant", tpm_pct=0.95)
    candidates, _ = router.ordered_candidates("simple")
    assert candidates[0] == "allam-2-7b"  # fresh peer takes over

    # Fresh again -> 8B leads the pool.
    tracker.simulate_usage("llama-3.1-8b-instant")
    candidates, _ = router.ordered_candidates("simple")
    assert candidates[0] == "llama-3.1-8b-instant"


def test_daily_headroom_protection_70b() -> None:
    """70B at 80%+ of its 100K TPD is not burned on strong work when a
    suitable peer (qwen) still has headroom."""
    tracker = ModelHealthTracker()
    router = ModelRouter(tracker)

    tracker.simulate_usage("llama-3.3-70b-versatile", tpd_pct=0.85)
    candidates, _ = router.ordered_candidates("strong")
    assert candidates[0] == "qwen/qwen3.6-27b"

    # When everyone is fresh, 70B leads the strong pool again.
    tracker.simulate_usage("llama-3.3-70b-versatile")
    candidates, _ = router.ordered_candidates("strong")
    assert candidates[0] == "llama-3.3-70b-versatile"


def test_usage_spreads_across_suitable_peers() -> None:
    """As models approach their limits, work shifts to the next suitable
    peer: A -> B -> C, without waiting for a 429."""
    tracker = ModelHealthTracker()
    router = ModelRouter(tracker)

    # Medium pool: 20B leads, qwen second.
    tracker.simulate_usage("openai/gpt-oss-20b", tpm_pct=0.90)
    candidates, _ = router.ordered_candidates("medium")
    assert candidates[0] == "qwen/qwen3.6-27b"

    # Now qwen is also near its limit -> compound-mini takes over.
    tracker.simulate_usage("openai/gpt-oss-20b", tpm_pct=0.90)
    tracker.simulate_usage("qwen/qwen3.6-27b", tpm_pct=0.90)
    candidates, _ = router.ordered_candidates("medium")
    assert candidates[0] == "groq/compound-mini"


def test_model_status_diagnostics_has_no_secrets() -> None:
    """The developer diagnostics snapshot reports per-model quota state
    without exposing keys or prompt content."""
    tracker = ModelHealthTracker()
    tracker.simulate_usage("llama-3.1-8b-instant", tpm_pct=0.5)
    summary = tracker.summary()
    assert "llama-3.1-8b-instant" in summary
    row = summary["llama-3.1-8b-instant"]
    assert row["quota_state"] in ("AVAILABLE", "HEALTHY", "BUSY")
    assert row["tpm_used"] > 0
    assert row["tpm_limit"] == MODEL_QUOTAS["llama-3.1-8b-instant"]["tpm"]
    assert all("key" not in str(v).lower() for v in row.values())
