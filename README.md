# AI Interview Agent

A production-ready hackathon project that simulates an **experienced technical
interviewer**. It interviews candidates conversationally — not a chatbot, not a
quiz, not a RAG assistant. Questions are planned **before** the interview
(minimum 8 questions across minimum 4 curriculum days), the difficulty ramps
easy → medium → advanced, every answer influences the next question, and the
session ends with **structured feedback** (`summary`, `strengths`, `gaps`,
`next`).

The engine is driven entirely by three mandatory datasets that it **never
modifies**:

| File                | Location                | Purpose                            |
| ------------------- | ----------------------- | ---------------------------------- |
| `curriculum.json`   | `backend/data/`         | The curriculum (days, topics, …)   |
| `candidate.json`    | `backend/data/`         | Candidate records to interview     |
| `technical-spec.md` | `backend/data/`         | The technical specification        |

> **Important:** place your three dataset files in `backend/data/` before
> starting. The application reads them read-only at startup; `GET /api/health`
> reports whether each one loaded. The loaders are schema-tolerant — they
> accept the common field spellings described in
> [`backend/data/README.md`](backend/data/README.md) and adapt to **any**
> candidate inside `candidate.json`.

---

## Features

- ✅ Conversational interview via `POST /api/interview`
- ✅ Minimum **8 questions** (configurable, default 12) across minimum **4
  curriculum days** (default 6)
- ✅ **Personalized** — question plan built from the candidate's missions,
  attempts, passed/failed/skipped topics, signals, experience, education and
  job role
- ✅ **Follow-up questions** — good answers go deeper, weak answers are
  simplified, wrong answers trigger recovery scaffolding
- ✅ **Context memory** — full-session memory of questions, answers, topics,
  difficulty, mistakes and strong answers
- ✅ **Structured final feedback** — exactly `summary`, `strengths`, `gaps`,
  `next` (score/confidence are computed internally but never exposed)
- ✅ **sessionId**-based state, in-memory session store (no database)
- ✅ Mixed question types: definition, conceptual, scenario, architecture,
  debugging, tradeoffs, design, production, deployment, reasoning
- ✅ Difficulty adaptation from the candidate profile (intern → basic,
  senior → system design, many attempts → conceptual, skipped → introductory)
- ✅ LLM abstraction layer — OpenAI-compatible (works with OpenAI, Gemini,
  Groq, Together, Azure…), **no API key hardcoded**
- ✅ Modern dark-theme React frontend with typing indicator, question counter,
  progress bar, current-day badge, auto-scroll, session indicator, error
  handling and loading animations

---

## Architecture

```
┌──────────────┐   POST /api/interview    ┌───────────────────────────────┐
│   React SPA  │ ───────────────────────► │          FastAPI              │
│  (Vite+TS)   │ ◄─────────────────────── │   ┌─────────────────────────┐ │
└──────────────┘   JSON (sessionId state) │   │   api/  routes + deps   │ │
                                          │   └───────────┬─────────────┘ │
                                          │               ▼               │
                                          │   ┌─────────────────────────┐ │
                                          │   │    agents/               │ │
                                          │   │  InterviewManager (SM)  │ │
                                          │   │  CandidateAnalyzer      │ │
                                          │   │  QuestionPlanner        │ │
                                          │   │  ResponseEvaluator      │ │
                                          │   │  FollowUpGenerator      │ │
                                          │   │  FeedbackGenerator      │ │
                                          │   └───┬───────┬───────┬─────┘ │
                                          │       ▼       ▼       ▼       │
                                          │  memory/  retrieval/  services│
                                          │  (context (loaders & (LLM     │
                                          │   memory)  retriever)  provider│
                                          │  models/  schemas/  prompts/  │
                                          └───────────────────────────────┘
                          datasets: curriculum.json · candidate.json · technical-spec.md
```

### State machine

```
START → INTRODUCTION → QUESTIONING → FOLLOW_UP → NEXT_TOPIC → …
       → FINAL_QUESTION → EVALUATION → FEEDBACK → DONE
```

Each state transition is validated (`backend/models/interview_state.py`);
illegal transitions raise a 409.

### Module map

| Module                       | Responsibility                                                        |
| ---------------------------- | --------------------------------------------------------------------- |
| `agents/interview_manager`   | Orchestrator — drives the state machine for every candidate message   |
| `agents/candidate_analyzer`  | Reads the raw candidate record → profile (strong/weak, difficulty…)   |
| `agents/question_planner`    | Builds the plan skeleton before questions; generates question text    |
| `agents/response_evaluator`  | Scores answers 0–10, picks verdict + next-move strategy               |
| `agents/followup_generator`  | Writes the adaptive follow-up (deeper / simplify / recovery / probe)  |
| `agents/feedback_generator`  | Produces final structured feedback                                    |
| `retrieval/*`                | Loads the three datasets verbatim; retrieves curriculum for a day     |
| `memory/*`                   | Conversation memory + per-turn prompt context snapshots               |
| `services/llm_service`       | LLM provider abstraction (OpenAI-compatible + deterministic mock)     |
| `services/prompt_builder`    | Loads `prompts/*.md` and fills them; deterministic transition lines   |
| `services/session_manager`   | In-memory session store with TTL expiry                               |
| `models/*`                   | State machine, session, plan, profile, enums                          |
| `schemas/*`                  | API contract + Pydantic schemas for every structured LLM output       |
| `prompts/*`                  | All prompt templates (persona, question, evaluate, follow-up, …)      |

---

## Folder structure

```
.
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── backend/
│   ├── main.py                 # FastAPI app, CORS, exception handlers, lifespan
│   ├── config.py               # Environment configuration (python-dotenv)
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   ├── data/                   # ← drop curriculum.json, candidate.json,
│   │   └── README.md           #   technical-spec.md here (read-only)
│   ├── api/                    # routes (POST /api/interview …) + DI container
│   ├── agents/                 # interview manager, analyzer, planner, …
│   ├── prompts/                # prompt templates (markdown, separate)
│   ├── memory/                 # conversation memory + context manager
│   ├── retrieval/              # dataset loaders + curriculum retriever
│   ├── models/                 # domain models, state machine, enums
│   ├── schemas/                # Pydantic API + LLM schemas
│   ├── services/               # LLM service, prompt builder, session manager
│   ├── utils/                  # errors, logging
│   └── tests/                  # pytest suite (fixture datasets in tests/fixtures)
└── frontend/
    ├── package.json
    ├── vite.config.ts          # dev proxy /api → http://localhost:8000
    ├── tsconfig.json
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    ├── Dockerfile
    ├── nginx.conf              # SPA serve + /api proxy for Docker
    └── src/
        ├── main.tsx / App.tsx / index.css
        ├── types/              # API contract types
        ├── services/           # typed fetch client
        ├── context/            # React Context (global interview state)
        ├── hooks/              # useAutoScroll, useTypingEffect
        ├── components/         # ChatMessage, TypingIndicator, ProgressBar, …
        └── pages/              # Landing, Interview, Feedback
```

---

## Quick start (local)

### 1. Datasets

Copy `curriculum.json`, `candidate.json` and `technical-spec.md` into
`backend/data/`.

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |  macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then set LLM_API_KEY (or LLM_MOCK_MODE=true)
uvicorn main:app --reload --port 8000
```

> No API key yet? Set `LLM_MOCK_MODE=true` in `backend/.env` to run the full
> flow with a deterministic offline provider — perfect for demos and tests.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                  # http://localhost:5173
```

The Vite dev server proxies `/api` to `http://localhost:8000`.

### 4. Tests

```bash
cd backend
pytest                     # 24 tests, fully offline (mock LLM + fixtures)
```

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

| Variable          | Example                                            | Meaning                    |
| ----------------- | -------------------------------------------------- | -------------------------- |
| `LLM_PROVIDER`    | `openai_compatible`                                | Provider identifier        |
| `LLM_BASE_URL`    | `https://api.openai.com/v1`                        | Base URL of the endpoint   |
| `LLM_MODEL`       | `gpt-4o-mini`                                      | Model name                 |
| `LLM_API_KEY`     | *(empty until provisioned)*                        | Secret key                 |
| `LLM_TEMPERATURE` | `0.7`                                              | Sampling temperature       |
| `LLM_MAX_TOKENS`  | `800`                                              | Max completion tokens      |
| `LLM_MOCK_MODE`   | `false`                                            | Offline demo provider      |

**Google Gemini** exposes an OpenAI-compatible endpoint too — minimal changes:

```ini
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
LLM_MODEL=gemini-2.0-flash
LLM_API_KEY=<your Gemini API key>
```

The provider abstraction lives in `backend/services/llm_service.py`
(`LLMProvider` protocol). Adding another provider = implement one class.

Every LLM call returns **structured JSON validated against a Pydantic schema**
(`backend/schemas/llm.py`); malformed output is repaired once and retried.

---

## API documentation

### `POST /api/interview`

The single conversational endpoint. Omit `sessionId` to start a new session.

**Request**

```json
{
  "candidateId": "candidate-1",
  "message": "Hi, I'm ready to start.",
  "sessionId": null
}
```

**Response**

```json
{
  "sessionId": "8f3c2a9e-1c4d-4f6a-9b0c-2e5a7d8f1b3a",
  "state": "INTRODUCTION",
  "message": "Welcome, Alex! I'm your interviewer today…",
  "questionNumber": 0,
  "totalQuestions": 12,
  "currentDay": null,
  "currentTopic": null,
  "interviewComplete": false,
  "feedback": null
}
```

**Continue the session**

```json
{
  "candidateId": "candidate-1",
  "message": "I'm Alex, a junior Python developer working with REST APIs.",
  "sessionId": "8f3c2a9e-1c4d-4f6a-9b0c-2e5a7d8f1b3a"
}
```

```json
{
  "sessionId": "8f3c2a9e-1c4d-4f6a-9b0c-2e5a7d8f1b3a",
  "state": "QUESTIONING",
  "message": "Great, thanks Alex! Let's get started.\n…",
  "questionNumber": 1,
  "totalQuestions": 12,
  "currentDay": "Python Fundamentals",
  "currentTopic": "python-loops",
  "interviewComplete": false,
  "feedback": null
}
```

**Final turn** — when the interview is done, `feedback` carries exactly the
required fields:

```json
{
  "sessionId": "8f3c2a9e-1c4d-4f6a-9b0c-2e5a7d8f1b3a",
  "state": "DONE",
  "message": "Thank you, Alex — that's everything…",
  "questionNumber": 12,
  "totalQuestions": 12,
  "currentDay": null,
  "currentTopic": null,
  "interviewComplete": true,
  "feedback": {
    "summary": "Solid overall performance…",
    "strengths": ["Clear explanations of core concepts"],
    "gaps": ["Production deployment experience is limited"],
    "next": ["Practice system design for the topics covered"]
  }
}
```

> `score`, `confidence` and `topics_covered` are computed internally but are
> **not** part of the API contract.

### `GET /api/interview/{sessionId}`

Full session snapshot (transcript + state + feedback) — used to resume after
a page refresh.

### `GET /api/candidates`

```json
[
  { "id": "candidate-1", "name": "Alex Doe", "role": "Junior Python Developer" }
]
```

### `GET /api/health`

```json
{
  "status": "ok",
  "app": "AI Interview Agent",
  "curriculumDays": 6,
  "candidates": 2,
  "specLoaded": true,
  "llmConfigured": false,
  "mockMode": true,
  "datasetsError": null
}
```

---

## Error handling

| Condition                  | Status | `detail.code`             |
| -------------------------- | ------ | ------------------------- |
| Unknown `candidateId`      | 404    | `candidate_not_found`     |
| Unknown / expired `sessionId` | 404 / 410 | `session_not_found` / `session_expired` |
| Missing datasets           | 503    | `curriculum_unavailable` / `datasets_unavailable` |
| No LLM configured          | 503    | `llm_not_configured`      |
| LLM failure / bad output   | 502    | `llm_error`               |
| Illegal state transition   | 409    | `invalid_state_transition` |
| Malformed request body     | 400    | `malformed_request`       |

All errors share the envelope `{ "detail": { "code", "message", … } }`.

---

## Design decisions

- **Plan first, text on demand** — the plan skeleton (days, topics, question
  types, difficulty ramp) is computed instantly at session start; only the
  question wording is LLM-generated when the question is asked, keeping
  per-turn latency to 1–2 LLM calls.
- **LLM always outputs JSON** — every prompt requests a single JSON object
  validated by Pydantic; no raw-text parsing anywhere.
- **Deterministic transitions** — intro, topic bridges and wrap-up lines are
  templated (no LLM), while evaluation, follow-ups, question wording and
  feedback are LLM-generated.
- **Schema-tolerant datasets** — the loaders accept common field spellings
  and degrade gracefully, so the project adapts to whatever your three files
  actually contain without touching them.
- **In-memory state** — sessions live in `SessionManager` with TTL expiry; no
  database, per the requirements.

## Roadmap ideas

- Streaming tokens from the provider to the chat UI
- Persistent session store (SQLite/Redis) behind the `SessionManager` interface
- Multi-provider fallback and token/cost tracking
- Export feedback as PDF/markdown

---

Generated with Codebuff 🤖 · Co-Authored-By: Codebuff <noreply@codebuff.com>
