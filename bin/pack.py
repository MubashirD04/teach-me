"""Portable 'subject pack': move what you're learning to another device.

  teach.py pack [FILE]            write roadmap + progress + relevant concepts + diagrams to one JSON file
  teach.py unpack FILE [--force]  load a pack into THIS project (activates the harness here)

Contents: roadmap, task/hint state, quiz history, diagrams, your concept evidence for this subject,
goals and level. NOT included: events log, scratch files, other subjects' concepts.
"""
import json, re, sys, time
from pathlib import Path
from teachlib import *
from roadmap import load_roadmap, save_roadmap, cname

FORMAT, VERSION = "teaching-harness-pack", 1
MAX_DIAGRAM = 500_000


def _slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:40] or "subject"


def build_pack():
    rm = load_roadmap()
    if not rm:
        return None
    s, p = load_state(), load_learner()
    names = {cname(c).lower() for m in rm["milestones"] for c in m["concepts"]}
    concepts = {k: v for k, v in p["concepts"].items() if k.lower() in names}
    diagrams = []
    for d in s.get("diagrams", []):
        f = project_dir() / d["path"]
        try:
            if f.is_file() and f.stat().st_size <= MAX_DIAGRAM:
                diagrams.append({"title": d["title"], "file": f.name, "at": d.get("at"), "html": f.read_text()})
        except Exception:
            pass
    return {"format": FORMAT, "version": VERSION, "packed": now(), "subject": rm["goal"],
            "roadmap": rm,
            "state": {k: s[k] for k in ("task", "hint_level", "attempts", "quiz_history")},
            "diagrams": diagrams, "concepts": concepts,
            "learner": {"goals": p["goals"], "level": p["level"]}}


def cmd_pack(a):
    pk = build_pack()
    if not pk:
        print("No roadmap in this project, so there is no subject to pack. Plan one with /teaching-harness:roadmap."); return 1
    out = Path(a[0]) if a else project_dir() / f"teach-{_slug(pk['subject'])}.pack.json"
    out.write_text(json.dumps(pk, indent=2))
    print(f"{out}\nSubject: {pk['subject']} | {len(pk['roadmap']['milestones'])} milestones, {len(pk['concepts'])} concepts, {len(pk['diagrams'])} diagrams")
    print("Copy this file to the other device, then run: teach.py unpack <file>   (or /teaching-harness:unpack <file>)")


def _valid(pk):
    try:
        return (pk["format"] == FORMAT and int(pk["version"]) <= VERSION and isinstance(pk["roadmap"]["milestones"], list)
                and isinstance(pk["roadmap"]["goal"], str) and isinstance(pk["state"], dict) and isinstance(pk["concepts"], dict))
    except Exception:
        return False


def cmd_unpack(a):
    force = "--force" in a
    args = [x for x in a if x != "--force"]
    if not args:
        print("usage: unpack FILE [--force]"); return 1
    try:
        pk = json.loads(Path(args[0]).read_text())
    except Exception as e:
        print(f"Cannot read pack: {e}"); return 1
    if not _valid(pk):
        print("Not a valid teaching-harness pack (or made by a newer version)."); return 1
    cur = load_roadmap()
    if cur and not force:
        print(f"This project already has a roadmap ('{cur['goal']}'). Unpacking would replace it.\n"
              "Re-run with --force to proceed (the current roadmap is backed up to .teach/backup/)."); return 1
    td = teach_dir()
    if cur:
        b = td / "backup"; b.mkdir(exist_ok=True)
        (b / f"roadmap-{time.strftime('%Y%m%d-%H%M%S')}.json").write_text(json.dumps(cur, indent=2))
    save_roadmap(pk["roadmap"])
    s = load_state()
    if s["mode"] == "off":
        s["mode"] = "learn"
    for k in ("task", "hint_level", "attempts"):
        s[k] = pk["state"].get(k, s[k])
    s["quiz_history"] = pk["state"].get("quiz_history", [])
    s["quiz"] = None
    s["diagrams"] = []
    dd = td / "diagrams"
    for d in pk.get("diagrams", []):
        name = re.sub(r"[^A-Za-z0-9._-]", "-", str(d.get("file", "diagram.html")))[:80]
        if not name.endswith(".html") or name.startswith("."):
            continue
        dd.mkdir(exist_ok=True)
        (dd / name).write_text(str(d.get("html", "")))
        s["diagrams"].append({"title": str(d.get("title", name)), "path": str(Path(".teach/diagrams") / name), "at": d.get("at")})
    save_state(s)
    # merge concept evidence: keep whichever side was seen more recently; never lose local-only concepts
    p = load_learner(); added = updated = 0
    for k, v in pk["concepts"].items():
        mine = p["concepts"].get(k)
        if mine is None:
            p["concepts"][k] = v; added += 1
        elif (v.get("last_seen") or "") > (mine.get("last_seen") or ""):
            p["concepts"][k] = v; updated += 1
    lr = pk.get("learner", {})
    for g in lr.get("goals", []):
        if g not in p["goals"]:
            p["goals"].append(g)
    save_learner(p)
    print(f"Loaded '{pk['subject']}' into this project (harness active, mode {s['mode']}).")
    print(f"Concepts: {added} added, {updated} updated from the pack; local-only concepts kept.")
