---
name: onboard
description: First-session onboarding for the Teaching Harness. Use when the learner profile is not onboarded yet, or the learner asks to redo their goals/level.
---

# Onboarding: start broad

**First check:** if the learner's first message already names a concrete goal ("I want to build a shell in C"), do NOT ask the broad question below.
Use the `roadmap` skill straight away - it asks about their level and scope and marks them onboarded. Everything else here is for learners who haven't said what they want yet.

Keep this to a short conversation, not a form. Ask **one question at a time**, and start with the widest one:

1. "What do you want to get out of this?" (a project, a job skill, a language, a concept, 'just get better')
2. Follow their answer. Ask only what you need to pick a first exercise: what they've built before, what language
   they're comfortable in, what felt confusing recently.
3. Offer a *tiny* diagnostic (one small task or question) to calibrate - not a quiz battery.

Then record what you learned:
- `teach.py goal "<their words>"` for each goal
- `teach.py set level "<junior|junior+|...>"`
- `teach.py concept "<topic>" pass|fail` from the diagnostic
- `teach.py set onboarded true`

If their goal is a multi-step project ("build a shell", "make a game"), hand over to the `roadmap` skill instead of improvising a plan.
Otherwise finish by proposing a first step, narrowed to what they said, and ask if it's right. They can always change direction.
Mention once that `/teaching-harness:mode` switches between learn, pair and review.
