# Deterministic interviewer messages
# These transitions do not need the LLM; they keep latency low and the flow
# consistent. Placeholders use Python str.format syntax.

[intro]
Welcome, {name}! I'm your interviewer today. Let's get started.

[first_question_bridge]
{question}

[next_question_bridge]
{question}

[final_question]
We've covered a good range of topics today. Before we wrap up, do you have
any questions for me — about the curriculum, the field, or how you did?

[wrap_up]
Thank you, {name} — that's everything I had for you today. I'm preparing your
feedback now; it will be ready in just a moment.
