Evaluate the candidate's answer to the last interview question and decide
how the interviewer should proceed.

QUESTION
{question}

QUESTION CONTEXT
- Topic: {topic}
- Question type: {question_type}
- Intended difficulty: {difficulty}
- Intent: {intent}

CANDIDATE'S ANSWER
{answer}

CANDIDATE PROFILE
{candidate_summary}

CONVERSATION SO FAR
{aggregate_summary}

BEHAVIOUR
- Be fair and encouraging. A short but correct answer can still be "good".
- If the answer is correct but shallow, prefer "next_topic" or a "deeper"
  follow-up only when the topic is central to the interview.
- If the answer is wrong, use "recovery": the interviewer will ask a simpler
  scaffolding question on the same topic.
- If the candidate says "I don't know" or similar, use "simplify".
- If the answer is weak or incomplete, use "simplify" so the interviewer can
  ask a clearer, easier version.
- If the answer is vague or rambling, use "probe" to ask for clarification.
- "mastered_topic" is true only when the answer demonstrates solid command
  of the topic. A wrong or weak answer does not mark the topic as mastered.

Respond with a JSON object only:
{{"score": <0-10>, "verdict": "excellent|good|weak|wrong|unclear",
  "follow_up": "deeper|simplify|recovery|next_topic|probe",
  "mastered_topic": true|false,
  "notes": "<short private rationale, 1 sentence>"}}
