The candidate has just answered a question. Generate a natural follow-up
question that continues the conversation on the SAME curriculum day.

ORIGINAL QUESTION
{question}

CURRICULUM DAY BEING ASSESSED
- Day: {day_title}
- Module: {module}
- Learning objective: {learning_objective}
- Technical concept: {concept}
- Expected evidence: {expected_evidence}

CURRICULUM GROUNDING (use ONLY this; never invent curriculum)
{curriculum_context}

CANDIDATE'S ANSWER
{answer}

EVALUATION
- Verdict: {verdict}
- Score: {score}/10
- Follow-up strategy: {strategy}
- Notes: {notes}
- Follow-ups so far on this topic: {follow_up_count}
- Consecutive weak answers in the interview: {consecutive_weak}

FOLLOW-UP STRATEGY MEANING
- deeper: good answer, follow-up #{follow_up_count} on this topic — go ONE
  cognitive level up from the previous question (application → scenario →
  debugging → trade-off → architecture → production). Do NOT re-ask an
  explanation or another example. Probe the next missing dimension (edge
  case, trade-off, architectural consequence) and build on something the
  candidate just said.
- simplify: struggled or "I don't know". DO NOT repeat or rephrase the
  question. Ask a clearly different, easier question — a concrete analogy or
  a single concrete example.
- recovery: wrong or struggling again. Ask a scaffolding question that
  gently guides back on track using a concrete scenario from the objective.
- verify: asserted knowledge ("I know", "yes") without evidence. Do NOT
  reward the claim. Ask for a concrete scenario or worked example.
- probe: unclear answer, or the notes say the answer contradicted an earlier
  statement. Ask them to clarify the specific point.
- If the notes mention a contradiction, gently point it out ("That's
  different from what you said earlier — …") and ask which they meant. Never
  quote internal scores or verdicts.
- Struggling repeatedly (high consecutive weak): patient but increasingly
  direct — acknowledge once, ask the simpler question. Never lecture, never
  repeat phrasing, never insult.

PREVIOUS QUESTIONS (recent ones — do not re-ask or paraphrase any)
{previous_questions}

RULES
- Stay on this day ({day_title}). Never jump topics.
- NEVER phrase it as "What is <day title>?". Ask about the {concept} concept
  and the objective.
- Reference something the candidate just said, so it feels like a real
  conversation.
- Exactly one question, under ~30 words, spoken-natural. No preamble, no
  bullets, no meta commentary.
- At most one short varied opener ("Good.", "Right.", "Let's try a simpler
  angle.") — or none. Never stock phrases ("Glad to hear it", "Let's make
  sure we're on the same page").
- Target difficulty: {difficulty}

Respond with a JSON object only:
{{"question": "...", "intent": "...", "difficulty": "easy|medium|advanced"}}
