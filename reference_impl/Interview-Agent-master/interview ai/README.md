# AI Interview Agent

An AI-powered technical interview platform built for the **ABTalks AI Cohort Hackathon**.

It conducts personalized, multi-turn technical interviews based on a candidate's real learning journey through the 31-day AI Engineering cohort, then generates structured feedback at the end.

**Live Demo:** *(add your Vercel URL here)*

---

## What it does

- Selects a candidate from 20 real cohort profiles
- Conducts a conversational interview tailored to what they actually completed
- Asks a minimum of 8 questions across 4+ curriculum days
- Generates follow-up questions based on each response
- Streams interviewer replies live, token by token - no more waiting for the full bubble
- Accepts answers by **voice** (Web Speech API, mic button in the chat input)
- **Survives page refreshes** - your in-progress interview is saved to the browser
- Produces structured feedback: summary, strengths, gaps, next steps, overall score, and topic scores

---

## Tech Stack

- **Frontend** - Next.js 14, Tailwind CSS, Framer Motion, Zustand
- **Backend** - Next.js API Routes
- **AI** - Groq (llama-3.3-70b-versatile) - free tier

---

## Getting Started

```bash
# Install dependencies
npm install

# Add your Groq API key (free at console.groq.com)
cp .env.local.example .env.local

# Run locally
npm run dev
```

Open http://localhost:3000

### Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `GROQ_API_KEY` | - | Required. Groq API key. |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Model used for interviews + feedback. |
| `MIN_QUESTIONS_REQUIRED` | `8` | Minimum questions before the interview may end. |
| `MIN_DAYS_REQUIRED` | `4` | Minimum distinct curriculum days that must be covered. |
| `MAX_QUESTIONS_PER_SESSION` | `14` | Hard cap on questions per session. |
| `SESSION_TIMEOUT_MS` | `7200000` | In-memory session expiry (2 hours). |

---

## API

`POST /api/interview`

The endpoint returns **JSON** by default; send the header `Accept: text/event-stream` to receive the reply streamed as Server-Sent Events (`token` events, then a `done` event). The JSON contract below is unchanged for non-streaming clients.

**Start interview:**

```json
{ "sessionId": "abc-123", "candidate": { "...candidate object..." } }
```

**Send a response:**

```json
{ "sessionId": "abc-123", "message": "..." }
```

**When the interview is complete:**

```json
{
  "reply": "Thanks for your time...",
  "done": true,
  "feedback": {
    "summary": "...",
    "strengths": ["..."],
    "gaps": ["..."],
    "next": ["..."]
  }
}
```

---

*Built for the ABTalks AI Cohort Hackathon. All candidate data is synthetic.*
