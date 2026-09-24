# Burnrate

An open-world economy where AI agents coexist in a free market and compete to be the most financially successful. Players write a strategy sheet; the house runs every agent on the same small open-weight model. Business replaces combat. Built in the open to research open-weight models with a fun use case.

## Files

- `DESIGN.md`: source of truth. Vision, settled decisions, open decisions, primitives, block plan, block log.
- `DEVLOG.md`: running log of every experiment, newest at the bottom.
- `experiments/`: one script per block (`block1_ledger.py`, `block2_market.py`, `block2_batch.py`, `block3_journal.py`) plus their output logs and `runs*/` folders. Rules and sheets are constants at the top of each file. Run scripts from inside the folder (`cd experiments`) so outputs land next to them.

Read `DESIGN.md` before proposing any design change.

## Settled decisions

Do not reopen these unless a result contradicts them. Full list in `DESIGN.md`.

- Players never bring a model. House model runs every agent.
- Token budget per agent per tick. Thinking costs in-world money.
- Forced mechanics stay light. Primitives, not features. Fewest mechanics, most strategies.
- You have to be alive to win.
- The player owns the reflection loop. The house model executes the sheet; it does not author or learn.
- Keep the model in the loop. No compiling sheets into deterministic code.

## Environment

- Mac, M1 Max, 64GB. System Python 3.9.6, run with `python3`. `requests` installed.
- Ollama runs models locally. Current house model: `qwen2.5:7b`.
- Model ladder: test the world on the strongest local model first (`qwen3.6:27b`), then step down (qwen3 14B, then `qwen2.5:7b`). Turn off Qwen3 thinking mode so it doesn't break the reply parser.
- Long runs: `cd experiments && caffeinate -i python3 <script>.py` so the Mac doesn't sleep.
- Local models only. Paid API runs only when a local result is ambiguous, and ask first.

## How we work

- Ship the next block and show results. Design talk without progress is a waste.
- One variable per experiment. n = 3 per setting minimum before believing a comparison.
- Check the harness before believing an agent-behaviour finding. Three early "findings" were our own bugs.
- Keep rules as constants at the top of the script.
- Add a dry-run path with a fake model so plumbing can be tested in seconds.

## Logging

- After each run, add a `DEVLOG.md` entry in the five-field format: Changed, Ran, Saw, Means, Next. Numbers over adjectives. Mark findings "unconfirmed" until they repeat.
- When a block closes, draft a Block log entry for `DESIGN.md` and wait for Gar to confirm before writing it.

## Working with Gar

- Brief and direct. No flattery. If an idea is wrong, say so.
- He is a product person, not a Python developer. Explain tooling in plain terms, give exact commands to type, and describe code changes as short pseudocode rather than walls of Python.
- Writing for him (docs, posts, READMEs): no em dashes, no "not X, but Y" constructions, no AI tells. To the point, playful but not fluffy. Review before handing over.
