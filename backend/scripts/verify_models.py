"""Probe every configured Groq model through the provider abstraction.

Each model receives one tiny completion so the probe costs almost nothing;
the report shows which models are reachable, which return 404 / JSON errors,
and which are rate-limited right now — exactly the per-model state the
intelligent router tracks at runtime.

Probing matches how the app actually calls each model:

* prompt-guard models (22M / 86M) are probability classifiers: a single
  user message, no ``response_format`` (they reject it), tiny output;
* every other model (generation + the safeguard chat model) uses the
  JSON ``complete()`` path, with an explicit JSON shape in the prompt
  (gpt-oss models return an empty generation otherwise).

Usage::

    cd backend
    .venv/Scripts/python scripts/verify_models.py

Only ``GROQ_API_KEY`` is required (never printed).
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Allow running as ``python scripts/verify_models.py`` from the backend dir.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from services.llm_service import OpenAICompatibleProvider
from services.model_router import MODEL_REGISTRY

_JSON_SYSTEM = "Reply with a JSON object only, no markdown, no commentary."
_JSON_USER = (
    "Return a JSON object with exactly these fields: "
    '{"ok": true, "probe": "reachable"}'
)


async def main() -> None:
    if not settings.llm_api_key:
        print("GROQ_API_KEY is not set — cannot probe live models.")
        return
    provider = OpenAICompatibleProvider(settings)
    print(f"provider: {settings.llm_base_url}")
    print(f"{'model':<42} {'status':<14} detail")
    print("-" * 78)
    results: dict[str, str] = {}
    for model in MODEL_REGISTRY:
        role = MODEL_REGISTRY[model].get("role", "")
        try:
            if role in ("guard_light", "guard_strong"):
                raw = await provider.classify(
                    model=model,
                    message="What is retrieval augmented generation?",
                    timeout=15,
                )
                print(f"{model:<42} {'OK':<14} role={role} reply={raw.strip()[:24]!r}")
            else:
                raw = await provider.complete(
                    model=model,
                    system=_JSON_SYSTEM,
                    user=_JSON_USER,
                    temperature=0.0,
                    max_tokens=128,
                    timeout=20,
                )
                print(f"{model:<42} {'OK':<14} role={role} reply={raw.strip()[:20]!r}")
            results[model] = "ok"
        except Exception as exc:  # noqa: BLE001 - report every failure mode
            status = "RATE_LIMITED" if "429" in str(exc) else "UNAVAILABLE"
            print(f"{model:<42} {status:<14} {str(exc)[:80]}")
            results[model] = status
    await provider.close()

    ok = sum(1 for s in results.values() if s == "ok")
    print("-" * 78)
    print(f"{ok}/{len(MODEL_REGISTRY)} models reachable right now.")


if __name__ == "__main__":
    asyncio.run(main())
