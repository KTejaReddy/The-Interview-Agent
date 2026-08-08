# 🤖 AI Usage Log

This document logs the AI tools used during the development of the **AI Interview Agent**.

---

## Tools Used

| Tool | Purpose |
|------|---------|
| **Freebuff (Buffy)** — AI coding agent | Generated the entire application codebase from the requirements in `prompt.md` and `technical-spec.md`: Next.js scaffolding, API route, interview agent logic, prompt builders, Zustand state, UI components and pages. |
| **Groq API — `llama-3.3-70b-versatile`** | The interview LLM. The application itself is an AI product: it conducts live technical interviews and generates structured feedback. |
| **DiceBear Avataaars API** | Generated candidate avatars (`https://api.dicebear.com/7.x/avataaars/svg?seed={name}`). |

## How AI Was Used in This Build

1. **Requirements analysis** — `prompt.md` was read in full and treated as the single source of truth; the API contract in `technical-spec.md` was implemented verbatim.
2. **Code generation** — All source files (types, lib modules, API route, components, pages, config) were produced by the AI coding agent, then validated with TypeScript typechecking and a production build.
3. **Runtime AI** — During an interview, the agent sends the candidate's profile + curriculum context to Groq, adapts follow-up questions based on responses, detects completion, and generates a grounded feedback report (temperature 0.1) from the actual transcript.
4. **Testing** — The agent validated the API error paths with curl and verified the UI flow in a live browser preview (with stubbed API responses for the demo flow, since no production API key was committed).

## Enhancement Pass (post-build)

A follow-up polish pass added: **streaming replies** (interviewer messages stream token-by-token over SSE, with the JSON API contract preserved for non-streaming clients), **voice answers** (Web Speech API mic input), **refresh-safe sessions** (Zustand persist to localStorage), **API hardening** (message length caps, no internal error details leaked), and a **design pass** (Space Grotesk display type, richer landing hero with stats + how-it-works, reduced-motion and keyboard-focus support).

## Notes

- All interview data (`candidates.json`, `curriculum.json`) is synthetic and provided by the hackathon organizers.
- No candidate personal data is stored outside the in-memory session store; sessions expire after 2 hours of inactivity.
- A running transcript is kept in the browser (localStorage) so a page refresh never loses an in-progress interview.
