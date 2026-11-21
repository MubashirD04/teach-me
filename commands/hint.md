---
description: Ask the teacher for the next rung of the hint ladder
allowed-tools: Bash(python3:*)
---
The learner asked for a hint. Run `python3 "${CLAUDE_PLUGIN_ROOT}/bin/teach.py" hint`.
If it says HOLD, do not escalate: ask the learner what they have tried, and have them attempt again.
Otherwise, give help at exactly the level the tool reports and no higher.
