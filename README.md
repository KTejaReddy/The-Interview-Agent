# AI Interview Agent

Build the interviewer, not the interview.

A production-ready hackathon project that simulates an **experienced
technical interviewer**. It conducts a conversational technical interview
based on a candidate's learning journey through the AI Cohort — not a
chatbot, not a quiz, not a RAG assistant.

The engine:

- plans every question **adaptively** — the next topic is scored from the
  candidate's completed missions, attempts, struggles, engagement and the
  conversation so far (never from uncompleted material),
- enforces **8+ actual interviewer questions across 4+ distinct curriculum
  days** as a hard engine rule (never an LLM suggestion) — a follow-up is
  also a question, so the counter reflects the real conversation,
- follows coherent **progression paths** (RAG path, agent path, production
  path) through the candidate's own completed days,
- asks **intelligent follow-ups** (deeper / simplify / recovery / probe),
  detects "I don't know" deterministically, and never traps the candidate
  on one topic,
- prevents **semantic duplicates** with deterministic text-similarity
  checks plus an LLM anti-duplication instruction,
- remembers what the candidate said (**context retention**) and references
  their own words later,
- ends with **structured feedback** — exactly `summary`, `strengths`,
  `gaps`, `next` per `technical-spec.md`.

The project is driven entirely by three mandatory datasets that it
**never modifies**:

| File                | Accepted locations                          | Purpose                         |
| ------------------- | ------------------------------------------- | ------------------------------- |
| `curriculum.json`   | `backend/data/`, `backend/`, project root   | The 31-day curriculum           |
| `candidates.json`   | `backend/data/`, `backend/`, project root   | Candidate records (also accepts `candidate.json`) |
| `technical-spec.md` | `backend/data/`, `backend/`, project root   | The technical specification     |

> **Datasets are immutable.** The application reads them read-only at
> startup; `GET /api/health` reports whether each loaded. The loaders are
> tolerant of the exact JSON shape (the official datasets ship with a
> `member` / `missions` / `signals` structure and days without explicit
> `topics` — both handled). `GET /api/health` reports dataset status.

---

## Features

- ✅ Conversational interview via `POST /api/interview` (exact
  `technical-spec.md` contract: `reply` / `done` / `feedback`)
- ✅ **8+ questions** and **4+ curriculum days** enforced by the engine —
  the interview cannot end before both are met
- ✅ **Personalized** — plan built from the candidate's completed missions,
  attempts, passed/failed/skipped topics, cohort signals, experience,
  education and job role
- ✅ **Adaptive follow-ups** — good answers go deeper, weak answers are
  simplified, wrong answers get recovery scaffolding, "I don't know" gets a
  *different* simpler diagnostic
- ✅ **Deterministic duplicate prevention** — token-set Jaccard checks against
  every previous question + guaranteed-fresh fallback follow-ups
- ✅ **Concise, evidence-driven length** — MIN 8 / target 8–10 / hard max 12
  ACTUAL questions (main questions + follow-ups — a follow-up is also a
  question); the interview finishes as soon as 8+ questions, 4+ days and
  sufficient evidence are reached (never a 15–20 question marathon)
- ✅ **Topic saturation** — max 2 main questions per day, at most one
  follow-up per topic, repeated failures mark a topic weak and move on
- ✅ **Context memory** — full-session memory plus candidate-mention tracking
  so later questions can reference the candidate's own words
- ✅ **Structured final feedback** — `summary`, `strengths`, `gaps`, `next`
  (+ optional extended `score` for the UI ring; `confidence`/`topics_covered`
  stay internal)
- ✅ **sessionId**-based state (client-supplied per spec), in-memory session
  store, TTL expiry
- ✅ **SSE streaming** transport on the same endpoint (JSON default)
- ✅ Mixed question types (definition → conceptual → scenario → architecture
  → debugging → tradeoffs → design → production → deployment → reasoning)
- ✅ **Prompt-injection guard** — candidate messages are sanitized and the
  interviewer prompt treats them as untrusted data
- ✅ LLM abstraction layer — OpenAI-compatible (OpenAI, Gemini, Groq,
  Together, Azure…), model fallback + retries, **no API key hardcoded**
- ✅ Modern dark-theme React frontend: candidate cards, typing indicator,
  question counter, progress bar, **curriculum coverage tracker**, day
  badge, auto-scroll, session indicator, **score ring** on the feedback page

---

## Architecture

```
┌──────────────┐   POST /api/interview      ┌───────────────────────────────┐
│   React SPA  │ ─────────────────────────► │          FastAPI              │
│  (Vite+TS)   │ ◄───────────────────────── │   ┌─────────────────────────┐ │
└──────────────┘  {reply, done} (+ SSE)     │   │  api/  routes + deps   │ │
                                            │   └───────────┬─────────────┘ │
                                            │               ▼               │
                                            │   ┌─────────────────────────┐ │
                                            │   │        agents/           │ │
                                            │   │  InterviewManager (SM)  │ │
                                            │   │  CandidateAnalyzer      │ │
                                            │   │  QuestionPlanner (score)│ │
                                            │   │  DuplicateGuard         │ │
                                            │   │  DifficultyManager      │ │
                                            │   │  ResponseEvaluator      │ │
                                            │   │  FollowUpGenerator      │ │
                                            │   │  FeedbackGenerator      │ │
                                            │   └───┬───────┬───────┬─────┘ │
                                            │       ▼       ▼       ▼       │
                                            │  memory/  retrieval/  services│
                                            │  (context (loaders & (LLM     │
                                            │   memory)  retriever)  provider│
                                            │  models/  schemas/  prompts/  │
                                            │  utils/input_guard (security) │
                                            └───────────────────────────────┘
              datasets: curriculum.json · candidates.json · technical-spec.md
```

### State machine

```
START → INTRODUCTION → QUESTIONING → FOLLOW_UP → NEXT_TOPIC → …
       → FINAL_QUESTION → EVALUATION → FEEDBACK → DONE
```

Every transition is validated (`backend/models/interview_state.py`);
illegal transitions raise a 409. Completion is a *hard engine decision* in
`InterviewManager._should_terminate`: the interview only ends once
`main_questions ≥ 8` **and** `distinct_days ≥ 4` are met **and** the
assessment is reasonably settled — the soft target (10) is the usual
finish line and an absolute safety cap (12) guarantees termination.  The
interview never runs on simply because more topics are available.

### Interview length policy

| Setting                    | Value | Meaning                                     |
| -------------------------- | ----- | ------------------------------------------- |
| `INTERVIEW_MIN_QUESTIONS`  | 8     | Hard requirement on ACTUAL questions (mains + follow-ups) |
| `INTERVIEW_TOTAL_QUESTIONS`| 10    | Soft target on actual questions — usual finish line |
| `INTERVIEW_MAX_QUESTIONS`  | 12    | Absolute safety ceiling on actual questions   |
| `INTERVIEW_MIN_DAYS`       | 4     | Hard requirement (never below)              |

### Module map

| Module                       | Responsibility                                                        |
| ---------------------------- | --------------------------------------------------------------------- |
| `agents/interview_manager`   | Orchestrator — state machine, coverage gate, mentions memory          |
| `agents/candidate_analyzer`  | Raw candidate → profile (strong/weak/failed/skipped, completed days)  |
| `agents/question_planner`    | Scores the next topic; progression paths; saturation; dedup regen     |
| `agents/duplicate_guard`     | Deterministic semantic-duplicate detection (Jaccard + cosine)         |
| `agents/difficulty_manager`  | All difficulty decisions (baseline, ramp, follow-up strategy)         |
| `agents/response_evaluator`  | Scores 0–10, verdict + strategy; deterministic "I don't know" rules   |
| `agents/followup_generator`  | Adaptive follow-up + guaranteed-fresh fallback                        |
| `agents/feedback_generator`  | Final structured feedback (evidence-based, per-topic assessments)     |
| `retrieval/*`                | Loads the datasets verbatim; day-number lookup, modules, mentions     |
| `memory/*`                   | Conversation memory + per-turn prompt context snapshots               |
| `services/llm_service`       | Provider abstraction, model fallback, retries, structured JSON        |
| `services/prompt_builder`    | Loads `prompts/*.md`; deterministic transition lines                  |
| `services/session_manager`   | In-memory session store with TTL expiry                               |
| `utils/input_guard`          | Prompt-injection / system-prompt-extraction sanitization              |
| `models/*`                   | State machine, session, plan (assessments), profile, enums            |
| `schemas/*`                  | API contract (spec-exact) + Pydantic schemas for LLM outputs          |

---

## Folder structure

```
.
├── README.md
├── .env.example
├── docker-compose.yml
├── curriculum.json          # ← official datasets (read-only) — also
├── candidates.json          #   accepted in backend/data/ or backend/
├── technical-spec.md
├── backend/
│   ├── main.py              # FastAPI app, CORS, exception handlers, lifespan
│   ├── config.py            # Env config + dataset location resolution
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── data/                # drop copies of the three datasets here
│   ├── api/                 # routes (POST /api/interview, SSE) + DI container
│   ├── agents/              # manager, analyzer, planner, guard, evaluator, …
│   ├── prompts/             # prompt templates (markdown, separate)
│   ├── memory/              # conversation memory + context manager
│   ├── retrieval/           # dataset loaders + curriculum retriever
│   ├── models/              # domain models, state machine, enums
│   ├── schemas/             # Pydantic API + LLM schemas
│   ├── services/            # LLM service, prompt builder, session manager
│   ├── utils/               # errors, logging, input guard
│   ├── scripts/live_tests.py# live scenario harness (A–H)
│   └── tests/               # pytest suite (real-shaped fixtures)
└── frontend/
    ├── package.json / vite.config.ts / tsconfig.json / tailwind.config.js
    ├── Dockerfile / nginx.conf
    └── src/
        ├── types/ services/ context/ hooks/
        ├── components/      # ChatMessage, CoverageTracker, ScoreRing, …
        └── pages/           # Landing, Interview, Feedback
```

---

## Quick start (local)

### 1. Datasets

The three files may live in `backend/data/`, `backend/`, or the project
root — the loaders find them at startup (root copies are used as-is,
read-only).

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |  macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then set LLM_API_KEY (or LLM_MOCK_MODE=true)
uvicorn main:app --reload --port 8000
```

> No API key yet? Set `LLM_MOCK_MODE=true` in `backend/.env` to run the
> full flow with a deterministic offline provider — perfect for demos and
> tests.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                  # http://localhost:5173
```

The Vite dev server proxies `/api` to `http://localhost:8000`.

### 4. Tests & live verification

```bash
cd backend
pytest                       # 143 tests, fully offline (mock LLM + fixtures)
python scripts/live_tests.py # live scenarios A–H against the real datasets
```

### 5. Performance

Interview turns are optimized for low latency without sacrificing the
conversational intelligence:

* **One LLM call per turn, often zero** — obvious answers ("I don't know",
  greetings, bare "I know" claims) are classified deterministically
  (`utils/answer_signals`) with no LLM round-trip, so weak-candidate turns
  cost a single (or zero) model call instead of evaluation + generation.
  Substantive answers still get full semantic LLM evaluation.
* **Fast-model routing** — short follow-ups on non-substantive verdicts
  (simplify / verify / recovery) route to `LLM_FAST_MODEL`
  (default `llama-3.1-8b-instant`, already in the fallback chain — no new
  key); complex reasoning (evaluation, new-topic questions, deep follow-ups,
  feedback) keeps the primary model. When the primary is rate-limited, the
  fast model is tried next so a quota outage degrades to ~0.3 s answers
  instead of a long fallback walk.
* **Compact context** — prompts see the last `TRANSCRIPT_WINDOW` turns
  verbatim (default 6) plus a structured digest (aggregate summary + notable
  earlier statements); earlier claims, mistakes and contradictions are never
  lost. Only final feedback reads the whole transcript (it runs once).
* **Slim prompts** — the prompt templates were audited and compressed (the
  largest fixed token cost per call): `interviewer_system` −24%,
  `generate_question` −32%, `evaluate_answer` −22%, `generate_follow_up`
  −23%.  A typical turn sends ~1,200–3,500 input tokens (question ~3.4K,
  evaluate ~1.2K, follow-up ~3.1K total) — inside the
  `<3K normal / <2K simple / <4K complex` budgets.
* **Persona/assessment split** — the full human-interviewer block
  (`prompts/human_interviewer.md`, ~2.1K tokens) is sent only on the
  conversation-facing calls (question + follow-up generation), where it
  shapes what the candidate hears.  Internal assessment calls (answer
  evaluation, final feedback) use the lean `assessment_system_prompt()`
  (engine contract + security only), so the persona is not paid on every
  internal call.
* **Capped output** — conversational calls use `LLM_TURN_MAX_TOKENS`
  (default 300) instead of the 800-token general budget; feedback keeps the
  full budget.
* **Quota-aware retries** — a daily-token-quota 429 ("try again in 20+
  min") skips straight to the next model instead of burning 1+2+4 s backoff
  on an exhausted model; transient errors still retry.
* **Instrumentation** — every LLM call logs
  `llm_call session=… type=… model=… ms=… in_tok~… out_tok~… max_tok=…
  est_total~…` (input estimate, actual output, output budget, estimated
  total) and every turn logs `turn session=… state=… total_ms=…`; the
  `GET /api/models` endpoint shows per-model quota state, usage fractions
  and selection counts.

Measured on the live server (Groq, `127.0.0.1`): start ≈ 0.6-1.0 s, an
"I don't know" follow-up ≈ 0.3-1.6 s, a new-topic question ≈ 0.7-1.4 s, a
substantive answer + follow-up ≈ 1.4-3.2 s — down from 30-35 s per turn.

### 5b. The human interviewer prompt

The interviewer's persona and behavior live in **one dedicated block**,
`backend/prompts/human_interviewer.md` (exposed as
`PromptBuilder.human_interviewer_prompt()`).  It is the single
authoritative home for how the interviewer behaves — listening, remembering
earlier answers, adapting difficulty, handling "I don't know" / bare "I
know" claims, noticing contradictions, expressing subtle emotion, avoiding
repetitive templates and scripted transitions — and is composed into the
system prompt (`PromptBuilder.system_prompt()`) that every conversation-
facing generation call receives.

The per-task templates (`generate_question`, `generate_follow_up`, …)
only carry their own mechanics (JSON contracts, dispatch markers, the
reaction/question assembly rules); the behavioral rules are **not
duplicated** there.  Deterministic guards backstop the LLM: canned-phrase
filtering, curriculum-title leakage checks, and stripping of dangling
connectors ("...embeddings, but") so a reaction always reads complete
before the question is appended.

### 6. Intelligent multi-model routing (one Groq API key)

All 11 supplied Groq models are supported through the **single**
`GROQ_API_KEY`, with an intelligent router (`services/model_router.py`)
that picks the right model for the task instead of serialising the fleet:

* **Specialised registry + task pools** — every model has a role
  (`fast_conversation`, `balanced_reasoning`, `technical_reasoning`,
  `deep_reasoning`, `advanced_reasoning`, `complex_agentic`, …) and each
  task (simple / medium / strong / advanced / question / feedback) has an
  ordered pool.  A normal turn uses **one** generation model.
* **Quota-aware load balancing** — `MODEL_QUOTAS` mirrors the exact Groq
  account table (RPM / RPD / TPM / TPD per model).  The router tracks each
  model's rolling minute/day usage and **switches before a limit is hit**
  (not after a 429): a weighted score — task fitness + quota headroom +
  latency + health + load balance — re-ranks the pool every call, so
  traffic spreads across suitable peers and a model at 80%+ of its TPM/TPD
  is demoted while a fresh peer takes over.  `MODEL_QUOTA_HEADROOM_PERCENT`
  (default 20) plus per-limit thresholds tune when switching happens.
* **Token reservation** — before each call the router reserves the
  estimated token cost against the model's TPM/TPD windows and picks
  another model if the reservation fails, so concurrent interview sessions
  cannot oversubscribe one model.  Actual usage is reconciled after the
  response; failed calls release their reservation.
* **Independent per-model quotas** — each model tracks its own health
  (rate-limited-until, hard-failure cooldown, latency, success rate).  One
  exhausted model is skipped; the fleet keeps answering.  A daily-quota 429
  ("try again in 20+ min") skips straight to the next model with no backoff.
* **Session model continuity** — the chosen model, routing reason and
  latency are stored per session; the interviewer's persona lives in the
  shared prompts, so model switches are invisible to the candidate.
* **Complexity estimation** — answer length + technical keywords select the
  judging tier: short/non-substantive replies route cheap, deep
  architecture answers escalate to 70B / 120B / compound.
* **Reasoning-model support** — `qwen/qwen3.6-27b` rejects
  `response_format: json_object`, so it is flagged `json_mode: False`:
  the provider skips the hook, gives the think block extra output
  headroom, and `_extract_json` strips `<think>…</think>` before parsing.
* **Security models on a dedicated path** — `classify()` sends guard
  models (prompt-guard 22M / 86M) a **single user message** with no JSON
  mode and parses their probability score; the safeguard chat model gets
  the full JSON template.  Guard models never generate interviewer text.

Probe live reachability with `scripts/verify_models.py` (one tiny call per
model; only `GROQ_API_KEY` is needed).  Watch the router's live per-model
quota state, usage and selection counts at `GET /api/models` (developer
diagnostics; exposes no keys or prompt content).

---

## Docker

```bash
docker compose up --build
# Frontend:  http://localhost:8080
# Backend:   http://localhost:8000/docs
# Datasets:  mounted read-only from ./backend/data
```

---

## LLM provider configuration

The backend talks to any **OpenAI-compatible** `/chat/completions` endpoint.
Configure it via environment variables — **no key is ever hardcoded**:

| Variable             | Example                                     | Meaning                   |
| -------------------- | ------------------------------------------- | ------------------------- |
| `LLM_PROVIDER`       | `groq`                                      | Provider identifier       |
| `GROQ_BASE_URL`      | `https://api.groq.com/openai/v1`            | Base URL (Groq default)   |
| `GROQ_MODEL`         | `llama-3.3-70b-versatile`                   | Primary model             |
| `LLM_FALLBACK_MODELS`| `groq/compound,openai/gpt-oss-20b,…`        | Fallback chain            |
| `LLM_API_KEY`        | *(empty until provisioned)*                 | Secret key                |
| `LLM_TEMPERATURE`    | `0.7`                                       | Sampling temperature      |
| `LLM_MAX_TOKENS`     | `800`                                       | Max completion tokens     |
| `LLM_MOCK_MODE`      | `false`                                     | Offline demo provider     |
| `LLM_JSON_MODE`      | `true`                                      | Disable for Gemini-style  |

**Google Gemini** exposes an OpenAI-compatible endpoint too:

```ini
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
LLM_MODEL=gemini-2.0-flash
LLM_API_KEY=<your Gemini API key>
LLM_JSON_MODE=false
```

The provider abstraction lives in `backend/services/llm_service.py`
(`LLMProvider` protocol). Every LLM call returns **structured JSON
validated against a Pydantic schema**; malformed output is repaired and
retried, and failures fall back through the model chain without losing
session state.

---

## API documentation

### `POST /api/interview`

Exactly per `technical-spec.md`. Two request shapes:

**1. Start interview** (first request — client supplies `sessionId` + the
candidate object; the id is resolved against the authoritative dataset):

```json
{
  "sessionId": "abc-123",
  "candidate": { "member": { "id": "CAND-001" } }
}
```

**Response**

```json
{
  "reply": "Welcome, Sarah — thanks for making the time. I've been reviewing your journey through the AI Cohort…",
  "done": false,
  "sessionId": "abc-123",
  "state": "QUESTIONING",
  "questionNumber": 1,
  "totalQuestions": 12,
  "currentDay": "Day 7 — Embeddings Explained",
  "currentTopic": "Embeddings Explained"
}
```

**2. Conversation turn** (every subsequent request):

```json
{
  "sessionId": "abc-123",
  "message": "Embeddings map tokens into vectors so similar meanings sit close together…"
}
```

**Response** — `{ "reply": "...", "done": false }` plus the informative
extras above.

**3. End of interview** — `done: true` with structured feedback:

```json
{
  "reply": "Thank you, Sarah — that's everything I had for you today…",
  "done": true,
  "feedback": {
    "summary": "…",
    "strengths": ["…"],
    "gaps": ["…"],
    "next": ["…"],
    "score": 78
  }
}
```

> `score` is an **optional extended field** (powers the UI score ring) and
> is omitted unless present. `confidence` and `topics_covered` are computed
> internally and never exposed.

**SSE streaming** — send `Accept: text/event-stream` to receive the same
payload as events (`{"type":"phase",…}` then `{"type":"reply","payload":…}`).
Plain JSON remains the default.

**Frontend shorthand** — the bundled UI also sends
`{ "candidateId": "CAND-001", "message": "…" }` to start (the id is
resolved server-side from the dataset).

### `GET /api/interview/{sessionId}`

Full session snapshot (transcript + state + feedback) — used to resume
after a page refresh.

### `GET /api/candidates`

```json
[
  {
    "id": "CAND-001", "name": "Sarah Johnson", "role": "Senior Data Engineer",
    "experience": 9, "education": "MS Computer Science",
    "missionsCompleted": 9, "missionsFirstTry": 4, "struggles": 2,
    "skipped": 1, "failed": 0
  }
]
```

### `GET /api/health`

```json
{
  "status": "ok",
  "app": "AI Interview Agent",
  "curriculumDays": 31,
  "candidates": 20,
  "specLoaded": true,
  "llmConfigured": true,
  "mockMode": false,
  "datasetsError": null
}
```

---

## Error handling

| Condition                    | Status | `detail.code`                     |
| ---------------------------- | ------ | --------------------------------- |
| Unknown candidate            | 404    | `candidate_not_found`             |
| Unknown session              | 404    | `session_not_found`               |
| Expired session              | 410    | `session_expired`                 |
| Missing datasets             | 503    | `curriculum_unavailable` / `datasets_unavailable` |
| No LLM configured            | 503    | `llm_not_configured`              |
| LLM failure / bad output     | 502    | `llm_error`                       |
| Candidate/session mismatch   | 409    | `session_candidate_mismatch`      |
| Illegal state transition     | 409    | `invalid_state_transition`        |
| Malformed / ambiguous body   | 400    | `malformed_request`               |

All errors share the envelope `{ "detail": { "code", "message", … } }`.
Validation errors return a clean 400 with field details.

---

## Interview intelligence

- **Candidate intelligence** — `candidate_analyzer` derives strong topics
  (passed ≤ 2 attempts), struggled topics (passed but ≥ 3 attempts, probed
  mid-interview), failed topics and skipped topics (both treated as *not
  demonstrated knowledge*), completed days (the only question pool),
  engagement and confidence from cohort signals.
- **Curriculum intelligence** — `curriculum_retriever` maps day numbers,
  modules and adjacency; `ground_context` grounds every question in the
  day's own objectives/tools; nothing is ever invented.
- **QuestionIntent — assess concepts, not course titles** — for every
  question the planner selects one real **learning objective** (never
  reused on the same day), derives a technical **concept** from it
  (`utils/concepts.py`: "Understand how text is converted into vector
  embeddings" → *how text is converted into vector embeddings*; "Create a
  /chat API endpoint…" → *how to create a /chat API endpoint…*), and packs
  objective + concept + cognitive level + purpose + evidence bar into a
  structured `QuestionIntent`. The LLM only translates that intent into
  natural interviewer language. Questions like "What is 'Embeddings
  Explained'?" are structurally impossible.
- **Adaptive planning** — `question_planner` scores every completed day by
  candidate relevance + module coherence + coverage need − saturation −
  failure penalty, producing RAG/agent/production progression paths.
- **Deepen after coverage** — before the 4-day minimum is met, uncovered
  days are strongly prioritised; once it is met, the *current* day and its
  neighbours win so the interview collects depth instead of day-count
  (a 13-question / 8-day hop-fest is structurally impossible).
- **Coverage enforcement** — `_should_terminate` refuses to end until
  8+ ACTUAL questions (main questions + follow-ups; a follow-up is also a
  question) AND 4+ distinct days; the planner prioritizes new days when
  coverage is low, then deepens (max 2 mains per day) so interviews stay
  in the 4–6 day / 8–10 question band instead of hopping to a new day
  every question. The 12-question ceiling applies to actual questions, so
  a follow-up-dense interview can never run long.
- **Evidence-based completion** — once the minimums are met, the interview
  ends when the soft budget (10 actual) is reached **or** every touched
  topic has a *settled* assessment: demonstrated (best score ≥ 7, no open
  failures/claims) **or** exhausted (moved on after repeated failures or
  bare claims). An all-"I don't know" interview therefore ends at the
  8-question minimum (4 mains + 4 follow-ups across 4 days) instead of
  being dragged to the soft target with topic revisits — and an absolute
  safety cap guarantees termination.
- **Evidence-based evaluation** — the evaluator never treats surface
  phrases as competence:
  - "I don't know" → deterministic weak/simplify (never rewarded),
  - greetings / filler ("hello", "yes", "okay") → non-answers: one short
    simpler recovery, never a lecture about why they didn't answer,
  - "I know" with no substance → `verify`: the interviewer asks for a
    concrete demonstration from the objective instead of scoring the claim
    (a claim always gets its one verification probe; a second claim marks
    the topic `insufficient_evidence` and moves on),
  - **failure ladder** on one topic — max **two attempts**: first
    struggle → a *different*, simpler diagnostic; second struggle (or a
    wrong answer, which gets one scaffolding probe) → topic marked weak
    and the interviewer moves on (never traps, never 5–6 questions on one
    concept).
- **Follow-up intelligence** — follow-ups are grounded in the question's
  concept/objective, reference what the candidate just said, and are
  checked against every earlier question; a guaranteed-fresh deterministic
  fallback exists when the LLM repeats itself. Fallbacks are
  **phrase-form safe** — activity-style templates use the gerund action
  phrase ("creating a /chat API endpoint…"), explanation-style ones the
  "how …" concept — so a template can never produce "How does how to build
  X fit…?" or "the core job of how to create X", and they rotate angles
  instead of repeating a main → example → mistake bundle. The universal
  "what's the core job of X?" simplification is banned — simplify
  follow-ups are concept-grounded questions about the actual activity
  ("walk me through X from the very first step", "what would X look like
  in practice?", "what does X actually involve?"), and the gerund verb
  table covers every curriculum verb so a phrase can never break mid-
  sentence ("securing chatbot APIs…", never "Secure chatbot APIs…").
- **Human conversational tone** — the system prompt, question and
  follow-up prompts enforce: ONE focused question per turn (never multi-
  part "and and and" questions), short spoken phrasing, brief *varied*
  acknowledgements (never "Glad to hear it…", "Let's make sure we're on
  the same page…" on repeat), no long commentary on non-answers, no
  over-use of the healthcare/capstone framing, and no mention-prefix spam
  ("You mentioned X earlier") on every question.
- **LLM-generated reactions (no prefixed-phrase system)** — the reaction
  to the candidate's last answer is generated by the LLM from what the
  candidate actually said: it acknowledges the correct part, targets the
  missing piece, gently identifies a misconception, or recognizes a
  recovery — never a canned "Great answer!" / "Let's try a simpler
  angle" dictionary. The question prompt receives a structured
  **interviewer state** (emotion, firmness 0–3, last verdict + notes,
  recovery flag) plus the full transcript, and writes a short content-aware
  `reaction` alongside the pure `question`; the reaction naturally bridges
  into the next question. Canned phrases, curriculum titles and day
  numbers are rejected deterministically and fall back to the neutral
  `messages.md` pools — the pools are a safety net, never the primary
  mechanism.
- **Deterministic topic transitions** — when the LLM leaves the reaction
  empty, the engine adds a short, **topic-free** transition that knows
  whether the next question stays on the same topic ("let's push a bit
  deeper…"), relates to it ("and related to that —"), or is a fresh area
  ("let's switch gears…"). The interviewer never reads a curriculum title
  to the candidate (no "let's talk about Security, Privacy & Guardrails")
  and never explains the relationship at length.
- **Emotional trajectory (firmness + recovery)** — the interviewer's
  tone is not a fixed template: it follows the conversation. The engine
  tracks the *consecutive weak-answer streak* ("I don't know" / bare
  claims) into an explicit firmness level (0 calm → 3 firm) and an emotion
  (neutral → concerned → mildly frustrated → firm; skeptical for repeated
  "I know" claims; relieved on a recovery), derived in `ConversationMemory`
  and passed to every prompt as data. The interviewer becomes gradually
  more direct under repeated non-answers, recognizes improvement with a
  recovery reaction, and is never insulting.
- **Full-conversation awareness** — every question, evaluation and
  follow-up prompt receives the **complete Q/A transcript** (all earlier
  questions *and* answers, not just the last one), so the interviewer can
  reason over the whole interview: earlier claims, mistakes, examples and
  topics. Long-term memory aggregates (mention tracking, per-topic
  assessment, contradictions) sit alongside it.
- **Contradiction detection** — the evaluator compares each answer against
  the full transcript; when the candidate contradicts an earlier statement
  (two claims that can't both be true), the interviewer gently probes the
  discrepancy ("That's different from what you said earlier — which did
  you mean?") instead of letting it pass silently, and the contradiction
  is recorded for later prompts and feedback.
- **Relevant context retention** — the mock (and the real LLM's prompt)
  reference concepts the candidate raised earlier, but only when they are
  actually related to the question at hand and at most ~1 in 4 questions —
  never a "You mentioned Docker" non-sequitur on every question.
- **Duplicate prevention** — token-set Jaccard + cosine checks against all
  previous questions; flagged questions are regenerated with a rotated
  learning objective first, then a changed cognitive task.
- **Context retention** — the candidate's own mentions (tools, day titles)
  are recorded and surfaced to later question prompts so the interviewer
  can build on their words.
- **Evidence-based feedback** — strengths come only from topics the
  candidate demonstrably scored well on; gaps are phrased as "Did not
  demonstrate sufficient understanding of X during the interview"; bare
  claims and profile signals are never cited as strengths; psychology is
  never diagnosed. `topics_covered` is **always the authoritative session
  state** (never reconstructed from generated text), so feedback can never
  report fewer topics than the transcript covered.
- **Consistent counters** — the reported question number never exceeds the
  total, so the UI can never show a contradictory "13 of 12"; the feedback
  hero reports "13 questions · 8 curriculum days" instead.

---

## Live test harness

`backend/scripts/live_tests.py` runs the required scenarios against the
real datasets and prints a pass/fail report:

| Scenario | What it verifies                                             |
| -------- | ------------------------------------------------------------ |
| A        | Repeated "I don't know" → topic moves, 8+ Qs, 4+ days, no duplicates, gaps reported |
| B        | Strong answers → deeper follow-ups, completes                 |
| C        | Mixed performance → adaptive behaviour                        |
| D        | Context retention (mentions recorded)                         |
| E        | Personalization (distinct interviews per candidate)           |
| H        | API contract status codes (400/404/409/200, reply+done)       |

```bash
cd backend
python scripts/live_tests.py                  # in-process, mock LLM
python scripts/live_tests.py --url http://127.0.0.1:8000   # against live server
```

---

## Design decisions

- **Plan scored on demand, text generated on demand** — topic selection is
  deterministic application logic (testable, never hallucinated); only the
  question wording is LLM-generated.
- **Structured state over parsed text** — the reference implementation
  parsed "Day X" and `[INTERVIEW_COMPLETE]` out of generated prose; this
  engine keeps every decision in typed state (plan, assessments, counters).
- **LLM always outputs JSON** — validated by Pydantic; no raw-text parsing.
- **Deterministic transitions** — intro, bridges, wrap-up are templated;
  evaluation, follow-ups, question wording and feedback are LLM-generated.
- **Hard minimums** — 8 questions / 4 days are enforced by the state
  machine, not by a prompt instruction.
- **Schema-tolerant datasets** — the loaders accept the official
  `member`/`missions`/`signals` shape and common variants without touching
  the files.
- **In-memory state** — sessions live in `SessionManager` with TTL expiry;
  no database, per the requirements.

---

Generated with Codebuff 🤖 · Co-Authored-By: Codebuff <noreply@codebuff.com>
