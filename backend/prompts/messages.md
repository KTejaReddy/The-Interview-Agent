# Deterministic interviewer messages
# These transitions do not need the LLM; they keep latency low and the flow
# consistent. Placeholders use Python str.format syntax.

[intro]
Hi {name}, welcome to the interview.

[first_question_bridge]
Hi {first_name}, thanks for joining. I've looked at your progress through the
cohort — let's start with something from your journey: {question}

[next_question_bridge]
{question}

[final_question]
We've covered a good range of topics today. Before we wrap up, do you have
any questions for me — about the curriculum, the field, or how you did?

[wrap_up]
Thank you, {name} — that's everything I had for you today. I'm preparing your
feedback now; it will be ready in just a moment.
