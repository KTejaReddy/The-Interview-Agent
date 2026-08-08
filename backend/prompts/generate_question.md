Generate ONE interview question that assesses exactly the intent below.

CANDIDATE PROFILE
{candidate_summary}
- Strong topics: {strong_topics}
- Weak topics: {weak_topics}
- Knowledge gaps: {knowledge_gaps}

EVIDENCE COLLECTED SO FAR (from actual answers, not the profile)
{assessment_summary}

CANDIDATE'S PREVIOUS ANSWER
{previous_answer}

PREVIOUS QUESTIONS ASKED
{previous_questions}

QUESTION INTENT — assess exactly this
- Curriculum day: Day {day_number} — {day_title}
- Module: {module}
- Learning objective: {learning_objective}
- Technical concept: {concept}
- Question type: {question_type} ({cognitive_level})
- Purpose: {purpose}
- Expected evidence: {expected_evidence}
- Difficulty: {difficulty}
- Selected because: {candidate_signal}

CURRICULUM GROUNDING (use ONLY this; never invent curriculum)
{curriculum_context}

CONVERSATIONAL CONTEXT
- Previous topic: {previous_topic}
- Relationship: {relationship}
- Candidate mentioned earlier: {candidate_mentions}
- Position: question {question_number} of {total_questions}
- Topics covered: {topics_covered}
- Consecutive weak answers: {consecutive_weak}

INTERVIEWER STATE (internal — calibrate tone, never quote it)
{interviewer_state}

RECENT CONVERSATION (most recent turns, verbatim)
{conversation_so_far}

RULES
- Read RECENT CONVERSATION + EVIDENCE + INTERVIEWER STATE + "Candidate
  mentioned earlier" before asking — together they carry the whole
  interview; do not behave as if you only saw the last answer.
- One focused question, one main idea, under ~30 words, spoken-natural.
  Never "and"-stacked. Assess the {concept} concept via the objective above.
- {day_title} is a course label, not a concept. Never ask "What is <day
  title>?". Ask about the concept/objective.
- Vary the angle with evidence: if the concept was already explained, ask to
  apply, trace, debug or trade off — never re-ask the same thing at the same
  level. Detect semantic similarity to PREVIOUS QUESTIONS ASKED; if the
  objective was assessed, change the cognitive task.
- REACTION field: a SHORT natural reaction to the candidate's LAST answer,
  based on what they actually said — acknowledge the correct part, target
  the missing piece, gently identify the misconception, or recognize a
  recovery. Calibrate to INTERVIEWER STATE. One short sentence, often a few
  words. Must read as a complete standalone phrase — NEVER end it with a
  dangling connector ("but", "and", "so", "also", "though") or leave it
  mid-thought. Empty string when no reaction is natural (e.g. moving on
  after repeated failures). May include a natural bridge into the question.
- QUESTION field: a single pure question. The engine assembles reaction +
  question; if your reaction is empty it adds its own short transition.
- Match the requested difficulty: {difficulty}.

Respond with a JSON object only:
{{"question": "...", "reaction": "...", "topic": "...", "intent": "...", "question_type": "{question_type}"}}
