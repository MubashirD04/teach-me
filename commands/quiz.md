---
description: Quiz me (optionally on a topic; add "quick" for multiple choice)
argument-hint: [topic] [quick]
allowed-tools: Bash(python3:*), Bash(gcc:*), Bash(cc:*), Bash(python:*), Read, Write
---
The learner wants to be quizzed. Topic/options: $ARGUMENTS (empty = pick from their weak concepts).
Load and follow the `quiz` skill: choose the topic, run `teach.py quiz start`, then ask ONE question and wait for their answer.
