#!/usr/bin/env python3
"""PreToolUse guard. In `learn` mode the agent may read, search and run code, but may not
modify the learner's project. Only <project>/.teach/ (scratch + state) is writable.

Bash is checked heuristically (best effort, not a sandbox): it catches the common ways of
writing files. It exists to make the *teaching behaviour structural* rather than a request
the model can be talked out of.
"""
import json, os, re, shlex, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))
from pathlib import Path
from teachlib import load_state, project_dir, log_event

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
BASH_WRITE = re.compile(
    r"(?<![<=>-])>{1,2}(?![=>&])"      # redirects (after stripping /dev/null forms)
    r"|\btee\b|\bsed\s+(-[a-zA-Z]*i|--in-place)|\bperl\s+-[a-zA-Z]*i\b"
    r"|\b(cp|mv|rm|rmdir|touch|truncate|install|patch|dd)\b"
    r"|\bgit\s+(apply|checkout\s+--|restore|reset\s+--hard|clean|stash|am|cherry-pick|merge|rebase|commit)\b"
)

DENY = ("Learn mode is on: the agent does not write the learner's code. "
        "Guide with questions/hints instead (see the teach skill). "
        "Scratch space for demos: .teach/scratch/. "
        "If the learner wants the agent to write code, they can switch with /teaching-harness:mode pair or review.")


def is_teach_cli(cmd: str) -> bool:
    """True only for a single `python3 <plugin>/bin/teach.py ...` invocation with no shell chaining."""
    if "\n" in cmd or "`" in cmd or "$(" in cmd or "${" in cmd:
        return False
    try:
        lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        toks = list(lex)
    except ValueError:
        return False
    if len(toks) < 2 or os.path.basename(toks[0]) not in ("python", "python3"):
        return False
    root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    want = os.path.realpath(os.path.join(root, "bin", "teach.py")) if root else None
    if (want and os.path.realpath(toks[1]) != want) or (not want and os.path.basename(toks[1]) != "teach.py"):
        return False
    return not any(t and set(t) <= set("();<>|&") for t in toks[2:])


def deny(reason=DENY):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                              "permissionDecision": "deny",
                                              "permissionDecisionReason": reason}}))
    sys.exit(0)


def inside_teach(path: str) -> bool:
    try:
        p = Path(path)
        p = (project_dir() / p) if not p.is_absolute() else p
        p.resolve().relative_to((project_dir() / ".teach").resolve())
        return True
    except Exception:
        return False


def decide(tool, inp):
    """Pure policy for learn mode: returns a denial reason, or None if the call is allowed."""
    inp = inp or {}
    if tool in WRITE_TOOLS:
        path = inp.get("file_path") or inp.get("notebook_path") or ""
        return None if inside_teach(path) else DENY
    if tool == "Bash":
        cmd = inp.get("command", "")
        if is_teach_cli(cmd):
            return None
        cleaned = re.sub(r"\d*>&\d+|&?>\s*/dev/null|\d*>\s*/dev/null", "", cmd)
        if BASH_WRITE.search(cleaned) and ".teach/" not in cmd:
            return DENY + " (Blocked a shell command that looks like it modifies files.)"
    return None


def main():
    try:
        ev = json.load(sys.stdin)
    except Exception:
        return
    if load_state()["mode"] != "learn":
        return
    tool, inp = ev.get("tool_name"), ev.get("tool_input") or {}
    reason = decide(tool, inp)
    if reason:
        log_event("guard_deny", tool=tool, detail=str(inp.get("file_path") or inp.get("notebook_path") or inp.get("command") or "")[:200])
        deny(reason)


if __name__ == "__main__":
    main()
