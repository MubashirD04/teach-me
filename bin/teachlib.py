"""Shared state helpers for the Teaching Harness.

Two stores:
  * project state   -> <project>/.teach/state.json   (mode, current task, hint level)
  * learner profile -> ~/.teach/learner.json         (goals, level, concepts; persists across projects)
"""
import json, os, time
from pathlib import Path

MODES = ("learn", "pair", "review", "off")
LADDER = {
    1: "QUESTION  - ask an open question about what they've tried / expect. No hints.",
    2: "NUDGE     - point at the relevant area or concept (file, function, error line). No code.",
    3: "PRINCIPLE - explain the underlying concept or pattern in prose, plus a tiny unrelated example.",
    4: "SCAFFOLD  - pseudocode or a skeleton with blanks for the learner to fill in.",
    5: "SOLUTION  - show the full solution, then walk through it and ask them to re-derive one part.",
}
MIN_ATTEMPTS_FOR_LEVEL = {4: 2, 5: 3}  # attempts required before escalating, unless forced


def project_dir() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def teach_dir(create: bool = True) -> Path:
    """<project>/.teach. Pass create=False for reads so inactive projects are never touched."""
    d = project_dir() / ".teach"
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d


def is_active() -> bool:
    """A project has opted in to the harness once .teach/state.json exists."""
    return (project_dir() / ".teach" / "state.json").exists()


def home_dir() -> Path:
    d = Path(os.environ.get("TEACH_HOME") or Path.home() / ".teach")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _load(path: Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def _save(path: Path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(path)


def load_state():
    raw = _load(teach_dir(False) / "state.json", None)
    s = raw or {}
    s.setdefault("mode", "learn" if raw is not None else "off")   # not opted in => inert
    s.setdefault("task", None)
    s.setdefault("hint_level", 0)
    s.setdefault("attempts", 0)
    s.setdefault("solutions_shown", [])
    s.setdefault("quiz", None)
    s.setdefault("quiz_history", [])
    return s


def save_state(s):
    _save(teach_dir() / "state.json", s)


def load_learner():
    p = _load(home_dir() / "learner.json", {})
    p.setdefault("goals", [])
    p.setdefault("level", "junior")
    p.setdefault("interests", [])
    p.setdefault("concepts", {})   # name -> {pass, fail, last_seen, hints_needed}
    p.setdefault("onboarded", False)
    return p


def save_learner(p):
    _save(home_dir() / "learner.json", p)


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def days_since(iso):
    """Days since an ISO timestamp; unknown counts as 30 (treated as stale)."""
    if not iso:
        return 30.0
    try:
        return (time.time() - time.mktime(time.strptime(iso, "%Y-%m-%dT%H:%M:%S"))) / 86400
    except Exception:
        return 30.0


def concept_priority(c):
    """Higher = more worth practising: weak, needed hints, or stale."""
    return (c["fail"] - c["pass"]) * 2 + c["hints_needed"] + min(days_since(c.get("last_seen")), 30) / 10


def log_event(kind, **data):
    """Append one line to .teach/events.jsonl (only for opted-in projects; never raises)."""
    if os.environ.get("TEACH_NO_LOG") or not is_active():
        return
    try:
        p = teach_dir() / "events.jsonl"
        with p.open("a") as f:
            f.write(json.dumps({"t": now(), "kind": kind, **data}) + "\n")
        if p.stat().st_size > 500_000:
            p.write_text("\n".join(p.read_text().splitlines()[-1000:]) + "\n")
    except Exception:
        pass
