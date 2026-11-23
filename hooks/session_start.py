#!/usr/bin/env python3
"""Injects teaching context (mode, learner profile) at session start."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))
from teachlib import load_state, load_learner, is_active, log_event
from roadmap import load_roadmap, summary_line

if not is_active():
    sys.exit(0)          # project hasn't opted in: stay silent
s, p = load_state(), load_learner()
if s['mode'] == 'off':
    sys.exit(0)
weak = sorted(p["concepts"].items(), key=lambda kv: kv[1]["fail"] - kv[1]["pass"], reverse=True)[:5]
lines = [
    "TEACHING HARNESS is active. You are a software-development teacher for a learner, not a code generator.",
    f"Mode: {s['mode']} (learn = you may not write their code; pair = they write key parts; review = you write, they must explain it back; off = normal).",
    f"Learner level: {p['level']}. Goals: {', '.join(p['goals']) or 'not set yet'}.",
]
if weak:
    lines.append("Shakiest concepts: " + ", ".join(k for k, _ in weak))
if s["task"]:
    lines.append(f"Current task: {s['task']} (hint level {s['hint_level']}/5).")
rm = load_roadmap()
if rm:
    lines.append(summary_line(rm) + " Read it with `teach.py roadmap status`; the learner can read .teach/ROADMAP.md.")
if not rm:
    lines.append("NO ROADMAP YET. If the learner's message states a multi-step project goal (e.g. 'I want to build a shell'), "
                 "start the `roadmap` skill immediately: ask its first scoping question. Do NOT give a general map first and do NOT ask whether they want a plan.")
lines.append("Load the `teach` skill and follow it." + ("" if p["onboarded"] else
             " The learner is NOT onboarded yet: unless they state a project goal (then use `roadmap`), begin with the `onboard` skill."))
if not os.environ.get("TEACH_NO_REFRESH"):
    try:
        from export import build_dashboard; build_dashboard()
    except Exception:
        pass
log_event("session_start", mode=s["mode"], onboarded=p["onboarded"], roadmap=bool(rm))
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                          "additionalContext": "\n".join(lines)}}))
