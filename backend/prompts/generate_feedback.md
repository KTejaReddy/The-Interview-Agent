The interview is finished. Write structured final feedback for the
candidate based ONLY on what was actually demonstrated during the interview.

FULL INTERVIEW TRANSCRIPT
{transcript}

CANDIDATE PROFILE
{candidate_summary}

AGGREGATE STATS
{aggregate_summary}

ASSESSMENT STATE (per-topic, derived from the actual interview)
{assessment_state}

PROFILE TOPICS NOT TESTED IN THIS INTERVIEW (do NOT make claims about these)
{not_tested}

RULES
- Base EVERY claim on the ASSESSMENT STATE and TRANSCRIPT. Do not invent
  evidence and do not infer knowledge from the candidate profile alone.
- Completing a mission in the cohort is NOT interview evidence. Saying "I
  know" or "yes" is NOT evidence. Never list either as a strength.
- If a topic in the transcript shows low confidence or repeated failures,
  phrase gaps as: "Did not demonstrate sufficient understanding of X during
  the interview."
- Never diagnose psychology ("low confidence", "not interested", "poor
  attitude"). "I don't know" means insufficient demonstrated evidence — state
  what was and was not demonstrated, objectively.
- "strengths" (2-4 items): what the candidate demonstrably did well, citing
  the specific answers that showed it.
- "gaps" (2-4 items): the weakest areas SHOWN during the interview, phrased
  as demonstrated evidence, not personality.
- "next" (2-4 items): concrete, actionable suggestions to study next, tied to
  the topics actually covered, ordered by priority.
- "summary" (2-4 sentences): a balanced overall assessment. Encourage but
  stay honest.
- "score" is an integer 0-100 overall performance rating based on the actual
  answers.
- "confidence" is a float 0.0-1.0 estimating how confident the candidate
  seemed during the interview.
- "topics_covered" is the list of topics actually discussed.

Respond with a JSON object only:
{{"summary": "...", "strengths": ["..."], "gaps": ["..."],
  "next": ["..."], "score": <0-100>, "confidence": <0.0-1.0>,
  "topics_covered": ["..."]}}
