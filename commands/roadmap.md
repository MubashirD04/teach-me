---
description: Plan or view your project roadmap (e.g. "build a shell in C")
argument-hint: [goal | status]
allowed-tools: Bash(python3:*), Read, Write, AskUserQuestion
---
Input: $ARGUMENTS
- Empty or "status": run `teach.py roadmap status` and show progress. If no roadmap exists, ask what they want to build (one question).
- Otherwise treat the input as their goal and follow the `roadmap` skill: ask at most 3 scoping questions, ONE per message, as multiple choice (AskUserQuestion, options labelled in words not letters), draft the outline in chat, save it once they approve.
