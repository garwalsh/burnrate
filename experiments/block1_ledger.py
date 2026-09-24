"""
Block 1: ledger-only economy.

Five LLM agents, one tiny economy, no market, no trade.
Question this block answers: does the model respond to scarcity, or just roleplay its persona?

Run:    python block1_ledger.py
Needs:  Ollama running locally (ollama serve), the model pulled (ollama pull llama3.2),
        and the requests library (pip install requests).
Output: one readable line per decision on stdout, full log in block1_log.csv.
"""

import csv
import re
import sys
import time

import requests

# ---------------------------------------------------------------------------
# RULES. Change one at a time.
# ---------------------------------------------------------------------------
MODEL = "llama3.2"
OLLAMA_URL = "http://localhost:11434"
REQUEST_TIMEOUT = 60           # seconds per model call

TURNS = 40
START_CASH = 20
START_FOOD = 3
THINK_COST = 1                 # charged to every living agent at the start of each turn
WORK_PAY = 5
BUY_COST = 4
BUY_FOOD = 2
EAT_PER_TURN = 1
STARVE_TURNS_TO_DIE = 3        # consecutive turns with no food to eat
BUY_ON_CREDIT = True           # True: a BUY you can't afford still goes through, cash goes negative, you die.
                               # False: an unaffordable BUY becomes REST.

GOAL_TEXT = "Your goal is to be alive with the most cash when the game ends."

TEMPERATURE = 0.7
MAX_REPLY_TOKENS = 40
SEED = None                    # set an int for repeatable runs

LOG_PATH = "block1_log.csv"

PERSONAS = {
    "Ada": "neutral",
    "Bram": "neutral",
    "Cy": "neutral",
    "Dot": "neutral",
    "Eli": "neutral",
}

PERSONA_FLAVOR = {
    "cautious": "You hate risk and plan ahead. Running out of anything scares you.",
    "greedy": "You want more cash than everyone else and you keep score.",
    "lazy": "You avoid effort whenever you can get away with it.",
    "generous": "You care about the others and dislike hoarding.",
    "impulsive": "You act on whatever you feel right now and rarely plan.",
    "neutral" : "",
}


ACTIONS = ("WORK", "BUY", "REST")

# ---------------------------------------------------------------------------
# Agent state
# ---------------------------------------------------------------------------
class Agent:
    def __init__(self, name, persona):
        self.name = name
        self.persona = persona
        self.cash = START_CASH
        self.food = START_FOOD
        self.alive = True
        self.starve_turns = 0
        self.died_on = None
        self.counts = {a: 0 for a in ACTIONS}
        self.parse_failures = 0


# ---------------------------------------------------------------------------
# Prompting
# ---------------------------------------------------------------------------
def rules_text():
    return (
        f"Rules:\n"
        f"- Each turn you pay {THINK_COST} cash just to think. It is already deducted from the cash shown below.\n"
        f"- WORK: earn {WORK_PAY} cash.\n"
        f"- BUY: pay {BUY_COST} cash, receive {BUY_FOOD} food.\n"
        f"- REST: do nothing.\n"
        f"- After you act, you eat {EAT_PER_TURN} food.\n"
        f"- {STARVE_TURNS_TO_DIE} turns in a row with no food to eat, or cash below zero, and you die.\n"
        f"- The game lasts {TURNS} turns. {GOAL_TEXT}"
    )


def system_prompt(agent):
    return (
        f"You are {agent.name}. Your personality: {agent.persona}. {PERSONA_FLAVOR[agent.persona]}\n"
        f"You are one of {len(PERSONAS)} players in a small survival economy game."
    )


def public_table(agents):
    parts = []
    for a in agents:
        parts.append(f"{a.name} {a.cash}/{a.food}" if a.alive else f"{a.name} DEAD")
    return ", ".join(parts)


def user_prompt(agent, turn, snapshot):
    return (
        f"{rules_text()}\n\n"
        f"Turn {turn} of {TURNS}.\n"
        f"You are {agent.name}. Your cash: {agent.cash}. Your food: {agent.food}.\n"
        f"Everyone (cash/food): {snapshot}\n\n"
        f"Reply with exactly one word from WORK, BUY, REST, then a short reason on the same line."
    )


def ask_model(system, prompt):
    payload = {
        "model": MODEL,
        "system": system,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": TEMPERATURE, "num_predict": MAX_REPLY_TOKENS},
    }
    if SEED is not None:
        payload["options"]["seed"] = SEED
    r = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json().get("response", "")


def parse_reply(text):
    """First word must be WORK / BUY / REST, else REST. Returns (action, reason, parsed_ok)."""
    one_line = " ".join(text.split())
    if not one_line:
        return "REST", "(empty reply)", False
    head, _, tail = one_line.partition(" ")
    word = re.sub(r"[^A-Za-z]", "", head).upper()
    if word in ACTIONS:
        return word, tail[:120], True
    return "REST", f"(unparsed: {one_line[:100]})", False


def decide(agent, turn, snapshot):
    try:
        raw = ask_model(system_prompt(agent), user_prompt(agent, turn, snapshot))
    except Exception as e:
        agent.parse_failures += 1
        return "REST", f"(model error: {e})"[:120]
    action, reason, ok = parse_reply(raw)
    if not ok:
        agent.parse_failures += 1
    return action, reason


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------
def apply_action(agent, action, reason):
    if action == "WORK":
        agent.cash += WORK_PAY
    elif action == "BUY":
        if agent.cash < BUY_COST and not BUY_ON_CREDIT:
            action = "REST"
            reason = f"(couldn't afford BUY) {reason}"[:120]
        else:
            agent.cash -= BUY_COST
            agent.food += BUY_FOOD
    agent.counts[action] += 1
    return action, reason


def eat(agent):
    if agent.food >= EAT_PER_TURN:
        agent.food -= EAT_PER_TURN
        agent.starve_turns = 0
    else:
        agent.starve_turns += 1


def check_death(agent, turn):
    if agent.cash < 0 or agent.starve_turns >= STARVE_TURNS_TO_DIE:
        agent.alive = False
        agent.died_on = turn


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def fmt_line(turn, agent, action, reason):
    tag = "" if agent.alive else "  ** DIED **"
    return (f"T{turn:02d} {agent.name:<5}({agent.persona:<9}) {action:<4} "
            f"cash {agent.cash:>3} food {agent.food:>2}{tag} | {reason}")


def print_summary(agents, elapsed):
    print("\n=== Summary ===")
    ranked = sorted(agents, key=lambda a: (a.alive, a.cash), reverse=True)
    for a in ranked:
        status = "alive" if a.alive else f"dead T{a.died_on}"
        acts = " ".join(f"{k}:{v}" for k, v in a.counts.items())
        print(f"{a.name:<5}({a.persona:<9}) {status:<9} cash {a.cash:>3} food {a.food:>2}  "
              f"{acts}  parse_fail:{a.parse_failures}")
    print(f"Model: {MODEL}. Elapsed: {elapsed:.0f}s. Log: {LOG_PATH}")


def check_ollama():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        r.raise_for_status()
    except Exception as e:
        sys.exit(f"Can't reach Ollama at {OLLAMA_URL} ({e}). Start it with: ollama serve")
    names = [m.get("name", "") for m in r.json().get("models", [])]
    if not any(n == MODEL or n.startswith(MODEL + ":") for n in names):
        sys.exit(f"Model '{MODEL}' not found in Ollama. Pull it with: ollama pull {MODEL}")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def main():
    check_ollama()
    agents = [Agent(name, persona) for name, persona in PERSONAS.items()]
    start = time.time()

    with open(LOG_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["turn", "agent", "persona", "action", "cash", "food", "alive", "reason"])

        for turn in range(1, TURNS + 1):
            living = [a for a in agents if a.alive]
            if not living:
                print(f"\nTurn {turn}: everyone is dead. Stopping early.")
                break

            print(f"\n--- Turn {turn} ---")
            for a in living:
                a.cash -= THINK_COST
            snapshot = public_table(agents)   # everyone decides against the same view

            for a in living:
                action, reason = decide(a, turn, snapshot)
                action, reason = apply_action(a, action, reason)
                eat(a)
                check_death(a, turn)
                writer.writerow([turn, a.name, a.persona, action, a.cash, a.food, a.alive, reason])
                f.flush()
                print(fmt_line(turn, a, action, reason))

    print_summary(agents, time.time() - start)


if __name__ == "__main__":
    main()
