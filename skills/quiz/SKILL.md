---
name: quiz
description: Quiz the learner. Use when they say "quiz me", "test me", "check my knowledge", "practice questions", or run /teaching-harness:quiz. One question at a time, adaptive, results recorded.
---

# Quiz: retrieval practice, one question at a time

Quizzing works because the learner has to *pull the answer out of their own head*. Anything that lets them skim the answer first defeats it.

## 1. Choose the topic
- A roadmap milestone is active -> `quiz pick` lists its concepts first; quiz those, and record answers under the exact concept names from the milestone.
- They named one ("quiz me on pointers") -> use it.
- Otherwise run `python3 "${CLAUDE_PLUGIN_ROOT}/bin/teach.py" quiz pick`. It ranks concepts by weakness and staleness. Offer the top 2-3 in one line and let them choose,
  or just start with the top one if they said "anything".
- If it prints `NO HISTORY`, ask one open question: what do they want to be tested on? (Use their goals / current project as suggestions.)

## 2. Start
`teach.py quiz start "<topic>"` (add `--mc` if they asked for a "quick" quiz). It sets the starting difficulty and tells you the question style for it.
Default length is 5 questions; they can say "stop" any time. Say how it works in one line, then ask question 1.

## 3. Each question
- **One question per message.** Never list several. Never include the answer, or hints, in the question.
- **Match the difficulty tag** from the CLI: recall, read & predict, spot the bug/fill the blank, modify/compare, unfamiliar territory.
- **Use their own world** when you can: read their project files (read-only) and quiz on code they wrote or on the thing they're building (e.g. their shell).
- **Verify before you ask.** For any predict-the-output / spot-the-bug question, put the snippet in `.teach/scratch/`, compile/run it, and confirm the real answer.
  An unverified answer key is the fastest way to teach something wrong. Keep snippets <= ~12 lines, and one concept per question.
- **Open-ended (default):** they answer in their own words or code. **Multiple choice (`--mc`):** 4 options, plausible distractors built from *real* misconceptions,
  and vary which letter is correct (don't favour B/C).
- Then **stop and wait.**

## 4. Mark their answer
- Judge the substance, not the phrasing. Right idea with sloppy wording = pass. Right answer for a wrong reason = partial.
- Run `teach.py quiz answer pass|fail|partial ["specific concept"]` - **first attempt only**. A retry never upgrades the record.
- **Pass:** confirm *why* it's right in one sentence (reinforces it), add one small extension thought if useful, next question.
- **Fail/partial:** name what was right, ask a narrowing question or give a smaller hint, let them retry once. If they still miss, explain it
  briefly, then ask a *fresh variant* later in the quiz instead of moving on forever. Mistakes are information; keep the tone steady.
- If they say "I don't know", don't reveal the answer. Offer the next hint-ladder step (`teach.py hint`) or a smaller version of the question.

## 5. Wrap up
After the last question (or when they stop): `teach.py quiz end`, then summarise in 3-4 lines: what was solid, what to revisit, and one concrete next step
(e.g. a small exercise, or offer a `diagram` for the concept they missed). Don't give a numeric "grade" as the headline; the point is the next step.
