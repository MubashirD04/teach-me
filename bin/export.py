"""Read-only snapshot of harness state (schema 1) + dashboard builder. Never modifies learner state."""
import json, os, subprocess, sys
from pathlib import Path
from teachlib import *
from roadmap import load_roadmap

SCHEMA = 1
ROOT = Path(__file__).resolve().parent.parent


def _hook_text(script, stdin="{}"):
    env = dict(os.environ, TEACH_NO_LOG="1", TEACH_NO_REFRESH="1", CLAUDE_PROJECT_DIR=str(project_dir()))
    try:
        out = subprocess.run([sys.executable, str(ROOT / "hooks" / script)], input=stdin, capture_output=True,
                             text=True, env=env, timeout=10).stdout.strip()
        return json.loads(out)["hookSpecificOutput"].get("additionalContext", "") if out else ""
    except Exception:
        return ""


GUARD_SAMPLES = [
    ("Write", {"file_path": "app.c"}), ("Edit", {"file_path": "src/main.c"}),
    ("Write", {"file_path": ".teach/scratch/demo.c"}), ("Write", {"file_path": ".teach/../app.c"}),
    ("Bash", {"command": "echo hi > app.c"}), ("Bash", {"command": "sed -i s/a/b/ app.c"}),
    ("Bash", {"command": "gcc app.c -o app"}), ("Bash", {"command": "./app > /dev/null"}),
    ("Bash", {"command": "make 2>&1 | tail -5"}), ("Bash", {"command": "ls -la"}),
    ("Bash", {"command": "python3 bin/teach.py hint"}), ("Bash", {"command": "git commit -am x"}),
]


def guard_table():
    sys.path.insert(0, str(ROOT / "hooks"))
    import guard
    rows = []
    for tool, inp in GUARD_SAMPLES:
        r = guard.decide(tool, inp)
        rows.append({"tool": tool, "input": inp.get("file_path") or inp.get("command"), "allowed": r is None})
    return rows


def build_export():
    s, p, rm = load_state(), load_learner(), load_roadmap()
    concepts = []
    for name, c in p["concepts"].items():
        concepts.append({"name": name, **c, "days_since": days_since(c.get("last_seen")), "priority": round(concept_priority(c), 2)})
    concepts.sort(key=lambda c: -c["priority"])
    events = []
    ev = teach_dir(False) / "events.jsonl"
    if ev.exists():
        for line in ev.read_text().splitlines()[-200:]:
            try: events.append(json.loads(line))
            except Exception: pass
    try: hooks = [{"event": k, "matcher": v[0].get("matcher", "")} for k, v in json.loads((ROOT / "hooks" / "hooks.json").read_text())["hooks"].items()]
    except Exception: hooks = []
    return {
        "schema": SCHEMA, "generated": now(), "project": project_dir().name, "active": is_active(),
        "state": {k: s[k] for k in ("mode", "task", "hint_level", "attempts", "solutions_shown")},
        "diagrams": s.get("diagrams", []),
        "quiz": {"active": s["quiz"], "history": s["quiz_history"][-50:]},
        "roadmap": rm, "profile": {"goals": p["goals"], "level": p["level"], "onboarded": p["onboarded"]},
        "concepts": concepts, "events": events,
        "harness": {"session_start_text": _hook_text("session_start.py"), "prompt_reminder_text": _hook_text("prompt_reminder.py", '{"prompt":"x"}'),
                    "guard_samples": guard_table(), "hooks": hooks, "profile_path": str(home_dir() / "learner.json"),
                    "plugin_root": str(ROOT)},
    }


def build_dashboard():
    """Write .teach/dashboard.html (self-contained). Returns path. Only for active projects."""
    if not is_active():
        return None
    data = json.dumps(build_export()).replace("<", "\\u003c").replace("\u2028", "\\u2028")
    html = (ROOT / "bin" / "dashboard_template.html").read_text().replace("/*DATA*/null", data, 1)
    out = teach_dir() / "dashboard.html"
    out.write_text(html)
    return out


def cmd_export(a):
    print(json.dumps(build_export(), indent=2))


def cmd_dashboard(a):
    out = build_dashboard()
    if not out:
        print("Harness not active in this project; run `mode learn` first."); return 1
    print(out)
    if "--open" in a:
        import webbrowser; webbrowser.open(out.as_uri())
