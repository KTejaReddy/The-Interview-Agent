Generate ONE interview question for the candidate.

CANDIDATE PROFILE
{candidate_summary}
- Strong topics: {strong_topics}
- Weak topics: {weak_topics}
- Knowledge gaps: {knowledge_gaps}

CURRICULUM GROUNDING (use ONLY this content; never invent curriculum)
{curriculum_context}

PREVIOUS QUESTIONS ASKED
{previous_questions}

QUESTION SPEC
- Topic: {topic}
- Question type: {question_type}
- Difficulty: {difficulty}
- Position in interview: question {question_number} of {total_questions}
- Topics already covered: {topics_covered}

CONSTRAINTS
- Ask exactly one question, phrased the way a senior interviewer would speak it aloud. Do not include preamble, bullets or meta commentary.
- The question must be answerable from the curriculum topic above.
- Match the requested difficulty: {difficulty}.
- DO NOT REPEAT OR REPHRASE any question from PREVIOUS QUESTIONS ASKED. Detect semantic similarity. If this topic was asked before, change the cognitive task (e.g. from explanation to scenario).
- If this is not the first question, include a short, natural, conversational transition before asking the question. Do NOT use generic phrases like "Let's move on to the next topic." Instead, connect it conceptually if possible (e.g., "Let's approach this from another angle.", "Now I'd like to explore the retrieval side of that.").

Respond with a JSON object only:
{{"question": "...", "topic": "...", "intent": "...", "question_type": "{question_type}"}}
