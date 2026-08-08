Evaluate the candidate's answer to the last interview question and decide
how the interviewer should proceed.

QUESTION
{question}

QUESTION CONTEXT
- Topic: {topic}
- Question type: {question_type}
- Intended difficulty: {difficulty}
- Intent: {intent}
- Learning objective assessed: {learning_objective}
- Technical concept: {concept}

CANDIDATE'S ANSWER
{answer}

CANDIDATE PROFILE
{candidate_summary}

CONVERSATION SO FAR
{aggregate_summary}

RECENT CONVERSATION (the most recent turns, verbatim)
{conversation_so_far}

EARLIER NOTABLE STATEMENTS (from before the recent window — the candidate's
earlier strong answers and mistakes, kept compact so nothing important is lost)
{notable_earlier_statements}

BEHAVIOUR
- Judge the SUBSTANCE of the answer: correctness, completeness and relevance
  to the concept above. Do not judge by tone or length alone.
- Read the RECENT CONVERSATION and EARLIER NOTABLE STATEMENTS before
  judging. If the candidate's current answer contradicts something they said
  earlier in this interview (two claims that cannot both be true — e.g.
  earlier "the vector database creates the embeddings", now "the embedding
  model creates the embeddings"), set ``contradiction_detected`` to true and
  put the earlier statement in your notes so the interviewer can gently
  point out the discrepancy and ask which they meant. Do NOT flag a mere
  elaboration or a recovery from an earlier mistake as a contradiction.
- A greeting ("hello", "hi") or filler ("okay", "hmm") is a non-substantive
  response: verdict "weak", follow_up "simplify" — one short, simpler
  recovery question is enough.
- A bare knowledge claim ("I know", "yes", "I understand", "of course") with
  NO substantive content is NOT evidence. Score it at most 5, verdict
  "unclear", follow_up "verify" — the interviewer will ask for evidence.
- If the candidate says "I don't know" or similar, use verdict "weak" and
  follow_up "simplify" (the interviewer will ask a different, easier
  diagnostic question).
- If the candidate already failed this concept once, prefer "next_topic"
  unless the new answer demonstrates real substance — a real interviewer
  does not keep asking about a concept the candidate cannot answer.
- If the answer is wrong, use "recovery": the interviewer will ask a
  scaffolding question on the same concept.
- If the answer is correct but shallow, prefer "next_topic", or "deeper" only
  when the concept is central to the interview.
- If the answer is vague or rambling, use "probe" to ask for clarification.
- "mastered_topic" is true ONLY when the answer demonstrates solid command of
  the concept. A wrong answer, a weak answer, or a bare claim never marks the
  topic as mastered.

Respond with a JSON object only:
{{"score": <0-10>, "verdict": "excellent|good|weak|wrong|unclear",
  "follow_up": "deeper|simplify|recovery|verify|next_topic|probe",
  "mastered_topic": true|false,
  "contradiction_detected": true|false,
  "notes": "<short private rationale, 1 sentence>"}}
