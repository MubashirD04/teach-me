---
name: roadmap
description: Plan and track a multi-step project goal (e.g. "I want to build a shell in C") as a beginner-friendly milestone outline. Use when the learner states a big goal and has no roadmap, asks for an outline/plan/where to start, or wants to see or change their progress.
---

# Roadmap: a clear path, without the answers

Turn a big goal into 5-8 small, checkable milestones and keep the learner on them. The plan names *what* they'll meet, never *how to do it*.

**Start immediately.** The learner stated a goal, so begin with the first scoping question. Never ask "do you want a roadmap?".
If a roadmap already exists, run `python3 "${CLAUDE_PLUGIN_ROOT}/bin/teach.py" roadmap status` and show progress instead.

## 1. Scope (max 3 questions, ONE per message)
Use AskUserQuestion (clickable options) if you have it; otherwise numbered options in plain text.
- **Never bundle questions.** Give 2-4 options labelled in words with a short example, never bare letters (A/B/C): "C" is ambiguous in a C conversation. Recommended option first.
- Order: scope ("smallest version you'd be proud of?"), then experience ("what have you written so far?"). A third only if it changes the plan.
- Recap each answer in one line ("Got it: ..."). If it's unclear, ask one short clarification; never silently assume. "Skip" or "no idea" is fine: pick defaults and say what you assumed.

## 2. Draft the outline in chat (save only after they approve)
Show each milestone in exactly this layout: bold labels, blank lines between, the First step as its own blockquote.

**1. Show a prompt and echo a line**

**Outcome:** your program waits for a line and repeats it back.

**Done when:** you run `./myshell`, see `$ `, type `hello`, and it prints `you typed: hello`; Ctrl-D exits cleanly.

**Concepts you'll meet:**
- **stdin** - where a program's keyboard input arrives
- **buffering** - why output may not appear until a newline

**Look up:** `man 3 getline`

> **First step (about 10 minutes):** Write a tiny program that prints a `$ ` prompt once with a newline and once without, then waits a few seconds (look up `sleep`). Does the `$ ` appear straight away each time? Tell me what you saw.

Rules:
- Each milestone is doable in 1-2 sittings, ends with something that runs, and has at most 3-4 new concepts, sized to their experience (for basic-C-only, strings, pointers and `malloc` are separate milestones). The first one is quick and winnable.
- **Concepts are shown up front** as `name | what it is in plain words`. Say what it IS, never how to combine concepts. OK: "fork | creates a copy of the running program". Not OK: "call fork, then exec in the child". Include classic beginner gotchas (output buffering, a failed system call).
- **Done when** names exact input and expected output, checkable alone. Never "works correctly".
- **Look up** is required: real man pages or docs.
- **First step**: one concrete ~10-minute action with real values, no unexplained jargon, exact commands (and what to report if a tool is missing), not a recall quiz on facts they can't know yet (point to a look-up), and it ends by asking for something back.
- No code or step-by-step solution anywhere. A concept appears before it's used.

Then ask: "Does this order make sense? Anything missing, too big, or confusing?" and revise. For a big plan, or if they ask for a second opinion, you can have the `teaching-harness:roadmap-reviewer` agent review the draft first.

## 3. Save
```
teach.py roadmap init "<goal in their words>"
teach.py roadmap add --title "..." --outcome "..." --done-when "..." \
    --concepts "stdin | where keyboard input arrives; getline | reads a whole line" \
    --look-up "man 3 getline; man 7 signal" --first-step "..."
```
`--concepts` and `--look-up` separate items with `;`, and a concept's name from its description with `|`. The tool rejects missing descriptions, code, or a first step that doesn't ask for something back.
Then run `teach.py roadmap lint`, fix any warning with `roadmap edit`, `teach.py roadmap start 1`, tell them `.teach/ROADMAP.md` is their readable copy, and begin with the first step.

## 4. Working a milestone
- Teach with the `teach` skill. `roadmap start N` resets the hint ladder.
- **Stay on track:** if they ask for something outside the current milestone, say so in one friendly sentence and ask: park it (`teach.py roadmap park "idea"`) or switch milestone?
- When they think they've met **done when**, have them demonstrate it, quiz the milestone's concepts (exact concept names), then `teach.py roadmap done N`. It needs at least one recorded concept pass; `--force` only if the learner insists.
- Celebrate in a line, show progress ("3 of 7"), offer the next milestone. They decide when to start it.

### Test out (for learners who already know it)
Offer ONCE per milestone, when they say they know it or clearly do: "Want to test out of this one? A short quiz plus showing me your work. Pass and we skip ahead; miss and we only cover the gaps." Never skip on their say-so alone.
1. `teach.py quiz start "M<N> test-out" --testout`: difficulty 3 or higher, one question per milestone concept, no hints, never recall (see the `quiz` skill).
2. Have them demonstrate the milestone's **done when** with their own code or explanation.
3. `teach.py roadmap skip N --demonstrated "<what they showed>"`. On NOT YET, ask the missing questions. If they missed concepts, teach only those gaps (passed concepts are already recorded), then close it with a normal `roadmap done`.
4. After two test-outs in a row, you may offer one combined quiz to skip several milestones; each skipped milestone still needs its own evidence. `--force` only if the learner insists.

## 5. Plan quality is YOUR job, never the learner's
Fix lint warnings, vague done-whens and oversized milestones yourself with `roadmap edit`. Never ask the learner to write milestone text or predict the output of a program they haven't learned to write. Ask them only about scope, pace and preferences, then say in one line what you changed.
To re-plan, use `roadmap edit N ...` or `roadmap remove N`, say why, and keep the rest intact.
