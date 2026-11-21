---
description: Create an HTML visual aid (diagram) for a concept
argument-hint: <concept to visualise>
allowed-tools: Bash(python3:*), Read, Write
---
The learner wants a visual aid for: $ARGUMENTS (if empty, ask what they want visualised, in one short question).
Load and follow the `diagram` skill: get the path from `teach.py diagram`, build one self-contained HTML file from the template,
write it only under `.teach/diagrams/`, tell them where it is, and ask one question about it.
