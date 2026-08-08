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
- Question type: {question_type}
- Cognitive task: {question_type} ({cognitive_level})
- Purpose: {purpose}
- Expected evidence: {expected_evidence}
- Difficulty: {difficulty}
- Selected because: {candidate_signal}

CURRICULUM GROUNDING (use ONLY this content; never invent curriculum)
{curriculum_context}

CONVERSATIONAL CONTEXT
- Previous topic: {previous_topic}
- Relationship to previous topic: {relationship}
- Candidate mentioned earlier: {candidate_mentions}
- Position in interview: question {question_number} of {total_questions}
- Topics already covered: {topics_covered}

RULES
- Ask exactly one question that assesses the LEARNING OBJECTIVE above through
  the {concept} concept. The question must be answerable using ONLY the
  curriculum content provided above.
- ONE focused question, ONE main idea. Never stack multiple questions with
  "and". If you want to ask about several things, ask about the most
  important one — the next turn will follow the answer.
- Keep it short and spoken-natural (aim under ~30 words). Avoid formal exam
  framing such as "In the context of our enterprise healthcare chatbot
  architecture…". Use the project context only when it genuinely frames the
  concept; otherwise ask plainly about the concept.
- The day title ("{day_title}") is a course label, NOT a concept. NEVER phrase
  the question as "What is <day title>?" or "Explain <day title>". Ask about
  the concept and objective instead.
- Vary the angle based on the evidence collected: if the candidate already
  explained the concept, ask them to apply, trace, debug or trade it off
  rather than explain it again.
- Do NOT repeat or rephrase any question from PREVIOUS QUESTIONS ASKED. Detect
  semantic similarity; if this objective was already assessed, change the
  cognitive task (e.g. from explanation to scenario).
- If the candidate mentioned one of the concepts above earlier, you MAY
  naturally reference their own words — but only if it fits naturally; never
  force it, and never open with a robotic "You mentioned X earlier" on every
  question.
- If this is not the first question, open with a short, natural, conversational
  transition. If the previous topic is related (see "Relationship to previous
  topic"), connect them conceptually. Never use generic phrases like "Let's
  move on to the next topic."
- Never reveal internal profile metadata (attempt counts, mission statuses,
  learning signals). You may subtly reflect that the candidate covered the
  material.
- Phrase it the way a senior interviewer would speak it aloud: specific,
  natural, one question only. No preamble, no bullets, no meta commentary.
- Match the requested difficulty: {difficulty}.

Respond with a JSON object only:
{{"question": "...", "topic": "...", "intent": "...", "question_type": "{question_type}"}}
