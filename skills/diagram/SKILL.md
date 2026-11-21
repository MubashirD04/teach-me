---
name: diagram
description: Create an HTML visual aid (diagram, flow, memory layout, step-through) when the learner asks for a visual, picture, diagram, chart, illustration, or says they're a visual learner or "can't picture" something.
---

# Diagram: make the concept visible

Trigger: the learner asks for a visual aid in any wording ("diagram", "draw", "show me", "visualise", "can you picture", "a chart of..."),
or `/teaching-harness:diagram <topic>`. You may also *offer* one (one line) when a concept is inherently spatial
(memory/pointers, process trees, call stacks, pipes and file descriptors, request/response flows) - but only create it if they say yes.

## Steps
1. Get the path: `python3 "${CLAUDE_PLUGIN_ROOT}/bin/teach.py" diagram "<short title>"`
   It prints a safe path like `.teach/diagrams/fork-and-exec.html` and logs it. **Write only to that path** - `.teach/` is the one
   place you may write in learn mode.
2. Read `${CLAUDE_PLUGIN_ROOT}/skills/diagram/template.html` and start from it. Output must be **one self-contained HTML file**:
   inline CSS, inline SVG/JS, no CDN links, no external fonts or images. It must work by double-clicking the file.
3. Tell the learner the path (relative to the project) and how to open it. Don't paste the HTML into chat.
4. Follow up with ONE question about the diagram ("Before you click Next: what do you think `fork()` returns in the child?").

## Design rules
- **Diagram the concept, not their answer.** In learn mode the visual must not contain the solution to their current task; use a
  generic or analogous example. (A picture of how `fork`/`exec`/`wait` interact is fine; a finished shell is not.)
- Small and focused: one idea per diagram, roughly 3-8 labelled parts. Split into several files rather than one dense one.
- Prefer a **step-through** (the template's Prev/Next) for anything that happens over time: processes, loops, call stacks, data flow.
  Use a static layout for structure: memory layout, struct fields, architecture.
- Label everything in plain words. Every box and arrow gets a label; every step gets a one-sentence caption.
- Show real values where possible (addresses, bytes, return values) - concrete beats abstract for juniors.
- Accessible: sufficient contrast, works in light and dark, no information conveyed by colour alone.
- Add a short "Try this" line at the bottom pointing back to something they can run or change in their own code.

## After
Record it as evidence they engaged: when they answer your follow-up, run `teach.py concept "<topic>" pass|fail` as usual.
If the diagram didn't land, try a different representation (analogy, trace table, smaller example) rather than repeating it.
