---
description: Switch teaching mode (learn | pair | review | off) or show status
argument-hint: learn | pair | review | off
allowed-tools: Bash(python3:*)
---
Run `python3 "${CLAUDE_PLUGIN_ROOT}/bin/teach.py" mode $ARGUMENTS`. With no argument, or with `status`, it shows the current mode, task, hint level, goals and the profile file path; with `learn`, `pair`, `review` or `off` it switches mode.
Report the result in one line and explain what the new mode means for how you'll behave.
