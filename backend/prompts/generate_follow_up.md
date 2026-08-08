The candidate has just answered a question. Generate a natural follow-up
question that continues the conversation on the SAME topic.

ORIGINAL QUESTION
{question}

CANDIDATE'S ANSWER
{answer}

EVALUATION
- Verdict: {verdict}
- Score: {score}/10
- Follow-up strategy: {strategy}
- Notes: {notes}

CURRICULUM GROUNDING (use ONLY this content; never invent curriculum)
{curriculum_context}

FOLLOW-UP STRATEGY MEANING
- deeper: the answer was good. Go one level deeper — probe nuance, edge
  cases, trade-offs or a small architectural consequence.
- simplify: the candidate struggled or said "I don't know". DO NOT repeat the same question. Ask a clearer, easier conceptual question, or use a concrete analogy to help them build a foundation.
- recovery: the answer was wrong. Ask a scaffolding question that gently
  guides the candidate back on track without embarrassing them.
- probe: the answer was unclear. Ask them to clarify or elaborate on the
  point they were making.

CONSTRAINTS
- Stay on the topic "{topic}". Do not jump to a new topic.
- Reference something the candidate just said, so it feels like a real
  conversation.
- Ask exactly one question. No preamble, no bullets, no meta commentary.
- Target difficulty: {difficulty}

Respond with a JSON object only:
{{"question": "...", "intent": "...", "difficulty": "easy|medium|advanced"}}
