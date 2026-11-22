"""Roadmap: a persisted, beginner-friendly plan toward a project goal.

Stored in <project>/.teach/roadmap.json, with a human-readable copy in .teach/ROADMAP.md.
Design rules (enforced here, not just requested in a prompt):
  * every milestone has: title, outcome, done_when, concepts (shown from the start, each with a plain-words
    description), first_step, optional look_up
  * concepts are NAMED and DESCRIBED ("what it is"), never explained as a recipe ("how to combine them")
  * first_step must be an action or question, not code
  * a milestone can only be closed once the learner has passed a check on at least one of its concepts
"""
import argparse, math, re
from teachlib import *
from teachlib import _load, _save

ASK_BACK = re.compile(r"\?|\b(tell me|show me|describe|write down|report back|bring back|let me know)\b", re.I)
ICON = {"done": "[x]", "skipped": "[~]", "active": "[>]", "todo": "[ ]"}


# ---------------------------------------------------------------- storage / helpers
def load_roadmap():
    return _load(teach_dir() / "roadmap.json", None)


def save_roadmap(r):
    _save(teach_dir() / "roadmap.json", r)
    (teach_dir() / "ROADMAP.md").write_text(render_md(r))


def cname(c):  return c.split("|", 1)[0].strip()
def cdesc(c):  return c.split("|", 1)[1].strip() if "|" in c else ""
def active_milestone(r): return next((m for m in r["milestones"] if m["status"] == "active"), None)
def n_done(r): return sum(1 for m in r["milestones"] if m["status"] in ("done", "skipped"))
def n_skipped(r): return sum(1 for m in r["milestones"] if m["status"] == "skipped")
def _tested(r): return f" ({n_skipped(r)} tested out)" if n_skipped(r) else ""


def summary_line(r):
    m, total = active_milestone(r), len(r["milestones"])
    cur = f"current: {m['id']}. {m['title']}" if m else "no active milestone"
    return f"Roadmap '{r['goal']}': {n_done(r)}/{total} milestones done{_tested(r)}, {cur}."


def render_md(r):
    out = [f"# Roadmap: {r['goal']}", "", f"Progress: {n_done(r)}/{len(r['milestones'])} milestones done{_tested(r)}", ""]
    for m in r["milestones"]:
        out += [f"## {ICON[m['status']]} {m['id']}. {m['title']}", "",
                f"**Outcome:** {m['outcome']}", "", f"**Done when:** {m['done_when']}", "", "**Concepts you'll meet:**"]
        out += [f"- **{cname(c)}** - {cdesc(c)}" for c in m["concepts"]]
        if m.get("look_up"):
            out += ["", "**Look up:** " + ", ".join(f"`{x}`" for x in m["look_up"])]
        out += ["", f"> **First step:** {m['first_step']}", ""]
        if m["status"] == "skipped":
            t = m.get("tested_out", {})
            out += [f"*Tested out{' (forced)' if t.get('forced') else ''}: showed {t.get('demonstrated') or 'n/a'}.*", ""]
    if r.get("parked"):
        out += ["## Parked ideas (for later)", ""] + [f"- {p['idea']}" for p in r["parked"]] + [""]
    return "\n".join(out)


# ---------------------------------------------------------------- validation
class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def _parse_fields(args, required):
    ap = _Parser(prog="roadmap", add_help=False)
    for f in ("title", "outcome", "done-when", "concepts", "first-step", "look-up"):
        ap.add_argument("--" + f)
    ns = vars(ap.parse_args(args))
    ns = {k: v for k, v in ns.items() if v is not None}
    if required:
        missing = [f"--{k.replace('_', '-')}" for k in ("title", "outcome", "done_when", "concepts", "first_step") if k not in ns]
        if missing:
            raise ValueError("missing " + ", ".join(missing))
    return ns


def _check_text(name, text, min_len=10):
    if len(text.strip()) < min_len:
        raise ValueError(f"{name} is too short to be clear for a beginner (min {min_len} chars)")
    if "```" in text or re.search(r"\)\s*;", text):
        raise ValueError(f"{name} must be plain words, not code")


def _normalise(ns):
    out = {}
    for k, v in ns.items():
        key = k.replace("-", "_")
        if key == "concepts":
            cs = [c.strip() for c in v.split(";") if c.strip()]
            if not cs:
                raise ValueError("--concepts needs at least one 'name | plain-words description'")
            for c in cs:
                if "|" not in c or len(cdesc(c)) < 8 or not cname(c):
                    raise ValueError(f"concept '{c}' needs the form 'name | what it is in plain words' (>= 8 chars of description)")
                _check_text("concept description", cdesc(c), 8)
            out[key] = cs
        elif key == "look_up":
            out[key] = [x.strip() for x in v.split(";") if x.strip()]
        else:
            _check_text("--" + k, v, 8 if key == "title" else 15)
            if key == "first_step":
                if len(v.strip()) < 40:
                    raise ValueError("--first-step is too thin for a beginner: say exactly what to do, with concrete values (>= 40 chars)")
                if not ASK_BACK.search(v):
                    raise ValueError("--first-step must end by asking the learner to bring something back "
                                     "(a question with '?' or 'tell me / show me / describe / write down ...') so they know what finished looks like")
            out[key] = v.strip()
    return out



CONCRETE = re.compile(r"[`'\"/:]|\d|\./|\s-{1,2}\w")
RECALL = re.compile(r"\b(which|what)\s+(numbers?|flags?|arguments?|names?|header|function|options?|macros?)\b", re.I)
LOOKUP_PHRASE = re.compile(r"\b(look up|man |read |check the docs)", re.I)


def lint(r):
    """Quality warnings a beginner would hit. Returns a list of strings."""
    w = []
    for m in r["milestones"]:
        tag = f"M{m['id']} '{m['title']}'"
        if not CONCRETE.search(m["done_when"]) or len(m["done_when"]) < 30:
            w.append(f"{tag}: done-when has no concrete example - name exactly what they type and what they should see")
        if len(m["concepts"]) > 4:
            w.append(f"{tag}: {len(m['concepts'])} concepts is too many for one milestone - split it")
        if RECALL.search(m["first_step"]) and not LOOKUP_PHRASE.search(m["first_step"]):
            w.append(f"{tag}: first step looks like recalling a fact they haven't met - make it a look-up (name the man page) or a reasoning/prediction")
    return w


# ---------------------------------------------------------------- commands
def _start(r, n):
    for m in r["milestones"]:
        if m["status"] == "active":
            m["status"] = "todo"
    m = r["milestones"][n - 1]
    m["status"] = "active"; m["started"] = now()
    s = load_state(); s.update(task=f"M{n}: {m['title']}", hint_level=0, attempts=0); save_state(s)
    save_roadmap(r)
    return m


def _status(r):
    print(f"GOAL: {r['goal']}")
    print(f"PROGRESS: {n_done(r)}/{len(r['milestones'])} done{_tested(r)}")
    for m in r["milestones"]:
        print(f" {ICON[m['status']]} {m['id']}. {m['title']}")
    m = active_milestone(r)
    if m:
        print(f"\nCURRENT MILESTONE {m['id']}: {m['title']}")
        print(f"  outcome:    {m['outcome']}")
        print(f"  done when:  {m['done_when']}")
        print(f"  first step: {m['first_step']}")
        print("  concepts:   " + "; ".join(f"{cname(c)} ({cdesc(c)})" for c in m["concepts"]))
        if m.get("look_up"):
            print("  look up:    " + ", ".join(m["look_up"]))
    else:
        nxt = next((x for x in r["milestones"] if x["status"] == "todo"), None)
        print("\nNO ACTIVE MILESTONE." + (f" Next up: {nxt['id']}. {nxt['title']} (run `roadmap start {nxt['id']}`)." if nxt else " All done!"))
    if r.get("parked"):
        print(f"\nPARKED IDEAS ({len(r['parked'])}): " + "; ".join(p["idea"] for p in r["parked"]))


def cmd_roadmap(a):
    sub, rest = (a[0], a[1:]) if a else ("status", [])
    r = load_roadmap()
    try:
        if sub == "init":
            goal = " ".join(x for x in rest if x != "--force").strip()
            if not goal:
                print('usage: roadmap init "goal" [--force]'); return 1
            if r and "--force" not in rest:
                print("a roadmap already exists (use --force to replace it)"); return 1
            r = {"goal": goal, "milestones": [], "parked": [], "created": now()}
            save_roadmap(r)
            p = load_learner()
            if goal not in p["goals"]:
                p["goals"].append(goal)
            p["onboarded"] = True   # planning a goal covers what onboarding is for
            save_learner(p)
            print(f"roadmap created for: {goal}. Add milestones with `roadmap add --title ... --outcome ... --done-when ... --concepts 'name | plain words; ...' --first-step ...`")
            return
        if sub == "render":
            if r: save_roadmap(r); print(".teach/ROADMAP.md updated"); return
        if not r:
            print("no roadmap yet. Use the `roadmap` skill to plan one (`roadmap init \"goal\"` then `roadmap add ...`)."); return 1
        if sub == "status":
            _status(r)
        elif sub == "add":
            ns = _normalise(_parse_fields(rest, required=True))
            if not ns.get("look_up"):
                raise ValueError("--look-up needs at least one real reference (e.g. 'man 3 fgets; K&R 7.6') so the learner can find things themselves")
            ns.update(id=len(r["milestones"]) + 1, status="todo")
            r["milestones"].append(ns); save_roadmap(r)
            print(f"added milestone {ns['id']}: {ns['title']}")
        elif sub in ("edit", "remove", "start", "done", "skip"):
            if not rest or not rest[0].isdigit() or not (1 <= int(rest[0]) <= len(r["milestones"])):
                print(f"usage: roadmap {sub} N (1-{len(r['milestones'])})"); return 1
            n, rest = int(rest[0]), rest[1:]
            if sub == "edit":
                ns = _normalise(_parse_fields(rest, required=False))
                r["milestones"][n - 1].update(ns); save_roadmap(r); print(f"edited milestone {n}")
            elif sub == "remove":
                r["milestones"].pop(n - 1)
                for i, m in enumerate(r["milestones"], 1): m["id"] = i
                save_roadmap(r); print(f"removed milestone {n}; renumbered")
            elif sub == "start":
                m = _start(r, n); print(f"milestone {n} active: {m['title']}. Hint ladder reset. First step: {m['first_step']}")
            elif sub == "skip":
                m = r["milestones"][n - 1]
                if m["status"] in ("done", "skipped"):
                    print(f"milestone {n} is already {m['status']}"); return 1
                ap = _Parser(prog="roadmap skip", add_help=False)
                ap.add_argument("--demonstrated", default=""); ap.add_argument("--force", action="store_true")
                a2 = ap.parse_args(rest)
                st = load_state()
                results = list((st.get("quiz") or {}).get("results", [])) + [x for h in st["quiz_history"] for x in h["results"]]
                names = [cname(c) for c in m["concepts"]]
                ok = {nm for nm in names if any(x["concept"] == nm and x["result"] == "pass" and x["difficulty"] >= 3 for x in results)}
                gaps = [nm for nm in names if nm not in ok]
                demo = a2.demonstrated.strip()
                if (gaps or not demo) and not a2.force:
                    msg = []
                    if gaps:
                        msg.append(f"no first-attempt pass at difficulty >= 3 yet for: {', '.join(gaps)} "
                                   f"(passed: {', '.join(sorted(ok)) or 'none'}). Run `quiz start \"M{n} test-out\" --testout` and ask one question per gap concept, no hints.")
                    if not demo:
                        msg.append("--demonstrated \"<what the learner showed>\" is required: have them run or explain their own work against the milestone's done-when.")
                    print("NOT YET: " + " ".join(msg) + " (--force only if the learner insists.)"); return 1
                m["status"] = "skipped"
                m["tested_out"] = {"at": now(), "passed": sorted(ok), "demonstrated": demo, "forced": bool(gaps or not demo)}
                save_roadmap(r)
                nxt = next((x for x in r["milestones"] if x["status"] == "todo"), None)
                print(f"milestone {n} tested out ({n_done(r)}/{len(r['milestones'])} done)." +
                      (f" Next: {nxt['id']}. {nxt['title']} - `roadmap start {nxt['id']}` when the learner is ready." if nxt else " The roadmap is complete!"))
            else:  # done
                m, p = r["milestones"][n - 1], load_learner()
                if m["status"] in ("done", "skipped"):
                    print(f"milestone {n} is already {m['status']}"); return 1
                passed = [cname(c) for c in m["concepts"] if p["concepts"].get(cname(c), {}).get("pass", 0) >= 1]
                need = 1
                if len(passed) < need and "--force" not in rest:
                    todo = [cname(c) for c in m["concepts"] if cname(c) not in passed]
                    print(f"NOT YET: no concept of this milestone has a recorded pass. "
                          f"Quiz or check the learner on: {', '.join(todo)}. (--force only if the learner insists.)")
                    return 1
                m["status"] = "done"; m["done_at"] = now(); m["forced"] = len(passed) < need
                save_roadmap(r)
                nxt = next((x for x in r["milestones"] if x["status"] == "todo"), None)
                print(f"milestone {n} done ({n_done(r)}/{len(r['milestones'])})." +
                      (f" Next: {nxt['id']}. {nxt['title']} - `roadmap start {nxt['id']}` when the learner is ready." if nxt else " The roadmap is complete!"))
        elif sub == "lint":
            w = lint(r)
            print("\n".join(f"WARN {x}" for x in w) if w else "lint: no warnings")
            if w: print(f"{len(w)} warning(s). Fix each with `roadmap edit N ...` (or split the milestone), then lint again.")
        elif sub == "park":
            idea = " ".join(rest).strip()
            if not idea:
                print('usage: roadmap park "idea"'); return 1
            r["parked"].append({"idea": idea, "at": now()}); save_roadmap(r); print("parked for later")
        elif sub == "parked":
            print("\n".join(f"- {p['idea']}" for p in r["parked"]) or "(nothing parked)")
        else:
            print("usage: roadmap init|add|edit|remove|status|start|done|skip|park|parked|lint|render"); return 1
    except ValueError as e:
        print(f"ERROR: {e}"); return 1
