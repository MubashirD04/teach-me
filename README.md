# Teaching Harness

A Claude Code plugin that makes the agent behave like a software-development teacher, and *enforces* it.

## What's in v0.1
| Piece | Where | What it does |
|---|---|---|
| Learn-mode guard | `hooks/guard.py` | In `learn` mode, blocks Write/Edit and file-modifying Bash. Only `.teach/` is writable. |
| Hint ladder | `bin/teach.py hint` | 5 rungs (question -> nudge -> principle -> scaffold -> solution); levels 4-5 need recorded attempts. |
| Learner profile | `~/.teach/learner.json` | Goals, level, per-concept pass/fail/hints, persists across projects. |
| Session context | `hooks/session_start.py` | Injects mode + profile so every session starts as a teacher. |
| Skills | `skills/teach`, `onboard`, `check-understanding` | Pedagogy, broad-start onboarding, verification. |
| Diagrams | `skills/diagram`, `/teaching-harness:diagram` | Builds a self-contained HTML visual aid (step-through template) in `.teach/diagrams/`. |
| Quiz | `skills/quiz`, `/teaching-harness:quiz`, `teach.py quiz` | One question at a time, weak/stale concepts first, adaptive difficulty, results recorded to the profile. |
| Roadmap | `skills/roadmap`, `/teaching-harness:roadmap`, `teach.py roadmap` | Beginner-friendly milestone plan for a project goal: outcomes, 'done when', concepts shown from the start, first step; persisted in `.teach/ROADMAP.md`; keeps you on the current milestone and parks tangents. |
| Reviewer agent | `agents/roadmap-reviewer.md` | Read-only subagent (Read/Grep/Glob) that reviews a draft roadmap against a rubric before the learner sees it. Addressed as `teaching-harness:roadmap-reviewer`. |
| Commands | `/teaching-harness:mode`, `:hint`, `:progress`, `:diagram`, `:quiz`, `:roadmap` | Switch modes, ask for a hint, see progress. |

Modes: `learn` (agent can't write your code), `pair` (you write key parts), `review` (agent writes, you explain it back), `off`.

## Try it
```
claude --plugin-dir "<path to this folder>"
```
Then just say what you want to learn. Run `bash tests/test_harness.sh` to check the guard and ladder.

## Known limits
- The Bash guard is heuristic, not a sandbox (e.g. `python -c "open(...).write()"` isn't caught). For hard guarantees, run in a container or use permission deny rules.
- Concept names are free text; no concept graph yet.

## Next
1. Spaced review: resurface old concepts as short exercises from your own past code.
2. Curriculum: pick the next task from weak concepts, using failing tests as exercises.
3. Eval personas that try to extract answers, to measure guard + ladder robustness.
4. Multi-learner profiles (`TEACH_HOME` already supports separate stores).
