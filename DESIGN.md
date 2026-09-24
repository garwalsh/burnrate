# Business MMO design

Sep 21, 2026 · @Gar

## Vision

Burnrate: a seasonal public competition shaped like an MMORPG where combat is replaced by business.

Players submit a playbook: a strategy prompt under a hard token limit. The house runs every agent on the same small open-weight model. The most successful business at season end wins.

Seasons last a few days. Then the world resets and one new mechanic is added.

**Why.** The idea came from dead metaverses: what happens if you populate one with agents? The end goal is an open world where agents coexist in a free market, each trying to become the most successful. It doubles as a way to research open-weight models with a fun use case. Public posts lead with this vision and the why; mechanics and seasons come later.

## Settled decisions

Do not reopen these unless a result contradicts them.

- House model, player prompt. Players never bring a model. Using a bigger model to write your playbook is fine.
- Token budget per agent per tick, so inference cost is capped by design.
- Forced mechanics stay light. Design primitives, not features.
- Emergent strategies are the point. If a loan shark playbook can win, the design works.
- Thinking is a resource: reasoning costs in-world money.
- Hidden information and noise so raw intelligence has diminishing returns.
- Prior art: Screeps (CPU budget, server runs your code, open-source private servers).
- You have to be alive to win. Dead agents don't rank, whatever they died holding. (Sep 21, from Block 1.)
- House model is qwen2.5:7b, replacing llama3.2. The floor for any house model is following a playbook, and llama3.2 is below it. (Sep 21, from Block 2.)
- The player owns the reflection loop. The player reads the run, spots the pattern and rewrites the playbook; the house model executes. Otherwise the game becomes model vs model. Players feeding results to a stronger model to update their playbook is fine, since they still have to take part in the loop. (Sep 22, from Block 3.)
- Keep the model in the loop. Compiling English playbooks into deterministic server-side code is rejected: chance and non-deterministic strategy are part of the game. The challenge: can a player prompt an agent to join an economy and deal with other agents so it ends up the most financially successful, by any means? The world should be loose enough for many strategies (buying wholesale and reselling retail, side deals, boycotts) built from the fewest mechanics. Closer to RuneScape: messaging, currency, goods, trading, few levers, complex economies. (Sep 23.)

## Open decisions

Parked until Gar raises them.

- Classes and attribute points on top of the playbook. Not sold yet. (Sep 24.)
- Contract enforcement: world / nobody (reputation only) / optional collateral. Leaning nobody or collateral.
- Is persuading another agent by message to hand over money legal play? Leaning yes with message limits.
- One forced pressure that makes deals necessary, so the world doesn't stall.
- Tick rhythm: publish a turn at a fixed interval (every few hours) no matter how fast it computes. Compute offline, publish on a clock, so players have a reason to come back and there's no real-time load. (Sep 23.)
- Do players act between ticks? Locked playbook means the whole season can be computed in advance, but the tick is theatre. Reacting between ticks is the reason to return, but rewards whoever is online at 3am. Leaning: playbook locked for the season plus a small budget of directives (around 3), each a short instruction delivered on the next tick, so the decision is when to spend them. (Sep 23.)
- Who pays for inference at scale. Levers: cap agents per player, offline batching, free tier of one agent, players supplying their own key pinned to the house model. (Sep 23.)
- Season scoring metric. Cash alone rewards hoarding, which drove a lot of Block 2's behavior. (Sep 23.)
- How players reach the game. Wants: players play free on compute they already pay for (Claude or ChatGPT subscriptions), with model capability limited. Gar is fine paying to host the world. No entry fee, and no free season paid for by Gar as the answer to inference cost. One option: an MCP server. (Sep 22.)
- How far to build before recruiting collaborators. Some UI would help, even a dashboard that runs during a season. (Sep 22.)

## Primitives

- Transfer money
- Transfer goods
- Structured contract (X now for Y at tick T)
- Message another agent
- Public ledger of balances and contract history
- Ticks with a world interest rate

## Seasons

- Reset every few days
- One new mechanic per reset
- Patch notes
- Nerf the dominant playbook
- Hidden per-season parameters
- Balance so no playbook beats every matchup

## Risks

- Meta collapse: one playbook copied by all
- Prompt injection through agent messages
- Inference cost at public scale
- A world where nothing happens

## Block plan

Each block ends with something to look at and a question it answers.

| Block | What ships | Question it answers |
| --- | --- | --- |
| 1 | Ledger-only economy, 5 agents, local model | Does the model respond to scarcity or roleplay? |
| 2 | Add a market | Does a price form and move under shocks? |
| 3 | DONE (Sep 23). Journal farmer: a principle sheet plus a journal across 5 games, plan before each game, lessons after. Replaced the old Block 3 (persistence and memory) and pulled sheets forward from Block 4. | Does an agent invent a strategy and explain it, and does its own history change it? |
| 4 | NEXT. A thicker world: 3 or 4 goods, agents better at making different ones, at least one good needing an input. Named bilateral trade and private messages replace the anonymous auction. | Does the world support more than one viable strategy? Run 3 different playbooks, n = 3 each. |
| 5 | Deals with no enforcement: offers, acceptance, promises that can be broken, and a post-season reveal of all private messages. | Can the house model negotiate, honour a deal, and break one? Untested, and load-bearing for the whole design. |
| 6 | The player loop: run report, replay viewer, ticks published on a clock, playbook submission, directive budget. Closed alpha with 5 friends. | Can a player spot a planted pattern from the report alone, and beat the house playbooks? What do they exploit? |
| 7 | Web app and first public season: accounts, submission, tick scheduler, leaderboard, replays. | Can strangers play without Gar in the loop, and does anyone care? |

## Picking this up (as of Sep 23, 2026)

**Where it stands.** Blocks 1 to 3 are done, all three with negative or narrow results. The through-line: the house model executes a playbook faithfully and cannot author strategy or learn from its own history. So the player owns the thinking loop (watch a run, spot what the world is doing, rewrite the playbook) and the agent owns execution. The sim as built is one good, one anonymous auction, identical information for everyone, which leaves pricing as the only strategy. Block 4 is about giving the world enough surface for strategies to differ.

**Code**, in Gar's `burnrate` folder, Python 3.9, Ollama running qwen2.5:7b locally:

- `block2_market.py` is the world. 5 agents (2 farmers, 3 workers), think cost, eat-or-starve, spoilage above 6 food, a call auction that clears once a turn, a hidden drought at T15 to T22, and per-agent strategy sheets (the code's name for playbooks). Rules and sheets are constants at the top. Writes a per-turn CSV and a price CSV.
- `block2_batch.py` runs it N times per arm (drought vs control) and prints one comparison table.
- `block3_journal.py` runs 5 games with one agent on a principle sheet plus a journal that survives between games, writing `block3_journal.md`.

**How we work.** One variable per run. n = 3 per setting minimum, because single-run comparisons produced two false findings in Block 2. Every run gets logged in the Burnrate dev log with what changed, what ran, what was seen, what it means, and what's next. Before believing an agent-behaviour finding, check the harness first: three early "findings" were our own bugs (a price in the prompt example anchored all trades, an answer-first reply format forced the agent's first word, and agents saw trades but never the order book).

**Open threads not yet in a block:** what a playbook can express before fidelity breaks (does qwen honour a conditional?), the scoring metric, and the tick rhythm plus directive budget in Open decisions.

**Model ladder (agreed Sep 23).** Testing the world on a small model confounds two questions: is the world thin, or is the model too weak to see what's in it? So from Block 4 on, the world is tested on the strongest model Gar's Mac can run (M1 Max, 64GB) first. If it finds several distinct ways to win, the world is rich enough. Then its winning strategies get written up as playbooks and handed to smaller and smaller models. The smallest one that still follows them faithfully becomes the house model, since the production model needs to be obedient, not clever (the player does the thinking). Ladder: qwen3.6:27b (top), a qwen3 14B (middle), qwen2.5:7b (current house model). All local and free; pay for an API run set only when a local result is ambiguous. Expect about an hour per game on the top rung, so test sets run overnight.

**Next step.** Gar pulls `qwen3.6:27b` (about 17GB) and checks it replies. Then: switch the model in `block2_market.py`, turn off Qwen3's built-in thinking mode so it doesn't slow the run or break the reply parser, and start Block 4 step 1. Block 4 is built in steps, one run set each: (1) named offers replace the auction, one good; (2) private messages; (3) extra goods and an input chain; (4) the 3-playbook test that closes the block. Possibly the first job done in Claude Code.

## Block log

### Block 1: ledger-only economy (Sep 21, 2026). 9 runs, llama3.2.

**Question:** does the model respond to scarcity or roleplay? **Answer:** both, badly. It reads its state but tracks one number at a time. Left alone, it works every turn and starves with 40+ cash (12 of 15 neutral agents). A persona doesn't cause the failure, it picks which one you get: cautious and lazy fixate on food and go broke, the rest starve rich. Survival: 0 of 15 with personas, 2 of 15 without.

**Rules finding:** the economy is a treadmill. Alternating work and buy ends the game at 0 cash; best case is about 27. Dead agents posted the highest cash numbers, which is why "alive to win" is now a settled decision.

**Design implication:** the house model won't find a two-variable loop on its own, so the player's sheet has to carry the policy. That's compatible with the vision (the sheet is the skill), but the game doesn't really start until Block 4's sheet loader.

**Harness:** 20 to 45 seconds a run, zero parse failures in 45 agent-lives. Full run-by-run detail in the Burnrate dev log.

### Block 2: add a market (Sep 21 to 22, 2026). 10 runs plus a 6-run batch.

**Question:** does a price form and move under shocks? **Answer:** a price forms reliably, once agents run on strategy sheets. Whether it moves under a shock depends on the sheets, not the market. With sellers who price off the last trade and ignore bids, a mid-game drought showed no price effect across 3 drought and 3 control runs; run-to-run noise was bigger than any shock.

**Model finding:** agents built from rules alone don't trade on either model. llama3.2 misreads the rules (farmers buying food, workers resting to "conserve energy") and can't follow a sheet. qwen2.5:7b understands the rules, procrastinates without a sheet, and follows a sheet almost perfectly. House model is now qwen2.5:7b.

**Harness findings:** three early results were our bugs. A price in the prompt's example reply anchored every trade. An answer-first format forced the first word and hid the reasoning. Agents saw trades but not orders, so a market with no trades looked empty. Single-run comparisons fooled us twice: n = 3 per setting minimum from here.

**Design implication:** sheets don't just steer agents, they shape the market (a pricing rule that ratchets up drove prices more than the drought did). Rule sheets give fidelity but no room for invention. The next question is what a looser sheet plus memory produces.

### Block 3: journal farmer (Sep 22 to 23, 2026). 5 games, qwen2.5:7b.

**Question:** does an agent invent a strategy and explain it, and does its own history change it? **Answer:** no, on both counts. Ada wrote the same plan five times (farm for N turns, then sell, then sell aggressively and "buy low", a move a farmer has no use for). The only thing that changed was N: 10, 15, 12, 10, 15. Her lessons were fluent and empty: be more dynamic, adjust to market trends, time sales better. Never a mechanism change.

**The planted pattern was missed.** Her harvest drops from 3 to 1 for turns 15 to 22 of every game, and it sits in her own turn record. No plan or lesson ever mentioned it.

**She also lost:** Ada averaged 145 cash across five games against Bram's 165 on a fixed rule sheet, losing 4 of 5.

**Design implication:** the house model executes, it does not author or learn. The reflection loop belongs to the player: watch the run, spot what the world is doing, rewrite the sheet. That makes the run report a first-class artifact (players can only spot what they can see) and raises the real open question, which is how much a sheet can express before fidelity breaks.
