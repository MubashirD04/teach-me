#!/usr/bin/env python3
"""Teaching Harness CLI. Used by slash commands, skills, and by you directly.

  teach.py status
  teach.py mode [status]|learn|pair|review|off
  teach.py task "what the learner is working on"
  teach.py attempt                 # record that the learner tried something
  teach.py hint [--force]          # escalate one rung of the ladder (gated by attempts)
  teach.py hint --reset
  teach.py concept NAME pass|fail  # record evidence for a concept
  teach.py goal "text"             # add a learning goal
  teach.py set level|onboarded VALUE
  teach.py profile                 # print the learner profile
  teach.py quiz pick [N]           # rank concepts worth quizzing (weak / stale first)
  teach.py quiz start TOPIC [--mc|--testout] # begin a quiz (--mc = multiple choice; --testout = harder, for skipping a milestone)
  teach.py quiz answer pass|fail|partial [CONCEPT]   # record the FIRST attempt at a question
  teach.py quiz status | end
  teach.py roadmap init "goal" | add ... | edit N ... | remove N | status | start N | done N | skip N --demonstrated "..." | lint | park "idea" | parked
  teach.py diagram "title"          # safe path for an HTML visual aid under .teach/diagrams/
"""
import sys, json
sys.path.insert(0, __import__("os").path.dirname(__file__))
from teachlib import *
from roadmap import cmd_roadmap, load_roadmap, active_milestone, cname


def cmd_status(_):
    s, p = load_state(), load_learner()
    print(f"mode: {s['mode']}")
    print(f"profile file: {home_dir() / 'learner.json'}  (onboarded: {p['onboarded']})")
    print(f"task: {s['task'] or '(none)'}")
    print(f"hint level: {s['hint_level']}/5   attempts this task: {s['attempts']}")
    print(f"goals: {', '.join(p['goals']) or '(none yet)'}")
    weak = sorted(p["concepts"].items(), key=lambda kv: kv[1]["fail"] - kv[1]["pass"], reverse=True)[:5]
    if weak:
        print("shakiest concepts: " + ", ".join(f"{k} (+{v['pass']}/-{v['fail']})" for k, v in weak))


def cmd_mode(a):
    if not a or a[0] == "status":
        return cmd_status(a)
    if a[0] not in MODES:
        print(f"usage: mode {'|'.join(MODES)}"); return 1
    s = load_state(); s["mode"] = a[0]; save_state(s)
    print(f"mode set to {a[0]}")


def cmd_task(a):
    s = load_state()
    s.update(task=" ".join(a) or None, hint_level=0, attempts=0); save_state(s)
    print(f"task: {s['task']} (hint ladder reset)")


def cmd_attempt(_):
    s = load_state(); s["attempts"] += 1; save_state(s)
    print(f"attempts: {s['attempts']}")


def cmd_hint(a):
    s = load_state()
    if "--reset" in a:
        s["hint_level"] = 0; s["attempts"] = 0; save_state(s); print("hint ladder reset"); return
    nxt = min(s["hint_level"] + 1, 5)
    need = MIN_ATTEMPTS_FOR_LEVEL.get(nxt, 0)
    if s["attempts"] < need and "--force" not in a:
        print(f"HOLD at level {s['hint_level'] or 1}: level {nxt} needs {need} recorded attempts "
              f"(have {s['attempts']}). Ask the learner to try again, then run `attempt`. "
              f"Use --force only if the learner explicitly demands it.")
        return
    s["hint_level"] = nxt
    if nxt == 5:
        s["solutions_shown"].append({"task": s["task"], "at": now()})
    save_state(s)
    print(f"LEVEL {nxt}: {LADDER[nxt]}")
    # hints are evidence about the learner
    if s["task"]:
        p = load_learner()
        c = p["concepts"].setdefault(s["task"], {"pass": 0, "fail": 0, "last_seen": None, "hints_needed": 0})
        c["hints_needed"] = max(c["hints_needed"], nxt); c["last_seen"] = now(); save_learner(p)


def cmd_concept(a):
    if len(a) < 2 or a[-1] not in ("pass", "fail"):
        print("usage: concept NAME pass|fail"); return 1
    name, res = " ".join(a[:-1]), a[-1]
    p = load_learner()
    c = p["concepts"].setdefault(name, {"pass": 0, "fail": 0, "last_seen": None, "hints_needed": 0})
    c[res] += 1; c["last_seen"] = now(); save_learner(p)
    print(f"{name}: +{c['pass']}/-{c['fail']}")


def cmd_goal(a):
    p = load_learner(); p["goals"].append(" ".join(a)); save_learner(p); print("goal added")


def cmd_set(a):
    if len(a) < 2 or a[0] not in ("level", "onboarded"):
        print("usage: set level|onboarded VALUE"); return 1
    p = load_learner(); p[a[0]] = (a[1] == "true") if a[0] == "onboarded" else " ".join(a[1:]); save_learner(p)
    print(f"{a[0]} = {p[a[0]]}")


def cmd_diagram(a):
    import re
    title = " ".join(a).strip()
    if not title:
        print("usage: diagram \"title\""); return 1
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60] or "diagram"
    d = teach_dir() / "diagrams"; d.mkdir(parents=True, exist_ok=True)
    path, n = d / f"{slug}.html", 2
    while path.exists():
        path = d / f"{slug}-{n}.html"; n += 1
    rel = path.relative_to(project_dir())
    s = load_state(); s.setdefault("diagrams", []).append({"title": title, "path": str(rel), "at": now()}); save_state(s)
    print(rel)


DIFFICULTY = {
    1: "RECALL - name the term / say what X does",
    2: "READ & PREDICT - trace a small snippet (<=12 lines) and say what it prints/returns",
    3: "SPOT THE BUG / FILL THE BLANK - one realistic mistake or missing piece",
    4: "MODIFY or COMPARE - change code for a new requirement, or weigh two approaches",
    5: "UNFAMILIAR TERRITORY - debug or design something new, reasoning aloud",
}
START_LEVEL = {"beginner": 1, "junior": 2, "junior+": 3, "intermediate": 3, "senior": 4}


def _concept(p, name):
    return p["concepts"].setdefault(name, {"pass": 0, "fail": 0, "last_seen": None, "hints_needed": 0})


def _priority(c):
    return (c["fail"] - c["pass"]) * 2 + c["hints_needed"] + min(days_since(c.get("last_seen")), 30) / 10


def cmd_quiz(a):
    sub, rest = (a[0], a[1:]) if a else ("status", [])
    s, p = load_state(), load_learner()
    q = s.get("quiz")
    if sub == "pick":
        n = int(rest[0]) if rest and rest[0].isdigit() else 5
        ranked = sorted(p["concepts"].items(), key=lambda kv: _priority(kv[1]), reverse=True)[:n]
        rm = load_roadmap(); am = active_milestone(rm) if rm else None
        if am:
            print(f"CURRENT MILESTONE {am['id']} ({am['title']}) - quiz these first:")
            for c in am["concepts"]:
                k = p["concepts"].get(cname(c), {"pass": 0, "fail": 0})
                print(f"  {cname(c)}  (+{k['pass']}/-{k['fail']})")
            if ranked: print("other weak/stale concepts:")
        if not ranked and not am:
            print("NO HISTORY: ask the learner what they want to be quizzed on. "
                  f"Goals: {', '.join(p['goals']) or '(none)'}. Current task: {s['task'] or '(none)'}.")
            return
        for name, c in ranked:
            print(f"{'  ' if am else ''}{name}  (+{c['pass']}/-{c['fail']}, hints {c['hints_needed']}, last seen {days_since(c['last_seen']):.0f}d ago)")
    elif sub == "start":
        mc, testout = "--mc" in rest, "--testout" in rest
        topic = " ".join(x for x in rest if x not in ("--mc", "--testout")).strip()
        if not topic:
            print("usage: quiz start TOPIC [--mc]"); return 1
        lvl = START_LEVEL.get(p["level"], 2)
        c = p["concepts"].get(topic)
        if c and c["fail"] > c["pass"]:
            lvl = max(1, lvl - 1)
        if testout:
            lvl = max(3, lvl)
        s["quiz"] = {"topic": topic, "format": "multiple-choice" if mc else "open-ended", "difficulty": lvl,
                     "floor": 3 if testout else 1, "testout": testout,
                     "asked": 0, "streak": 0, "results": [], "started": now()}
        save_state(s)
        print(f"quiz started: {topic} [{s['quiz']['format']}] difficulty {lvl}: {DIFFICULTY[lvl]}"
              + (" | TEST-OUT: difficulty never drops below 3, one question per milestone concept, no hints, no recall questions" if testout else ""))
    elif sub == "answer":
        if not q:
            print("no active quiz; run `quiz start TOPIC` first"); return 1
        if not rest or rest[0] not in ("pass", "fail", "partial"):
            print("usage: quiz answer pass|fail|partial [CONCEPT]"); return 1
        res, concept = rest[0], (" ".join(rest[1:]) or q["topic"])
        q["asked"] += 1
        if res in ("pass", "fail"):
            c = _concept(p, concept); c[res] += 1; c["last_seen"] = now(); save_learner(p)
        q["results"].append({"concept": concept, "result": res, "difficulty": q["difficulty"]})
        if res == "pass":
            q["streak"] += 1
            if q["streak"] >= 2 and q["difficulty"] < 5:
                q["difficulty"] += 1; q["streak"] = 0
        else:
            q["streak"] = 0
            if res == "fail" and q["difficulty"] > q.get("floor", 1):
                q["difficulty"] -= 1
        save_state(s)
        d = q["difficulty"]
        print(f"recorded {res} for '{concept}' (question {q['asked']}). Next question difficulty {d}: {DIFFICULTY[d]}")
    elif sub == "status":
        if not q:
            print("no active quiz"); return
        print(f"quiz: {q['topic']} [{q['format']}] asked {q['asked']}, difficulty {q['difficulty']}: {DIFFICULTY[q['difficulty']]}")
    elif sub == "end":
        if not q:
            print("no active quiz"); return
        r = q["results"]
        n = lambda k: sum(1 for x in r if x["result"] == k)
        print(f"quiz on '{q['topic']}': {len(r)} asked - {n('pass')} pass, {n('partial')} partial, {n('fail')} fail")
        weak = sorted({x["concept"] for x in r if x["result"] != "pass"})
        solid = sorted({x["concept"] for x in r if x["result"] == "pass"} - set(weak))
        if solid: print("solid: " + ", ".join(solid))
        if weak: print("revisit: " + ", ".join(weak))
        s["quiz_history"].append({"topic": q["topic"], "at": now(), "results": r}); s["quiz"] = None; save_state(s)
    else:
        print("usage: quiz pick|start|answer|status|end"); return 1


def cmd_profile(_):
    print(json.dumps(load_learner(), indent=2))


CMDS = {"status": cmd_status, "mode": cmd_mode, "task": cmd_task, "attempt": cmd_attempt,
        "hint": cmd_hint, "concept": cmd_concept, "goal": cmd_goal, "set": cmd_set, "profile": cmd_profile, "diagram": cmd_diagram, "quiz": cmd_quiz, "roadmap": cmd_roadmap}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        print(__doc__); sys.exit(1)
    sys.exit(CMDS[sys.argv[1]](sys.argv[2:]) or 0)
