#!/usr/bin/env python3
"""PostToolUse(Bash): rebuild .teach/dashboard.html after a teach.py command. Silent; active projects only."""
import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin"))
try:
    ev = json.load(sys.stdin)
    cmd = (ev.get("tool_input") or {}).get("command", "")
    from teachlib import is_active
    if "teach.py" in cmd and is_active() and not os.environ.get("TEACH_NO_REFRESH"):
        from export import build_dashboard
        build_dashboard()
except Exception:
    pass
