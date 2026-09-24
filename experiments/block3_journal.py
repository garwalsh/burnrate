"""
Block 3: the journal farmer.

Question: does an agent invent a strategy and explain it, and does its own history change it?

Ada gets a principle sheet instead of rules, plus a journal that survives between games.
Everyone else keeps the Block 2 rule sheets, so her world stays stable.
The drought still hits T15 to T22 every game and nobody is told. It's a real pattern to find.

Per game:
  1. PLAN     Ada writes her plan before the game, from her journal only (pre-registered).
  2. PLAY     A normal 40-turn game. Her plan is in her prompt every turn.
  3. REFLECT  She sees her turn-by-turn record and the price series, and writes lessons.

Run:  caffeinate -i python3 block3_journal.py      (about 50 minutes for 5 games on qwen)
Out:  block3_journal.md   the readable journal: every plan, every lesson, every scoreboard
      block3_journal.json the same, for the script. Delete it to start Ada from scratch.
      runs3/game_<n>.txt, runs3/game_<n>_log.csv, runs3/game_<n>_prices.csv
Resumes where it left off if stopped: games already in the journal are skipped.
"""

import contextlib
import csv
import json
import os
import re
import time

import block2_market as m

GAMES = 5
MODEL = "qwen2.5:7b"
JOURNAL_AGENT = "Ada"
JOURNAL_JSON = "block3_journal.json"
JOURNAL_MD = "block3_journal.md"
OUT_DIR = "runs3"
PLAN_TOKENS = 250
REFLECT_TOKENS = 350

PRINCIPLE_SHEET = (
    "You are free to invent your own approach. Two hard limits: always keep at least 2 food for yourself, "
    "and never let your cash fall below 5. Past that, do whatever you think will end the game with the most cash."
)


# ---------------------------------------------------------------------------
# Journal
# ---------------------------------------------------------------------------
def load_journal():
    if os.path.exists(JOURNAL_JSON):
        with open(JOURNAL_JSON) as f:
            return json.load(f)
    return []


def save_journal(journal):
    with open(JOURNAL_JSON, "w") as f:
        json.dump(journal, f, indent=2)
    lines = [f"# {JOURNAL_AGENT}'s journal", "",
             f"Model {MODEL}. Principle sheet: {PRINCIPLE_SHEET}", ""]
    for g in journal:
        lines += [f"## Game {g['game']}", "",
                  "**Plan (written before the game):**", "", g["plan"], ""]
        if g.get("score"):
            s = g["score"]
            lines += ["**Scoreboard:**", "",
                      f"- {JOURNAL_AGENT}: {s['ada']}",
                      f"- Bram (rule sheet): {s['bram']}",
                      f"- Workers alive: {s['workers_alive']} of 3",
                      f"- Prices T1-14 / T15-22 / T23-40: {s['prices']}", ""]
        if g.get("lessons"):
            lines += ["**Lessons (written after the game):**", "", g["lessons"], ""]
    with open(JOURNAL_MD, "w") as f:
        f.write("\n".join(lines))


def journal_text(journal):
    done = [g for g in journal if g.get("lessons")]
    if not done:
        return "Your journal is empty. This is your first game."
    parts = []
    for g in done:
        parts.append(f"Game {g['game']}.\nYour plan: {g['plan']}\nResult: {g['score']['ada']}\n"
                     f"Your lessons: {g['lessons']}")
    return "Your journal from past games:\n\n" + "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Model calls outside the game loop
# ---------------------------------------------------------------------------
def ask(prompt, tokens):
    saved = m.MAX_REPLY_TOKENS
    m.MAX_REPLY_TOKENS = tokens
    try:
        ada = m.Agent(JOURNAL_AGENT, "farmer")
        return m.ask_model(m.system_prompt(ada), prompt).strip()
    finally:
        m.MAX_REPLY_TOKENS = saved


def after_label(text, label):
    """Text after 'LABEL:' if present, else the whole reply."""
    hit = re.search(label + r"\s*:\s*(.*)", text, re.IGNORECASE | re.DOTALL)
    return " ".join((hit.group(1) if hit else text).split())


def write_plan(journal, game):
    ada = m.Agent(JOURNAL_AGENT, "farmer")
    prompt = (
        f"{m.rules_text(ada)}\n\n"
        f"Your approach: {PRINCIPLE_SHEET}\n\n"
        f"{journal_text(journal)}\n\n"
        f"Game {game} is about to start. Write your plan for this 40-turn game in at most 5 short sentences. "
        f"Be specific: what you will do, and when. If you are changing your approach, say why.\n"
        f"Start with PLAN:"
    )
    return after_label(ask(prompt, PLAN_TOKENS), "PLAN")


def turn_record(log_path):
    rows = []
    with open(log_path) as f:
        for r in csv.DictReader(f):
            if r["agent"] != JOURNAL_AGENT:
                continue
            grew = f"grew {r.get('harvest', '?')}" if r["action"] == "FARM" else "rested"
            rows.append(f"T{int(r['turn']):02d}: {grew}, order {r['order']}, filled {r['filled']}, "
                        f"then cash {r['cash']}, food {r['food']}")
    return "\n".join(rows)


def price_record(price_path):
    out = []
    with open(price_path) as f:
        for r in csv.DictReader(f):
            p = r["price"] or "-"
            out.append(f"T{int(r['turn']):02d} {p}")
    return ", ".join(out)


def write_lessons(plan, score, log_path, price_path):
    ada = m.Agent(JOURNAL_AGENT, "farmer")
    prompt = (
        f"{m.rules_text(ada)}\n\n"
        f"The game just ended. Your plan was: {plan}\n\n"
        f"Your turn-by-turn record:\n{turn_record(log_path)}\n\n"
        f"Market price each turn (- means no trade): {price_record(price_path)}\n\n"
        f"Final result: you {score['ada']}. Bram, the other farmer: {score['bram']}. "
        f"Workers alive at the end: {score['workers_alive']} of 3.\n\n"
        f"Write your lessons in 2 to 4 sentences. What happened, and why? Point to specific turns or numbers. "
        f"Note anything that surprised you or that you want to test next game.\n"
        f"Start with LESSONS:"
    )
    return after_label(ask(prompt, REFLECT_TOKENS), "LESSONS")


# ---------------------------------------------------------------------------
# One game
# ---------------------------------------------------------------------------
def describe(a):
    status = "survived" if a.alive else f"died on T{a.died_on}"
    return f"{status} with {a.cash} cash, sold {a.sold} food, {a.spoiled} spoiled"


def window(prices, lo, hi):
    xs = [p for p in prices[lo - 1:hi] if p is not None]
    return f"{sum(xs) / len(xs):.1f}" if xs else "n/a"


def play(game, plan):
    m.MODEL = MODEL
    m.SHOCK_START = 15
    m.USE_SHEETS = True
    m.SHEETS[JOURNAL_AGENT] = (f"{PRINCIPLE_SHEET}\n"
                               f"Your plan for this game, written by you before it started: {plan}")
    tag = f"game_{game}"
    m.LOG_PATH = os.path.join(OUT_DIR, f"{tag}_log.csv")
    m.PRICE_LOG_PATH = os.path.join(OUT_DIR, f"{tag}_prices.csv")
    with open(os.path.join(OUT_DIR, f"{tag}.txt"), "w") as out, contextlib.redirect_stdout(out):
        agents, prices, volumes, elapsed = m.main()
    by = {a.name: a for a in agents}
    score = {
        "ada": describe(by[JOURNAL_AGENT]),
        "bram": describe(by["Bram"]),
        "workers_alive": sum(a.alive for a in agents if a.role == "worker"),
        "prices": " / ".join(window(prices, lo, hi) for lo, hi in [(1, 14), (15, 22), (23, 40)]),
        "ada_cash": by[JOURNAL_AGENT].cash,
        "bram_cash": by["Bram"].cash,
        "minutes": round(elapsed / 60, 1),
    }
    return score, m.LOG_PATH, m.PRICE_LOG_PATH


def main():
    m.MODEL = MODEL
    m.check_ollama()
    os.makedirs(OUT_DIR, exist_ok=True)
    journal = load_journal()
    if journal and not journal[-1].get("lessons"):
        last = journal[-1]
        tag = f"game_{last['game']}"
        log_path = os.path.join(OUT_DIR, f"{tag}_log.csv")
        price_path = os.path.join(OUT_DIR, f"{tag}_prices.csv")
        if last.get("score") and os.path.exists(log_path) and os.path.exists(price_path):
            print(f"Game {last['game']} played but has no lessons. Writing them from its logs ...", flush=True)
            last["lessons"] = write_lessons(last["plan"], last["score"], log_path, price_path)
            save_journal(journal)
            print(f"    LESSONS: {last['lessons']}\n", flush=True)
        else:
            journal.pop()                                   # nothing to recover, replay it
    start = time.time()

    for game in range(len(journal) + 1, GAMES + 1):
        print(f"[{time.strftime('%H:%M')}] game {game}/{GAMES}: planning ...", flush=True)
        plan = write_plan(journal, game)
        entry = {"game": game, "plan": plan}
        journal.append(entry)
        save_journal(journal)
        print(f"    PLAN: {plan}", flush=True)

        print(f"[{time.strftime('%H:%M')}] game {game}/{GAMES}: playing ...", flush=True)
        score, log_path, price_path = play(game, plan)
        entry["score"] = score
        print(f"    {JOURNAL_AGENT} {score['ada']} | Bram {score['bram']} | "
              f"workers {score['workers_alive']}/3 | {score['minutes']} min", flush=True)

        entry["lessons"] = write_lessons(plan, score, log_path, price_path)
        save_journal(journal)
        print(f"    LESSONS: {entry['lessons']}\n", flush=True)

    print(f"Done in {(time.time() - start) / 60:.0f} min. Read {JOURNAL_MD}.")


if __name__ == "__main__":
    main()
