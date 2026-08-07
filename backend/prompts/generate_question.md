Generate ONE interview question for the candidate.

CANDIDATE PROFILE
{candidate_summary}
- Strong topics: {strong_topics}
- Weak topics: {weak_topics}
- Knowledge gaps: {knowledge_gaps}

CURRICULUM GROUNDING (use ONLY this content; never invent curriculum)
{curriculum_context}

QUESTION SPEC
- Topic: {topic}
- Question type: {question_type}
- Difficulty: {difficulty}
- Position in interview: question {question_number} of {total_questions}
- Topics already covered: {topics_covered}

CONSTRAINTS
- Ask exactly one question, phrased the way a senior interviewer would speak
  it aloud. Do not include preamble, bullets or meta commentary.
- The question must be answerable from the curriculum topic above.
- Match the requested difficulty: {difficulty}.
- Do not repeat a question that was already asked.

Respond with a JSON object only:
{{"question": "...", "topic": "...", "intent": "...", "question_type": "{question_type}"}}
