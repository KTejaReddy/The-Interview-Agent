# Deterministic interviewer messages
# These transitions do not need the LLM; they keep latency low and the flow
# consistent. Placeholders use Python str.format syntax.
#
# Sections whose content is one entry per line are ROTATION POOLS: the
# bridge picks an entry deterministically (by turn index) so the same stock
# phrase is never repeated back-to-back.  Keep any comments ABOVE the header
# they describe — the section parser reads everything between headers.

[intro]
Hi {name}, welcome to the interview.

[first_question_bridge]
Hi {first_name}, thanks for joining. I've looked at your progress through the
cohort — let's start with something from your journey: {question}

# Reactions to the previous answer, keyed by the last verdict.  Short,
# spoken-natural, human acknowledgements — never "Glad to hear it" style.
[reaction_good]
Good — 
Nice — 
Right — 
Exactly — 
That's solid — 
Good thinking — 

[reaction_weak]
No worries — 
That's okay — 
Let's come at it another way — 
Alright, let's keep it simple — 

[reaction_claim]
Alright — 
Fair enough — 
Okay — 

[reaction_wrong]
I see — 
There's a subtlety there — 
Let's look at that differently — 

# Transitions when the next topic is RELATED to the previous one.  Short,
# spoken connectors ONLY — never announce the curriculum topic, never
# explain the relationship at length.
[transition_related]
and related to that — 
and since those connect — 
one more thing on that thread — 

# Transitions when the next topic is a fresh area.  Short and topic-free:
# the interviewer never reads the curriculum title to the candidate.
[transition_new]
let's switch gears for a moment — 
let's try something else — 
okay, let's move on — 
one more thing — 

# Transition when we stay on the SAME topic (deeper second main question).
[transition_same]
let's push a bit deeper on that — 
let's stay on that a moment longer — 
one more angle on this — 

[final_question]
We've covered a good range of topics today. Before we wrap up, do you have
any questions for me — about the curriculum, the field, or how you did?

[wrap_up]
Thank you, {name} — that's everything I had for you today. I'm preparing your
feedback now; it will be ready in just a moment.
