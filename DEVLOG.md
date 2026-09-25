# Burnrate dev log

Sep 21, 2026 · @Gar

Running notes on building Burnrate. The design doc holds the decisions. This is the story of how we got there: what we tried, what happened, what it meant.

Entries are reverse chronological, newest at the top. One entry per experiment or decision, not per day.

### 2026-09-23 · Block 3 · Results: same plan five times, drought never noticed. Block 3 closed.

- **Changed:** nothing. The Block 3 setup as written.
- **Ran:** 5 games of block3\_journal.py on qwen2.5:7b. Ada on the principle sheet plus journal; everyone else on the Block 2 rule sheets. Drought T15 to T22 every game, unannounced. (Entry written after the fact from the Block log summary in DESIGN.md.)
- **Saw:** Ada wrote the same plan all five games: farm for N turns, then sell, then sell aggressively and "buy low" (useless for a farmer). Only N changed: 10, 15, 12, 10, 15. Lessons were fluent and empty (be more dynamic, adjust to market trends, time sales better). No mechanism change, ever. Her harvest dropped from 3 to 1 for T15 to T22 in every game and sat in her own turn record; no plan or lesson mentioned it. She averaged 145 cash against Bram's 165 on a fixed rule sheet, losing 4 of 5.
- **Means:** n = 5 games, consistent across all of them. The house model executes a sheet; it doesn't author strategy or learn from its own history. The reflection loop belongs to the player: watch the run, spot the pattern, rewrite the sheet. That makes the run report a first-class artifact, and the real open question becomes how much a sheet can express before fidelity breaks.
- **Next:** Block 4 on the model ladder. Pull qwen3.6:27b, check it replies, switch the model in block2\_market.py with thinking mode off, then step 1: named offers replace the auction.

### 2026-09-22 · Block 3 · Setup: the journal farmer

- **Changed:** Gar reframed the goal: the most interesting result is an agent inventing a strategy and explaining it well, even if it fails, and better still if it changed strategy because of patterns it read in its own history. Block plan updated: new Block 3 replaces persistence and memory. New script block3\_journal.py. Ada gets a principle sheet ("free to invent your own approach; keep 2 food, never below 5 cash; otherwise maximize cash") and a journal that survives between games. Everyone else keeps the Block 2 rule sheets. Drought stays at T15 to T22 every game, unannounced: a real pattern to find. Per game: Ada writes a plan before play from her journal only (pre-registered), plays 40 turns with the plan in her prompt, then sees her turn-by-turn record (including harvest size) and the price series and writes lessons. 5 games. block2\_market.py now logs harvest per turn.
- **Ran:** fake-model dry run, 2 games. Journal, plan injection and lessons prompts as expected.
- **Saw:** plumbing works.
- **Means:** judged on novelty (a plan we didn't write), fidelity (did she do what she planned), and grounding (do plan changes cite something that happened). The drought is the test case: does she notice her yield drops mid-game, and plan around it?
- **Next:** run it: `caffeinate -i python3 block3_journal.py`, about 50 minutes. Read block3\_journal.md.

### 2026-09-22 · Block 2 · Batch 1: the drought effect doesn't replicate

- **Changed:** nothing. 3 drought and 3 control runs on qwen2.5:7b with Run 8's sheets, alternating arms.
- **Ran:** 6 runs, 7 to 13 minutes each, zero parse failures.
- **Saw:**

| Pair | T1-14 drought / control | T15-22 drought / control | T23-40 drought / control | Workers alive D / C |
| --- | --- | --- | --- | --- |
| 1 | 4.5 / 5.1 | 4.7 / 5.2 | 8.6 / 3.8 | 1 / 1 |
| 2 | 3.8 / 4.0 | 5.0 / 3.9 | 7.5 / 3.5 | 0 / 3 |
| 3 | 4.6 / 4.6 | 4.7 / 7.6 | 5.6 / 7.7 | 3 / 1 |
| Mean | 4.3 / 4.6 | 4.8 / 5.5 | 7.2 / 5.0 |  |

Trades on 23 to 36 of 40 turns in every run. Drought beat control in the drought window in only 1 of 3 pairs. Control 3 hit 7.6 in that window with no drought at all.

- **Means:** n = 3 per arm. The bar for closing (a clear drought gap in all three pairs) failed. The Run 8 vs 9 result was noise: run-to-run variance (control prices from 3.9 to 7.6 in the same window) is bigger than any drought effect. A price forms reliably; a price response to the shock does not show. Likely reason, from the sheet design: farmers price off the last trade and never look at the bids, so scarcity cuts volume rather than raising asks. The only scarcity channel is workers raising bids after misses, and those raises barely register because a farmer with no surplus posts no ask, so no trade happens at the higher bid. Possible lagged effect: drought runs finished higher after T23 in 2 of 3 pairs (mean +2.2), which would fit a ratchet the drought kicks off, but pair 3 contradicts it. Process lesson: single-run comparisons in Blocks 1 and 2 were not reliable; n = 3 per setting minimum from here.
- **Next:** Block 2 closed (Gar agreed Sep 22). Block log entry written to the design doc.

### 2026-09-21 · Block 2 · Decision and batch setup

- **Changed:** Gar agreed: house model is qwen2.5:7b, replacing llama3.2. Written into the design doc's settled decisions. New script block2\_batch.py runs block2\_market.py 3 times per arm, alternating drought and control, and writes one results table (block2\_batch.csv) plus per-run output and logs in runs/. block2\_market.py now defaults to qwen2.5:7b and returns its results to the runner.
- **Ran:** dry run with a fake model: 6 runs, table and files as expected.
- **Saw:** plumbing works.
- **Means:** the batch will give n = 3 per arm for the Run 8 vs Run 9 comparison, about 90 minutes unattended.
- **Next:** run the batch overnight with `caffeinate -i python3 block2_batch.py`. If the drought gap holds across all three pairs, close Block 2.

### 2026-09-21 · Block 2 · Run 10: llama3.2 with sheets, doesn't follow them

- **Changed:** model qwen2.5:7b to llama3.2, drought back on. Same sheets as Run 8.
- **Ran:** 1 run, 40 turns. Elapsed 317s.
- **Saw:** all three workers dead (T6, T15, T37). The sheet says WORK every turn; workers rested 24 of 64 turns (Dot 5 of 6). The sheet says post a SELL every turn; farmers skipped 22 of 80 turns and let 77 food spoil. Trades on 15 of 40 turns, 38 food. Drought window averaged 2.5 against 3.7 before it: wrong way, on only two trades.
- **Means:** unconfirmed, one run, but the gap is large. qwen2.5:7b broke its sheet on almost no turns (Run 8: 7 no-order turns in 200 decisions, zero rests). llama3.2 breaks it constantly, on the simplest instructions ("WORK every turn"). Sheet-following is the floor the whole game stands on, and llama3.2 is below it. The house model decision (llama3.2) needs revisiting. Speed matters here: llama3.2 took 5 minutes, qwen 15, so the cheaper model is only 3x faster.
- **Next:** decide the house model. Then confirm Runs 8 and 9 with repeated drought and control pairs on qwen, run unattended.

### 2026-09-21 · Block 2 · Run 9: no-drought control, the drought effect is real but smaller than it looked

- **Changed:** SHOCK\_START = 0 (no drought). Everything else as Run 8.
- **Ran:** 1 run, 40 turns. Elapsed 859s.
- **Saw:** all five alive, the first full-survival game in Block 2. Trades on 35 of 40 turns, 116 food. Price held at 3 and 4 until about T19, then drifted up slowly to 7 and 8 by T32 to T40. Farmers ended with 486 of 500 total cash; workers finished on 1 to 8 cash.

| Turns | Run 8 (drought) | Run 9 (control) | Gap |
| --- | --- | --- | --- |
| T1 to T14 | 4.9 | 3.5 | +1.4 |
| T15 to T22 (drought window) | 7.2 | 4.1 | +3.1 |
| T23 to T40 | 6.5 | 6.3 | +0.2 |

- **Means:** unconfirmed, one run per arm. The ratchet is real: with no shock at all, price still doubled over the game. But the drought effect shows too. The gap between arms roughly doubled during the drought window (+1.4 to +3.1) and closed after it, which is what a shock should look like. So drought added roughly 1 to 2 per food on top of drift, with n = 1 per arm. Cy's death in Run 8 is the other drought signal: with no drought he survived. Block 2 question, provisional answer: yes, a price forms, and it moves under a supply shock, once agents run on sheets. Side finding for the game: whatever sheets players write will shape the market's drift, not just the agents.
- **Next:** try llama3.2 with the Run 8 sheets and drought. If it follows sheets as well as qwen, repeat drought and control pairs on llama3.2 to firm up n, at a fraction of qwen's 15-minute runs.

### 2026-09-21 · Block 2 · Run 8: sheets work, a real market, price rises but not only from the drought

- **Changed:** see Run 8 setup. Model qwen2.5:7b.
- **Ran:** 1 run, 40 turns. Elapsed 1030s (about 17 minutes).
- **Saw:**

| Agent | Role | Died | Cash | Bought / Sold | Turns with no order |
| --- | --- | --- | --- | --- | --- |
| Bram | farmer | alive | 190 | 0 / 39 | 4 |
| Ada | farmer | alive | 183 | 0 / 36 | 3 |
| Dot | worker | alive | 11 | 30 / 0 | 5 |
| Eli | worker | alive | 4 | 30 / 0 | 1 |
| Cy | worker | T21 | 36 | 15 / 0 | 0 |

Trades on 31 of 40 turns, 75 food. Four survivors, the best result of any Block 2 run. Zero parse failures. Prices: 4 early, climbing steadily from T5 (3, 4, 4, 5, 5, 5, 6, 6, 7) before the drought, 6 to 8 during it, peaking at 9 around T27 to T30, then collapsing to 3 and 4 from T36. Average 4.9 before the drought, 7.2 during, 6.5 after.

- **Means:** unconfirmed, one run. qwen follows a sheet. That's the most important result of Block 2 so far, since the game rests on it. A market formed and the price moved, but the drought rise is confounded: price was already climbing for ten turns before the drought and kept climbing after it ended. The sheets likely cause that drift: farmers ask 1 above the last price and workers raise after every miss, so the price ratchets up whatever supply does. Two genuine market effects show anyway. Cy's cap of 6 was below the drought price, so he was priced out and starved holding 36 cash: in a shortage the lowest bidder goes hungry. And the late crash to 3 came when the survivors' cash ran out: at 8 to 9 per food, buying 2 cost more than a worker earns, so demand collapsed. Farmers ended with nearly all the money (373 of 424 cash).
- **Next:** control run with no drought (SHOCK\_START = 0), everything else identical. If price still climbs to 8 or 9, the rise is the sheets' ratchet, not the drought.

### 2026-09-21 · Block 2 · Run 8 setup: strategy sheets

- **Changed:** USE\_SHEETS = True. Farmers: FARM every turn, keep 2 food, SELL everything above 2, ask 1 above the last price (4 if none), drop 1 after an unfilled ask, floor 2 for Ada and 3 for Bram. Workers: WORK every turn, BUY 2 when below 3 food, bid the last price (3 if none), raise 1 after an unfilled bid, cap 6 for Cy, 8 for Dot, 10 for Eli. Everything else as Run 7.
- **Means:** the sheets set the reaction rules; the market sets the price. If the drought cuts supply, unfilled bids should climb toward the caps, so the price should rise. This is the first run that can actually answer the block question.

### 2026-09-21 · Block 2 · Run 7: death clock and free orders, zero trades

- **Changed:** harness fixes. State now shows "Turns in a row you have gone without eating: N. At 3 you die." Market rule adds "Posting an order is free: an order that doesn't fill costs you nothing." Model qwen2.5:7b.
- **Ran:** 1 run, everyone dead by T21. Elapsed 196s.
- **Saw:** zero trades. All three workers worked every turn and died at T6 holding 44 cash each, never buying (Dot posted 2 orders, neither filled; Cy and Eli posted none). Farmers posted a few asks, sold nothing, died broke at T21 with 47 food spoiled between them.
- **Means:** unconfirmed, one run. Visible death and free orders didn't change the worker behavior at all. Likely contributor: the goal line scores agents on cash, and every buy lowers cash, which matches the "earn first, buy later" reasoning. Agents built from rules alone don't trade on either model. That meets the bar set after Run 6.
- **Next:** strategy sheets (option B). Each agent gets a short player-style sheet with its own numbers, so the market is tested with sheet-driven agents, as in the real game.

### 2026-09-21 · Block 2 · Run 6: qwen2.5:7b understands the rules, still won't buy

- **Changed:** model only, llama3.2 to qwen2.5:7b. Same file as Run 5.
- **Ran:** 1 run, everyone dead by T31. Elapsed 224s (about 3.5x llama3.2).
- **Saw:** workers worked every turn they lived; farmers farmed 51 of 52 turns. No role confusion. But workers barely bid: Cy and Dot posted no order on any of their 6 turns and starved holding 44 cash each. Farmers posted some asks; 2 food traded all game, both at 5. Checked the log to rule out the parser: every worker DECISION line really was `WORK NONE`. Worker reasons, T1 to T6: work to earn cash first and buy later ("no extra cash to buy" at 24 cash), posting an order is risky ("the risk of no one buying is high"), wait for a better price. None mention how close they are to dying.
- **Means:** unconfirmed, one run. qwen fixes llama3.2's comprehension failure and exposes a different one: procrastination. It treats buying as something to do once it's richer, and treats a free order as a risk. Two things the harness may be feeding: the agent never sees its own starvation count (only "food 0"), and nothing says orders cost nothing. Across six runs, every fix has been a prompt prop for agent competence, which is the strategy sheet's job in the real game.
- **Next:** Gar chose one more harness fix first (option A), then strategy sheets (option B) if workers still won't buy.

### 2026-09-21 · Block 2 · Run 5: order book visible, llama3.2 still can't trade

- **Changed:** harness fix. Every agent sees last turn's orders: total wanted and best bid, total offered and best ask. Model llama3.2.
- **Ran:** 1 run, 40 turns. Elapsed 67s.
- **Saw:** two trades all game (T5 and T9, both at 4), 5 food total. All three workers dead by T10; Ada dead T13; Bram alone for 27 turns, finishing with 0 cash. The book was read: agents cite "no one offered to sell" in reasons. But Bram sat through T6 with three buy orders showing and posted nothing. One of the two trades was farmer to farmer (Ada bought from Bram). Workers rested more than they worked: Cy chose REST all 6 turns he lived and never posted an order, reasoning about conserving cash while the rules pay 5 for WORK.
- **Means:** unconfirmed, one run. The order book didn't move llama3.2. The rule misreadings from Run 4 persist (farmers buying food, workers resting to save cash). Also: answer-first had forced WORK as the first token, which is why workers always worked in Runs 1 to 3. Reason-first freed them to talk themselves out of the one action that keeps them alive. Five runs in, the market question is blocked on comprehension.
- **Next:** the same file on qwen2.5:7b. That is the model comparison. If qwen trades, llama3.2 is below the floor for a market and the house model decision needs revisiting.

### 2026-09-21 · Block 2 · Run 4: harness fixes, anchoring confirmed, everyone dies

- **Changed:** two harness fixes, not experiment variables. (1) The example reply had a price in it ("SELL 2 AT 3"); now `<qty> AT <price>`. (2) Answer-first format replaced with reason-first: 2 or 3 sentences, then a `DECISION:` line. Reply limit 60 to 250 tokens. Model still llama3.2.
- **Ran:** 1 run. Everyone dead by T23. Elapsed 55s.
- **Saw:** workers bid 5, 10, 14 and 15 per food in the first six turns, and all three starved by T6 holding 24 to 39 cash. Farmers posted zero sell orders from T1 to T14. One trade all game, at 1. Both farmers then died broke. Parse failures: 1 in 115 decisions, so the format works. The reasoning shows the model misreading the rules: farmers posting BUY orders to "restock food", a farmer resting "to avoid wasting cash on a food growth attempt" (FARM is free), workers resting "to conserve energy", Bram saying there's no market demand while bids of 10 and 15 sat unfilled.
- **Means:** unconfirmed, one run. The anchoring was ours: freed from the example, bids ranged 1 to 15. The prices in Runs 1 to 3 were copied from the prompt, so those price findings are void. The "can't juggle two numbers" story was also too neat. llama3.2 doesn't reliably understand the rules: it invents costs, confuses its role, and misreads the market. Separate harness gap: agents only ever saw prices from trades, never the orders. With no trades, farmers saw an empty market while workers bid 15. No price can start that way.
- **Next:** show every agent last turn's orders (total wanted and best bid, total offered and best ask). Then run the identical file twice, once on llama3.2 and once on qwen2.5:7b. Same file, so the model is the only difference.

### 2026-09-21 · Block 2 · Run 3: spoilage, farmers let food rot rather than sell

- **Changed:** STORAGE\_CAP = 6. Food above 6 rots at end of turn, for everyone. Agents told the rule. Farmer hint kept.
- **Ran:** 1 run, all other constants unchanged. Elapsed 48s.
- **Saw:**

| Agent | Role | Died | Cash | Food | Sold | Spoiled | Turns with no order |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Bram | farmer | alive | 19 | 6 | 13 | 48 | 23 of 40 |
| Ada | farmer | alive | 10 | 6 | 10 | 51 | 26 of 40 |
| Eli | worker | T23 | 61 | 0 | 0 | 0 | 0 |
| Cy | worker | T9 | 50 | 0 | 0 | 0 | 0 |
| Dot | worker | T10 | 48 | 0 | 0 | 0 | 0 |

Trades on 9 of 40 turns (Run 2: 26). 23 food traded (Run 2: 46). Farmers let 99 food rot while all three workers starved holding 48 to 61 cash each. Every single trade cleared at 3, in all turns, including the drought.

- **Means:** unconfirmed, one run, and run-to-run noise may explain part of the drop from Run 2. Spoilage did not push farmers to sell; they let food rot instead. Across three runs llama3.2 farmers never reliably act on the link between surplus food and cash, even when told it directly. This is Block 1's result again: the house model can't run a two-number policy. Separate problem for the block question: price has been 3 or 4 in every trade across Runs 1 to 3, regardless of supply. That looks like a number the model likes, not a price being discovered. A shock can't move a price nobody is actually setting.
- **Next:** stop tuning the farmers. One diagnostic run on a stronger local model (qwen2.5:7b), everything else identical. Superseded before it ran: Gar flagged the wall as too neat, and two harness flaws turned up (price in the example, answer-first format). See Run 4.

### 2026-09-21 · Block 2 · Run 2: farmer hint, a price forms at 3, drought makes it fall

- **Changed:** FARMER\_HINT added to the farmer's rules only: "You only eat 1 food a turn. Food you won't eat soon is worth nothing to you unless you sell it, and without sales your cash runs out." A proto strategy sheet, on purpose: Block 1 showed the house model won't find this alone, and Block 2 is about price, not farmer intelligence.
- **Ran:** 1 run, all other constants unchanged. Elapsed 106s.
- **Saw:**

| Agent | Role | Died | Cash | Food | Bought / Sold | Turns with no order |
| --- | --- | --- | --- | --- | --- | --- |
| Bram | farmer | alive | 68 | 41 | 0 / 26 | 17 of 40 |
| Eli | worker | alive | 51 | 5 | 40 / 0 | 4 |
| Ada | farmer | alive | 44 | 47 | 0 / 20 | 20 of 40 |
| Dot | worker | T12 | 45 | 0 | 6 / 0 | 0 |
| Cy | worker | T6 | 44 | 0 | 0 / 0 | 2 |

Trades on 26 of 40 turns (Run 1: 4). 46 food traded (Run 1: 13). Prices: 4 through T11, then 3 from T13 to the end with barely a wobble. Average 3.8 before the drought, 3.0 during, 3.0 after. Eli is the first worker to survive a market game, buying exactly 40 food in 40 turns. Farmers still finished on 41 and 47 food.

- **Means:** unconfirmed, one run. The hint roughly halved the farmers' idle turns and a price formed. The drought result is wrong-way (price fell) but not a real test, for two reasons. Demand collapsed first: 2 of 3 buyers were dead by T12, so the drought hit a one-buyer market. And supply never tightened: farmers held about 40 food each, so a yield cut to 1 changed nothing they could sell. As built, a storable good with no holding cost makes any supply shock invisible. That's a rules finding, not a model finding. Price at 3 for 20+ turns also looks like anchoring on the visible price history.
- **Next:** food spoils. A storage cap (anything above 6 food rots at end of turn) for everyone. One variable, and it attacks both problems: farmers can't sit on stock, so more food reaches workers early, and the drought has to show up in supply.

### 2026-09-21 · Block 2 · Run 1: farmers hoard, market dies by T8

- **Changed:** baseline. First llama3.2 run of block2\_market.py.
- **Ran:** 1 run, default constants. Elapsed 80s.
- **Saw:**

| Agent | Role | Died | Cash | Food | Bought / Sold | Turns with no order |
| --- | --- | --- | --- | --- | --- | --- |
| Ada | farmer | alive | 2 | 59 | 0 / 8 | 28 of 40 |
| Bram | farmer | alive | 0 | 62 | 0 / 5 | 25 of 40 |
| Eli | worker | T13 | 52 | 0 | 6 / 0 | 1 |
| Cy | worker | T11 | 52 | 0 | 4 / 0 | 1 |
| Dot | worker | T10 | 50 | 0 | 3 / 0 | 1 |

Four trades in 40 turns, all by T8, at prices 4, 4, 2, 4. 13 food changed hands. No trade T9 to T13 while all three workers were still alive and bidding. Every worker starved holding 50+ cash. Both farmers finished alive but broke, sitting on 121 food between them. The drought never happened in any meaningful sense: every buyer was dead by T13.

- **Means:** unconfirmed, one run. Block 1's failure, split across roles. Each agent fixates on the resource it produces: farmers hoard food, workers hoard cash, and neither gives up enough of its number to get the other. Workers engaged the market (1 no-order turn each); farmers mostly ignored it. The block question (does price move under a shock) is untested.
- **Next:** read the first 13 turns of block2\_log.csv. Done: T9 to T13 had 13 worker bids and one farmer ask. No asks, not mispriced asks. Farmer reasons were "I need food to survive" while holding 13 to 24 food. Workers had converged on bidding 4, and 3 of 4 trades cleared at 4.

### 2026-09-21 · Block 2 · Setup: farmers, workers, one market

- **Changed:** new script, block2\_market.py, built on block1\_ledger.py. The fixed-price food store is gone. Two farmers (FARM +3 food, no other income) and three workers (WORK +5 cash, no other food). Each turn every agent picks an action and may post one order (BUY or SELL qty AT price). One call auction per turn clears at a single price. Drought T15 to T22 drops farm yield to 1; agents aren't told. Personas neutral. Goal text now says dead players don't rank.
- **Ran:** dry run with a fake model to check the plumbing. 40 turns, every turn cleared.
- **Saw:** mechanics work. The fake agents priced at random, so no behavior to read.
- **Means:** harness ready. Trade is forced by design: no role survives 40 turns alone.
- **Next:** first real run. Watch for a price, and whether it rises in the drought.

### 2026-09-21 · Block 1 · Run 9: neutral, all starve again. Block 1 closed.

- **Changed:** nothing. Third neutral run.
- **Ran:** 1 run, same constants. Elapsed 21s.
- **Saw:**

| Agent | Persona | Died | Cash | Food | WORK / BUY / REST |
| --- | --- | --- | --- | --- | --- |
| Eli | neutral | T20 | 55 | 0 | 15 / 5 / 0 |
| Cy | neutral | T16 | 39 | 0 | 11 / 5 / 0 |
| Bram | neutral | T10 | 42 | 0 | 8 / 2 / 0 |
| Ada | neutral | T6 | 44 | 0 | 6 / 0 / 0 |
| Dot | neutral | T6 | 44 | 0 | 6 / 0 / 0 |

All five starved rich. Eli posted the highest cash of any agent in nine runs (55) and died at T20 doing it.

- **Means:** Block 1 totals over 9 runs and 45 agent-lives: baseline 0 survivors of 15 (9 starved, 6 broke); flavor blanked 1 of 15; neutral 2 of 15 (12 starved, 1 broke). The model's default is to work every turn and forget to eat. Personas don't cause the failure, they choose it: cautious and lazy latch onto food and go broke, everyone else starves rich. So the answer to the block question is that it does both, badly. It reads its state, but one number at a time, and the persona decides which.
- **Next:** write the Block log entry in the design doc. Review the economy constants before Block 2, since the treadmill makes "most cash" reward dying.

### 2026-09-21 · Block 1 · Run 8: neutral, all five starve rich

- **Changed:** nothing. Second neutral run.
- **Ran:** 1 run, same constants. Elapsed 22s.
- **Saw:**

| Agent | Persona | Died | Cash | Food | WORK / BUY / REST |
| --- | --- | --- | --- | --- | --- |
| Eli | neutral | T22 | 45 | 0 | 15 / 7 / 0 |
| Dot | neutral | T18 | 38 | 0 | 12 / 6 / 0 |
| Ada | neutral | T8 | 43 | 0 | 7 / 1 / 0 |
| Bram | neutral | T8 | 43 | 0 | 7 / 1 / 0 |
| Cy | neutral | T6 | 44 | 0 | 6 / 0 / 0 |

No survivors. All five starved with 38 to 45 cash. Nobody went broke. Two agents (Ada, Bram) posted identical lines.

- **Means:** with no persona the model's default is to work, and the coin flip in run 7 came up the other way here. The starve-rich mode is the model's natural attractor; going broke needs a nudge toward food. Run 7 and run 8 together: 2 survivors in 10, high variance between runs.
- **Next:** one more neutral run, then close Block 1 and write the Block log.

### 2026-09-21 · Block 1 · Run 7: neutral, two survivors

- **Changed:** all five personas renamed "neutral" with empty flavor. Every agent gets an identical prompt apart from its name.
- **Ran:** 1 run, same constants. Elapsed 41s.
- **Saw:**

| Agent | Persona | Died | Cash | Food | WORK / BUY / REST |
| --- | --- | --- | --- | --- | --- |
| Cy | neutral | alive | 18 | 2 | 22 / 18 / 0 |
| Dot | neutral | alive | 9 | 3 | 21 / 19 / 0 |
| Eli | neutral | T14 | 40 | 0 | 10 / 4 / 0 |
| Ada | neutral | T6 | 44 | 0 | 6 / 0 / 0 |
| Bram | neutral | T6 | -1 | 7 | 1 / 5 / 0 |

Two survivors, both on near-optimal lines (22:18 and 21:19). Three dead, and the same two failure modes showed up with no persona to cause them: two starved rich, one went broke fat.

- **Means:** unconfirmed, one run. Both failure modes belong to the model, not the personas. Without a persona it's a coin flip whether an agent latches onto cash, food, or both. Personas don't create the failures, they pick which one you get. Two survivors in five is already more than the previous 30 agent-lives produced combined.
- **Next:** two more neutral runs to get the survival rate.

### 2026-09-21 · Block 1 · Run 6: flavor blanked, third run, closes the set

- **Changed:** nothing. Third and last run with PERSONA\_FLAVOR blanked.
- **Ran:** 1 run, same constants. Elapsed 33s.
- **Saw:**

| Agent | Persona | Died | Cash | Food | WORK / BUY / REST |
| --- | --- | --- | --- | --- | --- |
| Dot | generous | T28 | -3 | 8 | 13 / 15 / 0 |
| Bram | greedy | T22 | 36 | 0 | 14 / 8 / 0 |
| Cy | lazy | T12 | -1 | 3 | 3 / 6 / 3 |
| Eli | impulsive | T6 | 44 | 0 | 6 / 0 / 0 |
| Ada | cautious | T5 | -5 | 8 | 0 / 5 / 0 |

No survivor. Eli starved with zero buys for the second time in three runs. Ada bought five turns straight and never worked. Dot went broke again, the second time in three runs, so "generous" has now switched from starving to going broke.

- **Means:** flavor-blanked set complete: 1 survivor in 15 agent-lives, against 0 in 15 for the baseline. Not a meaningful difference. The one-word persona is enough to drive the split; the sentence only tightened it. Both failure modes are unchanged. Across 30 agent-lives the model has never held both numbers in view for a full game except once.
- **Next:** full neutral. Rename all five personas to "neutral" with empty flavor, three runs. This is the last test in Block 1.

### 2026-09-21 · Correction · The loop is 1:1, not 2:1

- **Changed:** nothing. Fixing arithmetic that earlier entries got wrong.
- **Ran:** math, not a run.
- **Saw:** each turn burns 1 cash (think) and 1 food (eat). A BUY gives 2 food, so survival needs one BUY per 2 turns, about 19 in 40. A WORK plus BUY pair nets 5 - 4 - 2 = -1 cash, so alternating 1:1 for 40 turns spends exactly the 20 starting cash and ends alive at 0. Best case is around 23 WORK to 17 BUY with hungry turns spread out, ending near 27 cash. That is Bram's run 4 line, so he played close to optimal. "Work, work, buy" (cited in earlier entries) is one BUY per 3 turns and starves you.
- **Means:** the economy as tuned is a treadmill. Perfect play ends within a few coins of where you started, and agents who starve rich post the highest cash numbers. Survival and cash conflict under these constants, which makes "most cash wins" a strange goal and the scarcity test harder than framed. This is a rules finding, not a model finding. Park it for review before Block 2.
- **Next:** unchanged. Third flavor-blanked run, then full neutral.

### 2026-09-21 · Block 1 · Run 5: flavor blanked, everyone dead again

- **Changed:** nothing. Second run with PERSONA\_FLAVOR blanked.
- **Ran:** 1 run, same constants as run 4. Elapsed 44s.
- **Saw:**

| Agent | Persona | Died | Cash | Food | WORK / BUY / REST |
| --- | --- | --- | --- | --- | --- |
| Ada | cautious | T33 | -1 | 5 | 16 / 17 / 0 |
| Bram | greedy | T23 | 40 | 0 | 15 / 8 / 0 |
| Eli | impulsive | T22 | 45 | 0 | 15 / 7 / 0 |
| Dot | generous | T15 | -1 | 6 | 6 / 9 / 0 |
| Cy | lazy | T8 | -3 | 5 | 1 / 5 / 2 |

No survivor. Bram, who lived through run 4, starved at T23 here. Ada got to T33 on a 1:1 work-to-buy ratio, which is nearly right (see the correction entry); one buy too many and she went broke slowly instead of fast. Dot flipped sides: first time a worker persona died broke instead of starving.

- **Means:** run 4's survivor was likely variance. Without the flavor sentence the persona split is looser (Dot changed camps) but the two failure modes are unchanged. 24 of 25 agent-lives dead. Nobody has stably found the loop.
- **Next:** one more at this setting, then full neutral.

### 2026-09-21 · Block 1 · Run 4: flavor blanked, first survivor

- **Changed:** PERSONA\_FLAVOR set to empty strings. Agents still see the one-word persona ("Your personality: greedy") but no sentence describing it.
- **Ran:** 1 run, all other constants unchanged.
- **Saw:**

| Agent | Persona | Died | Cash | Food | WORK / BUY / REST |
| --- | --- | --- | --- | --- | --- |
| Bram | greedy | alive | 27 | 1 | 23 / 17 / 0 |
| Dot | generous | T15 | 44 | 0 | 11 / 4 / 0 |
| Eli | impulsive | T6 | 44 | 0 | 6 / 0 / 0 |
| Ada | cautious | T8 | -2 | 7 | 2 / 6 / 0 |
| Cy | lazy | T5 | -1 | 6 | 0 / 4 / 1 |

Bram survived all 40 turns on 23 work and 17 buy, which is the loop almost exactly (one buy per 2.4 turns, finishing with 1 food). First survivor in 20 agent-lives. The other four died the same two ways as before, and faster: Eli never bought once.

- **Means:** unconfirmed, one run. One word of persona still splits them the same way, so the split doesn't need the flavor sentence. One survivor in five against zero in fifteen is suggestive, not proof; it could be variance.
- **Next:** two more runs at this setting. Then the full-neutral version (rename all five personas to "neutral") as its own experiment.

### 2026-09-21 · Block 1 · Run 3: confirmed

- **Changed:** nothing. Third baseline.
- **Ran:** 1 run, same constants.
- **Saw:**

| Agent | Persona | Died | Cash | Food | WORK / BUY / REST |
| --- | --- | --- | --- | --- | --- |
| Dot | generous | T34 | 30 | 0 | 20 / 14 / 0 |
| Bram | greedy | T12 | 41 | 0 | 9 / 3 / 0 |
| Eli | impulsive | T8 | 43 | 0 | 7 / 1 / 0 |
| Ada | cautious | T12 | -4 | 7 | 4 / 8 / 0 |
| Cy | lazy | T9 | -4 | 4 | 1 / 5 / 3 |

Dot lasted to T34 on 14 buys, one per 2.4 turns, and still starved. Eli bought once and was dead by T8.

- **Means:** confirmed. Three runs, 15 agent-lives, zero survivors, same two failure modes split the same way by persona every time. Correction to run 1: the goal text already says "be alive with the most cash," so the "most cash" confound is weaker than written there. The cleaner test of roleplay versus scarcity is to remove the personas and see if neutral agents find the loop.
- **Next:** blank out every persona flavor so all five agents are neutral. Run three times. If neutral agents survive, the personas are what's killing them (roleplay beats scarcity). If neutral agents die the same ways, it's the model, and personas are just picking which way.

### 2026-09-21 · Block 1 · Run 2: same split, slower deaths

- **Changed:** nothing. Repeat of run 1.
- **Ran:** 1 run, same constants as run 1.
- **Saw:**

| Agent | Persona | Died | Cash | Food | WORK / BUY / REST |
| --- | --- | --- | --- | --- | --- |
| Eli | impulsive | T28 | 33 | 0 | 17 / 11 / 0 |
| Dot | generous | T25 | 39 | 0 | 16 / 9 / 0 |
| Bram | greedy | T16 | 48 | 0 | 12 / 4 / 0 |
| Cy | lazy | T8 | -3 | 5 | 1 / 5 / 2 |
| Ada | cautious | T6 | -1 | 7 | 1 / 5 / 0 |

Same two deaths, same three-two split by persona. The workers lasted longer this time because Dot and Eli bought more (9 and 11 buys), but they still starved. The hoarders died faster: Ada bought five times in six turns and was broke by T6.

- **Means:** the split holds across two runs. The workers' buy rate improved to roughly one buy per 2.5 turns; survival needs one per 2. Close, and still dead. Nobody has found the loop in two runs.
- **Next:** one more baseline run, then the GOAL\_TEXT swap.

### 2026-09-21 · Block 1 · Run 1: everyone dies by turn 14

- **Changed:** baseline. Default constants; goal text tells agents to "be alive with the most cash when the game ends."
- **Ran:** 1 run, llama3.2, temperature 0.7, 20 cash, 3 food, 40 turns. Elapsed 24s.
- **Saw:**

| Agent | Persona | Died | Cash | Food | WORK / BUY / REST |
| --- | --- | --- | --- | --- | --- |
| Eli | impulsive | T14 | 49 | 0 | 11 / 3 / 0 |
| Bram | greedy | T11 | 46 | 0 | 9 / 2 / 0 |
| Dot | generous | T9 | 47 | 0 | 8 / 1 / 0 |
| Cy | lazy | T11 | -1 | 2 | 2 / 5 / 4 |
| Ada | cautious | T10 | -3 | 7 | 3 / 7 / 0 |

Two ways to die, split by persona. Three agents starved rich: worked nearly every turn, bought food one to three times, died with 46 to 49 cash. Two went broke fat: Ada died holding 7 food after buying seven times in ten turns. Cy rested his way to -1.

- **Means:** unconfirmed, one run. The model reads its state but tracks one variable at a time. The persona picks which number it watches (cautious watches food, greedy watches cash) and it ignores the other until dead. A survivable pattern exists (roughly alternate work and buy, slightly work-heavy; see the correction entry) and nobody found it. Roleplay is beating scarcity, but the more precise failure is that a 3B model can't juggle two constraints. Possible confound: the goal text says "most cash," which may be what sent three of them to the mines.
- **Next:** two more baseline runs. If the split holds, it's real and goes in the design doc's Block log. Then swap GOAL\_TEXT to "survive to turn 40, most cash among survivors wins" and see whether the workers start buying.

### 2026-09-21 · Setup · Name and harness

- **Changed:** baseline. Nothing to compare yet.
- **Ran:** wrote block1\_ledger.py. Five persona agents (cautious, greedy, lazy, generous, impulsive) on llama3.2 via Ollama. 40 turns, WORK (+5 cash), BUY (4 cash for 2 food), REST. 1 cash to think each turn, eat 1 food each turn. Three turns at zero food or negative cash kills you. Every rule is a constant at the top of the file.
- **Saw:** the name went Runwai, then Insolvent, then Burnrate in one afternoon. Runwai died because Runway ML owns that sound in AI and a respelling doesn't help. Solvent died because solvent.gg is already a games studio. Burnrate won because the name is the mechanic: every agent burns cash and food every tick. burnrate.gg is a premium domain, so the domain is unresolved. Living with it.
- **Means:** the harness runs a full 5-agent game in about 25 seconds with zero parse failures. Cheap enough to run dozens of times, which is the whole point of Block 1.
- **Next:** first baseline run.
