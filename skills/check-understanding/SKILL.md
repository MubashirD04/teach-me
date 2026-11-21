---
name: check-understanding
description: Verify the learner actually understood something before moving on - after a hint at level 4-5, after you wrote code in review mode, or at the end of a task.
---

# Check understanding (don't trust "I get it")

Pick one or two of these, matched to what was just done. Ask them, wait for the answer, don't answer for them.

- **Predict**: "Before I run this, what will it print / which test will fail, and why?"
- **Explain back**: "Walk me through this block as if teaching a teammate."
- **Change it**: "What would you change to make it handle <edge case>?" (they write it)
- **Break it**: "Change one line so the test fails. Which line, and why does it fail?"
- **Transfer**: a similar problem in a different setting, without the previous solution visible.

Mark the result honestly: `teach.py concept "<name>" pass|fail`. A fail is useful - go back down the hint ladder
(`teach.py hint --reset`) and approach it from a different angle. Only call the task done on a pass.
