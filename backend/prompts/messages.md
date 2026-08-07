# Deterministic interviewer messages
# These transitions do not need the LLM; they keep latency low and the flow
# consistent. Placeholders use Python str.format syntax.

[intro]
Welcome, {name}! I'm your interviewer today — I'll be asking about the topics
from your learning track, starting from the basics and going as deep as we can.
There are no wrong answers that cost you anything; just do your best.
First, could you introduce yourself briefly and tell me what you've been
working on lately?

[first_question_bridge]
Great, thanks {first_name}! Let's get started.
{question}

[next_question_bridge]
Let's move on to the next topic.
{question}

[final_question]
We've covered a good range of topics today. Before we wrap up, do you have
any questions for me — about the curriculum, the field, or how you did?

[wrap_up]
Thank you, {name} — that's everything I had for you today. I'm preparing your
feedback now; it will be ready in just a moment.
