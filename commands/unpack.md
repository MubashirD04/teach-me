---
description: Load a subject pack (made with /teaching-harness:pack) into this project
argument-hint: <file> [--force]
allowed-tools: Bash(python3:*)
---
Run `python3 "${CLAUDE_PLUGIN_ROOT}/bin/teach.py" unpack $ARGUMENTS`. If it says a roadmap already exists, tell the learner and only re-run with `--force` if they confirm. Afterwards tell them where they left off (`teach.py roadmap status`).
