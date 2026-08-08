The interview is finished. Write structured final feedback for the
candidate based on the full interview transcript.

FULL INTERVIEW TRANSCRIPT
{transcript}

CANDIDATE PROFILE
{candidate_summary}

AGGREGATE STATS
{aggregate_summary}

ASSESSMENT STATE
{assessment_state}

RULES
- Be specific and concrete. Reference actual topics and answers. Evidence must be derived from the interview, not just the profile.
- "strengths" (2-4 items): what the candidate did well, with evidence.
- "gaps" (2-4 items): the weakest areas shown during the interview.
- "next" (2-4 items): concrete, actionable suggestions to study next,
  ordered by priority.
- "summary" (2-4 sentences): a balanced overall assessment. Encourage but
  stay honest.
- "score" is an integer 0-100 overall performance rating.
- "confidence" is a float 0.0-1.0 estimating how confident the candidate
  seemed.
- "topics_covered" is the list of topics actually discussed.

Respond with a JSON object only:
{{"summary": "...", "strengths": ["..."], "gaps": ["..."],
  "next": ["..."], "score": <0-100>, "confidence": <0.0-1.0>,
  "topics_covered": ["..."]}}
