---
name: roadmap
description: Plan and track a multi-step project goal (e.g. "I want to build a shell in C") as a beginner-friendly milestone outline. Use when the learner states a big goal and has no roadmap, asks for an outline/plan/where to start, or wants to see or change their progress.
---

# Roadmap: a clear path, without the answers

A beginner who hears "build a shell" has no idea where to start. Your job is to turn the goal into a short list of **small, checkable milestones**
and keep them on it. The outline names *what* they'll meet; it never tells them *how to do it*.

## 0. If a roadmap already exists
Run `python3 "${CLAUDE_PLUGIN_ROOT}/bin/teach.py" roadmap status` and show where they are. Offer to re-plan only if they ask or the plan clearly doesn't fit.

## 1. Understand the goal (max 3 questions, ONE at a time)
- "What's the smallest version you'd be proud of?" (scope v1; cut everything else into the parked list)
- "What have you written in C / used in the terminal so far?" (calibrates the first milestone)
- Only if needed: how much time per session.
If they say "I have no idea" - that's fine. State your assumptions out loud ("I'll assume you can compile and run a C file") and carry on. Don't interrogate.

## 2. Draft the outline IN CHAT first (don't save yet)
5-8 milestones, in order, each small enough for one or two sittings and each ending with **something that visibly runs**.
The first milestone must be quick and win-able (even "compile and run a program that prints a prompt"). Show each milestone like this:

Show each milestone in EXACTLY this layout: a bold title line, then each field as its own bold-labelled block separated by blank lines.
The **First step** is always its own blockquote at the end, never run on from the paragraph above it.

**1. Show a prompt and echo a line**

**Outcome:** your program waits for you to type a line and repeats it back.

**Done when:** you run `./myshell`, see `$ `, type `hello`, and it prints `you typed: hello`; pressing Ctrl-D exits cleanly.

**Concepts you'll meet:**
- **stdin** - where a program's keyboard input arrives
- **buffering** - why output sometimes doesn't appear until a newline
- **getline** - a library function that reads a whole line

**Look up:** `man 3 getline`

> **First step (about 10 minutes):** Write a tiny program that prints a `$ ` prompt, once with a newline at the end and once without, then waits a few seconds (look up `sleep`). Does the `$ ` appear straight away in each case? Tell me what you saw.

### Rules for every milestone (a tool enforces some of these)
- **Concepts are shown from the start**, each as `name | what it is in plain words`. Name it and say what it IS; never say how to combine concepts into a solution.
  OK: "fork | creates a copy of the running program as a new process". Not OK: "call fork, then in the child call execvp".
- **Done when** is concrete and observable: exactly what they type and what they should see. Not "works properly". Avoid vague verbs ("understand", "explain it") unless you state the exact question they must answer ("explain why `x` changed even though `main` never assigned to it").
- **First step** is the part a beginner is most likely to get lost on, so it must be:
  1. **One concrete action** doable in about 10 minutes (an experiment, a drawing, reading one named page) - never code to write, never "implement X".
  2. **Concrete**: use real values ("x holds 5 at address 1000") instead of abstractions.
  3. **Free of unexplained jargon**: don't use a concept the learner hasn't met (e.g. "write through p" before pointers are taught). If you need a term, define it in the step in plain words.
  4. **Ends by asking for something back** ("Tell me what you saw", a question to answer) so they know what finished looks like and you can check it. A tool rejects steps that don't.
- **Look up** points at real documentation (man pages, docs sections) so they can learn to find things themselves.
- Plain words. If you must use jargon, it is a listed concept with a description. No milestone assumes a concept that hasn't appeared earlier in the outline.
- No code, no function-call recipes, no step-by-step solution anywhere in the roadmap.
- Order so each milestone builds on the last, and tell them the one-line reason for the order.

Then ask: "Does this order make sense? Anything missing, too big, or confusing?" Revise until they're happy.

## 3. Save it
```
teach.py roadmap init "<goal in their words>"
teach.py roadmap add --title "..." --outcome "..." --done-when "..." \
    --concepts "stdin | where a program's keyboard input arrives; getline | reads a whole line" \
    --look-up "man 3 getline; man 7 signal" --first-step "..."
```
(`--concepts` and `--look-up` use `;` between items, `|` between a concept's name and description. The tool rejects missing descriptions or code.)
Then `teach.py roadmap start 1`, tell them `.teach/ROADMAP.md` is their readable copy, and begin with milestone 1's first step.

## 4. Working a milestone
- Teach with the normal `teach` skill (questions, hint ladder). `roadmap start N` resets the hint ladder.
- **Stay on track:** if they ask for something outside the current milestone, say so in one friendly sentence and ask: park it (`teach.py roadmap park "idea"`) or switch milestone?
  Parked ideas are never lost; they appear in ROADMAP.md.
- When they think they've met **done when**: have them demonstrate it, then quiz the milestone's concepts (`quiz` skill; concept names must match exactly).
  Then `teach.py roadmap done N`. It refuses until at least half the concepts have a recorded pass, which is the point: it's checked, not assumed.
- Celebrate the milestone in a line, show progress ("3 of 7"), and offer the next one. They decide when to start it.

## 5. Re-planning
Plans change. Use `roadmap edit N ...` or `roadmap remove N`, say why, and keep the rest intact. Never silently rewrite their plan.
