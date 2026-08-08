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

# Reaction when the candidate STUMBLED on this topic earlier and has now
# given a good answer — the interviewer recognizes the recovery.
[reaction_recovery]
Much better — 
Yes, that's closer — 
Good recovery — 
That's more like it — 

# First struggle on a topic: still patient.
[reaction_weak]
No worries — 
That's okay — 
Let's come at it another way — 
Alright, let's keep it simple — 

# Second/third consecutive struggle: noticeably more direct.
[reaction_weak2]
Alright, let's make this one easier — 
Okay, let's slow down — 
Let's take a step back — 

# Repeated struggles across the interview: firm, about to move on.  Never
# insulting — just honest about the process.
[reaction_weak3]
I've tried this a couple of ways now — 
Alright, let's leave that one for now — 
Let's move past this one — 

[reaction_claim]
Alright — 
Fair enough — 
Okay — 

# Repeated "I know" without evidence: the interviewer needs the actual
# answer and says so plainly.
[reaction_claim2]
Fair enough — but I still need the answer itself — 
Alright — I can't mark that without seeing it — 
Okay — then let's see it in action — 

[reaction_wrong]
I see — 
There's a subtlety there — 
Let's look at that differently — 

# Transitions when the next topic is RELATED to the previous one.  Short,
# spoken connectors ONLY — never announce the curriculum topic, never
# explain the relationship at length.
[transition_related]

# Transitions when the next topic is a fresh area.  Short and topic-free:
# the interviewer never reads the curriculum title to the candidate.
[transition_new]

# Transition when we stay on the SAME topic (deeper second main question).
[transition_same]

[final_question]
We've covered a good range of topics today. Before we wrap up, do you have
any questions for me — about the curriculum, the field, or how you did?

[wrap_up]
Thank you, {name} — that's everything I had for you today. I'm preparing your
feedback now; it will be ready in just a moment.
