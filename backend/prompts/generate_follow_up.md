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

CURRICULUM GROUNDING (use ONLY this content; never invent curriculum)
{curriculum_context}

CANDIDATE'S ANSWER
{answer}

EVALUATION
- Verdict: {verdict}
- Score: {score}/10
- Follow-up strategy: {strategy}
- Notes: {notes}
- Follow-ups so far on this topic: {follow_up_count}

FOLLOW-UP STRATEGY MEANING
- deeper: the answer was good. This is follow-up #{follow_up_count} on this
  topic — go ONE COGNITIVE LEVEL UP from the previous question (application →
  scenario → debugging → trade-off → architecture → production). Do NOT ask
  another explanation or another "give me an example" — the candidate already
  explained it. Probe the next missing dimension (edge case, trade-off,
  architectural consequence) and base it on something the candidate just said.
- simplify: the candidate struggled or said "I don't know". DO NOT repeat the
  question and DO NOT rephrase it. Ask a clearly different, easier question
  about the concept — a concrete analogy or a single concrete example.
- recovery: the answer was wrong or the candidate is struggling again. Ask a
  scaffolding question that gently guides them back on track using a concrete
  scenario grounded in the learning objective above.
- verify: the candidate asserted knowledge ("I know", "yes") without providing
  evidence. Do NOT reward the claim and do NOT just take their word for it.
  Ask them to demonstrate it with a concrete scenario or worked example from
  the learning objective above.
- probe: the answer was unclear. Ask them to clarify or elaborate on the
  specific point they were making.

PREVIOUS QUESTIONS (do not re-ask or paraphrase ANY of these)
{previous_questions}

RULES
- Stay on this curriculum day ({day_title}). Do not jump to a new topic.
- NEVER phrase the follow-up as "What is <day title>?" — ask about the
  {concept} concept and the learning objective instead.
- Reference something the candidate just said, so it feels like a real
  conversation.
- Ask exactly one question. No preamble, no bullets, no meta commentary.
- Maximum ONE short acknowledgement before the question ("Good.", "Right.",
  "Let's try a simpler angle.") — or none at all. Vary your openers; never
  repeat stock phrases like "Glad to hear it", "Let's make sure we're on the
  same page", or "No problem — let's ground this differently".
- Keep the whole follow-up short and spoken-natural (aim under ~30 words).
  Do not describe the candidate's previous sentence back to them at length.
- Target difficulty: {difficulty}

Respond with a JSON object only:
{{"question": "...", "intent": "...", "difficulty": "easy|medium|advanced"}}
