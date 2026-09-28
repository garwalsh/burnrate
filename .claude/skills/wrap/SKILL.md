---
name: wrap
description: End-of-session handoff for Burnrate. Writes everything a fresh Claude session needs into the repo (devlog, design doc, AGENTS.md, memory), then commits. Use when Gar says /wrap, "wrap up", or "end the session".
---

# Wrap up the session

A new session starts with only AGENTS.md, memory, the files and git history. Anything that lives only in this conversation is lost. Your job is to move it into the files, then commit.

## 1. Review the session

Look back over this conversation and list, for yourself:
- Runs or experiments done, with their numbers
- Decisions made, and the reason for each
- Anything half-done or broken
- The next step Gar agreed to, or the obvious one if none was agreed
- New preferences about how Gar wants to work
- Surprises: bugs, tool quirks, things that took longer than expected

Then run `git status` and `git diff --stat` to see what changed on disk.

## 2. Update the files

Only touch a file if this session changed something it records. Skip anything already written down.

| What | Where |
| --- | --- |
| A run or experiment | `DEVLOG.md`, new entry at the top, five-field format (Changed, Ran, Saw, Means, Next) |
| A design decision | `DESIGN.md`, settled or open decisions, dated |
| Where things stand, next step | `DESIGN.md`, "Picking this up" section. Rewrite it so it's true today, and update its date |
| A block closed | Draft the Block log entry and show Gar. Don't write it until he confirms |
| A new rule for how we work | `AGENTS.md` |
| A preference about Gar himself | Memory |

Follow the writing rules in AGENTS.md: no em dashes, no "not X, but Y", numbers over adjectives.

## 3. Show Gar

Give a short summary:
- Files changed, one line each on what was added
- The next step as written in "Picking this up"
- Anything left uncommitted or unresolved

Ask him to confirm before committing.

## 4. Commit and push

Once he says yes: run the `/commit` format (emoji type, present tense, the why), commit everything relevant, and push. Never commit NOTES.md or content/. Before pushing, check the diff for secrets, personal paths or email addresses, since the repo is public.

Finish with one line Gar can paste to start the next session, e.g. "Read DESIGN.md 'Picking this up' and start the next step."
