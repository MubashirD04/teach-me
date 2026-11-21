---
description: Switch teaching mode (learn | pair | review | off) or show status
argument-hint: learn | pair | review | off
allowed-tools: Bash(python3:*)
---
Run `python3 "${CLAUDE_PLUGIN_ROOT}/bin/teach.py" mode $ARGUMENTS` (if no argument was given, run it with `status` instead of `mode`).
Report the result in one line and explain what the new mode means for how you'll behave.
