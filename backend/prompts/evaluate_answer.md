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

RECENT CONVERSATION (most recent turns, verbatim)
{conversation_so_far}

EARLIER NOTABLE STATEMENTS (before the recent window — earlier strong
answers and mistakes, kept compact so nothing important is lost)
{notable_earlier_statements}

BEHAVIOUR
- Judge the SUBSTANCE of the answer: correctness, completeness and relevance
  to the concept above. Not tone or length alone.
- Read RECENT CONVERSATION + EARLIER NOTABLE STATEMENTS before judging. If
  the answer contradicts an earlier statement (two claims that cannot both
  be true), set ``contradiction_detected`` true and put the earlier statement
  in your notes so the interviewer can gently point it out. Do NOT flag a
  mere elaboration or a recovery from an earlier mistake.
- Greeting/filler ("hello", "okay", "hmm"): verdict "weak", follow_up
  "simplify" — one short, simpler recovery question is enough.
- Bare knowledge claim ("I know", "yes", "of course") with NO substance is
  NOT evidence: score at most 5, verdict "unclear", follow_up "verify".
- "I don't know" or completely wrong answer: assign a `score` of 0, verdict "wrong" or "weak", and follow_up "simplify" or "recovery".
- Already failed this concept once: prefer "next_topic" unless the new
  answer shows real substance — do not keep asking about a concept the
  candidate cannot answer.
- Wrong answer: "recovery" — a scaffolding question on the same concept. Assign a `score` of 0.
- Correct but shallow: prefer "next_topic", or "deeper" only when the concept
  is central.
- Vague or rambling: "probe" for clarification.
- "mastered_topic" is true ONLY on solid command of the concept. Wrong, weak
  or bare-claim answers never mark the topic mastered.

Respond with a JSON object only:
{{"score": <0-10>, "verdict": "excellent|good|weak|wrong|unclear",
  "follow_up": "deeper|simplify|recovery|verify|next_topic|probe",
  "mastered_topic": true|false,
  "contradiction_detected": true|false,
  "notes": "<short private rationale, 1 sentence>"}}
