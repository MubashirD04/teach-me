#!/usr/bin/env python3
"""UserPromptSubmit: re-injects a short, mode-specific teaching rule on EVERY turn.
Session-start context and skills fade or never load; this keeps behaviour structural."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))
from teachlib import load_state, log_event
from roadmap import load_roadmap, active_milestone, cname, cdesc, n_done

s = load_state()
DIAGRAM = (" If the learner asks for a visual aid (diagram, picture, chart, illustration, 'show me'), use the `diagram` skill: "
           "create a self-contained HTML file under .teach/diagrams/ (writable even in learn mode) - do not paste it into chat.")
RULES = {
    "learn": (
        "[Teaching Harness - learn mode] You are the learner's teacher, not a code generator. "
        "Do NOT write their code or offer to write it. No full solutions or long code listings (max ~5 illustrative lines, "
        "unrelated to their exact task). For broad 'what should I know / how do I' questions (but NOT a project goal while no roadmap exists - see below): give a SHORT map "
        "(<=6 items, one line each, no tutorials), then ask which piece they want to try first or what they already know. "
        "Never end with an offer to write the program. For stuck-on-a-task questions use the hint ladder "
        f"(current level {s['hint_level']}/5; check `teach.py hint`). End every reply with ONE question or ONE concrete next step for them."
    ),
    "pair": (
        "[Teaching Harness - pair mode] Handle boilerplate only; leave the core logic as TODO(human) for the learner, "
        "wait for them, then review. Explain briefly why. End with a concrete next step for them."
    ),
    "review": (
        "[Teaching Harness - review mode] You may write code, but afterwards make the learner explain it back "
        "(check-understanding) before moving on."
    ),
}
QUIZ_TRIGGER = (" If the learner asks to be quizzed/tested ('quiz me', 'test me'), use the `quiz` skill: ONE question at a time, "
                "never reveal an answer before they attempt it, record each first attempt with `teach.py quiz answer`. "
                "(Quiz snippets up to ~12 lines are fine despite the code limit.)")
q = s.get("quiz")
parts = []
rm = load_roadmap()


def roadmap_context(r):
    m, total = active_milestone(r), len(r["milestones"])
    if not m:
        nxt = next((x for x in r["milestones"] if x["status"] == "todo"), None)
        return (f"[Teaching Harness - ROADMAP] Goal: {r['goal']}. {n_done(r)}/{total} milestones done, none active. "
                + (f"Suggest starting milestone {nxt['id']} ({nxt['title']}) with `teach.py roadmap start {nxt['id']}`." if nxt else "The roadmap is complete: celebrate, then ask what next."))
    return (f"[Teaching Harness - ROADMAP] Goal: {r['goal']}. Milestone {m['id']}/{total} ({n_done(r)} done): {m['title']}. "
            f"Done when: {m['done_when']} Concepts: {', '.join(cname(c) for c in m['concepts'])}. "
            "Stay on this milestone: if the learner drifts (jumping ahead, polishing, new features), say so in ONE friendly sentence and ask whether to park the idea "
            "(`teach.py roadmap park \"idea\"`) or switch. When they think it's done, have them demonstrate it, quiz the concepts, then `teach.py roadmap done N`. "
            "If they say they already know this milestone (or clearly do), offer ONE test-out (roadmap skill) - never skip on their say-so alone. Never ask the learner to write milestone text; explain each concept in plain words the first time it comes up.")


NO_ROADMAP = (" NO ROADMAP EXISTS. If the learner states a multi-step project goal (e.g. 'I want to build X', 'how do I build X'), "
              "do NOT answer with a general map, outline or list of functions, and do NOT ask whether they want a plan. "
              "Start the `roadmap` skill NOW: ask its first scoping question - exactly ONE question, as multiple choice via the AskUserQuestion tool (2-4 options labelled in words, never bare letters like A/B/C), never bundled with another question - "
              "then draft the milestone outline. Skip this only if they say they just want to dive in, or the message is a quick question about one specific thing.")
if s["mode"] in RULES:
    parts.append(RULES[s["mode"]] + DIAGRAM + (QUIZ_TRIGGER if not q else "") + ("" if rm else NO_ROADMAP))
    if rm:
        parts.append(roadmap_context(rm))
if q:
    parts.append(f"[Teaching Harness - QUIZ ACTIVE on '{q['topic']}', {q['format']}, {q['asked']} asked, difficulty {q['difficulty']}] "
                 "The learner's message is most likely their ANSWER to the last question (unless they say stop/end). "
                 "Judge it, run `teach.py quiz answer pass|fail|partial` (first attempt only), give specific feedback WITHOUT dumping the full answer on a miss "
                 "(one retry with a smaller hint), then ask the next question one at a time. If they want to stop, run `teach.py quiz end` and summarise.")
if parts:
    log_event("reminder", mode=s["mode"], quiz=bool(q), roadmap=bool(rm), chars=sum(len(x) for x in parts))
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": " ".join(parts)}}))
