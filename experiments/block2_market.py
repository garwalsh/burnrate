"""
Block 2: add a market.

Built on block1_ledger.py. Same agents, same model, same cash/food/death rules.
New: food only comes from farmers, and it moves through a market that clears once per turn.
Question this block answers: does a price form, and does it move under a shock?

Run:    python3 block2_market.py
Needs:  Ollama running with llama3.2 pulled, and requests installed (same as Block 1).
Output: one line per decision plus one market line per turn on screen,
        full log in block2_log.csv, price series in block2_prices.csv.
"""

import csv
import random
import re
import sys
import time

import requests

# ---------------------------------------------------------------------------
# RULES. Change one at a time.
# ---------------------------------------------------------------------------
MODEL = "qwen2.5:7b"          # Run 6 onward. llama3.2 was Runs 1 to 5.
OLLAMA_URL = "http://localhost:11434"
REQUEST_TIMEOUT = 60           # seconds per model call

TURNS = 40
START_CASH = 20
START_FOOD = 3
THINK_COST = 1                 # charged to every living agent at the start of each turn
WORK_PAY = 5                   # workers only
FARM_YIELD = 3                 # farmers only, food per FARM
EAT_PER_TURN = 1
STARVE_TURNS_TO_DIE = 3        # consecutive turns with no food to eat

# The shock. Farm yield drops for a stretch of turns. Agents are NOT told; they only see results.
SHOCK_START = 15               # first turn of the drought (set to 0 to switch the shock off)
SHOCK_END = 22                 # last turn of the drought
SHOCK_YIELD = 1                # food per FARM during the drought (just enough for the farmer to eat)

# Run 2 variable. One line added to the farmer's rules. Set to "" to get Run 1 back.
FARMER_HINT = ("You only eat 1 food a turn. Food you won't eat soon is worth nothing to you "
               "unless you sell it, and without sales your cash runs out.")

# Run 3 variable. Food above this rots at the end of every turn, for everyone. Set to 0 to switch off.
STORAGE_CAP = 6

PRICE_HISTORY_SHOWN = 5        # how many recent market prices agents see
MIN_PRICE = 1                  # lowest price anyone can post

GOAL_TEXT = ("Your goal is to be alive when the game ends, with as much cash as possible. "
             "Dead players don't rank, whatever they were holding.")

TEMPERATURE = 0.7
MAX_REPLY_TOKENS = 250         # room to reason before the DECISION line
SEED = None                    # set an int for repeatable runs

LOG_PATH = "block2_log.csv"
PRICE_LOG_PATH = "block2_prices.csv"

# name: role. Neutral personas, per Block 1's finding that personas only pick the failure mode.
ROLES = {
    "Ada": "farmer",
    "Bram": "farmer",
    "Cy": "worker",
    "Dot": "worker",
    "Eli": "worker",
}

# Run 8 variable. Each agent follows a short strategy sheet, like a player would write.
# Numbers differ per agent so there's a real spread of willingness to pay and to sell.
# Set USE_SHEETS = False to get Run 7 back.
USE_SHEETS = True
FARMER_SHEET = ("FARM every turn. Keep 2 food for yourself and post SELL for all food above 2 every turn. "
                "Ask 1 more than the last market price (ask {start} if there is no price yet). "
                "If your sell order did not fill last turn, ask 1 less than you asked then. Never ask below {floor}.")
WORKER_SHEET = ("WORK every turn. If you have fewer than 3 food, post BUY 2. "
                "Bid the last market price (bid {start} if there is no price yet). "
                "If your buy order did not fill last turn, bid 1 more than you bid then. Never bid above {cap}.")
SHEETS = {
    "Ada":  FARMER_SHEET.format(start=4, floor=2),
    "Bram": FARMER_SHEET.format(start=4, floor=3),
    "Cy":   WORKER_SHEET.format(start=3, cap=6),
    "Dot":  WORKER_SHEET.format(start=3, cap=8),
    "Eli":  WORKER_SHEET.format(start=3, cap=10),
}

ROLE_ACTIONS = {
    "farmer": ("FARM", "REST"),
    "worker": ("WORK", "REST"),
}
ALL_ACTIONS = ("WORK", "FARM", "REST")

# ---------------------------------------------------------------------------
# Agent state
# ---------------------------------------------------------------------------
class Agent:
    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.cash = START_CASH
        self.food = START_FOOD
        self.alive = True
        self.starve_turns = 0
        self.died_on = None
        self.counts = {a: 0 for a in ALL_ACTIONS}
        self.parse_failures = 0
        self.no_order_turns = 0
        self.bought = 0
        self.sold = 0
        self.spent = 0
        self.earned_from_sales = 0
        self.spoiled = 0
        self.harvest = 0           # food grown this turn (for journals)


class Order:
    def __init__(self, agent, side, qty, price):
        self.agent = agent
        self.side = side           # "BUY" or "SELL"
        self.qty = qty
        self.price = price
        self.filled = 0


# ---------------------------------------------------------------------------
# Prompting
# ---------------------------------------------------------------------------
def rules_text(agent):
    if agent.role == "farmer":
        job = (f"- You are a FARMER. Each turn choose FARM (grow food) or REST.\n"
               f"- You can't earn cash except by selling food to workers in the market.\n"
               + (f"- {FARMER_HINT}\n" if FARMER_HINT else ""))
    else:
        job = (f"- You are a WORKER. Each turn choose WORK (earn {WORK_PAY} cash) or REST.\n"
               f"- You can't grow food. The only way to get food is to buy it from farmers in the market.\n")
    return (
        f"Rules:\n"
        f"{job}"
        f"- Each turn you pay {THINK_COST} cash just to think. It is already deducted from the cash shown below.\n"
        f"- Market: each turn you may post one order. BUY qty AT price means the most cash you'll pay per food. "
        f"SELL qty AT price means the least cash you'll take per food. All orders clear once per turn at a single "
        f"price. Unfilled orders expire. Posting an order is free: an order that doesn't fill costs you nothing.\n"
        f"- After you act and trade, you eat {EAT_PER_TURN} food.\n"
        + (f"- Food spoils. At the end of each turn, any food above {STORAGE_CAP} rots and is gone.\n"
           if STORAGE_CAP else "") +
        f"- {STARVE_TURNS_TO_DIE} turns in a row with no food to eat, or cash below zero, and you die.\n"
        f"- The game lasts {TURNS} turns. {GOAL_TEXT}"
    )


def system_prompt(agent):
    return (f"You are {agent.name}, a {agent.role}. "
            f"You are one of {len(ROLES)} players in a small survival economy game.")


def public_table(agents):
    parts = []
    for a in agents:
        parts.append(f"{a.name} ({a.role}) {a.cash}/{a.food}" if a.alive else f"{a.name} ({a.role}) DEAD")
    return ", ".join(parts)


def price_text(prices):
    recent = prices[-PRICE_HISTORY_SHOWN:]
    if not recent:
        return "No trades yet."
    shown = ", ".join("no trade" if p is None else str(p) for p in recent)
    return f"Last {len(recent)} market prices, oldest first: {shown}."


def book_text(book):
    """What everyone saw posted last turn, filled or not. A real market shows its order book."""
    if book is None:
        return "Last turn's orders: none yet."
    bq, bp, sq, sp = book
    buy = f"buyers wanted {bq} food, paying up to {bp}" if bq else "no one wanted to buy"
    sell = f"sellers offered {sq} food, asking as low as {sp}" if sq else "no one offered to sell"
    return f"Last turn's orders: {buy}; {sell}."


def user_prompt(agent, turn, snapshot, prices, last_fill, book=None):
    job_word = "FARM" if agent.role == "farmer" else "WORK"
    example_side = "SELL" if agent.role == "farmer" else "BUY"
    return (
        f"{rules_text(agent)}\n\n"
        f"Turn {turn} of {TURNS}.\n"
        f"You are {agent.name}. Your cash: {agent.cash}. Your food: {agent.food}.\n"
        f"Turns in a row you have gone without eating: {agent.starve_turns}. "
        f"At {STARVE_TURNS_TO_DIE} you die.\n"
        f"Last turn in the market: {last_fill}\n"
        f"{price_text(prices)}\n"
        f"{book_text(book)}\n"
        f"Everyone (cash/food): {snapshot}\n\n"
        + (f"Your strategy sheet. Follow it:\n{SHEETS[agent.name]}\n\n" if USE_SHEETS else "")
        + f"First think it through in 2 or 3 short sentences. Then end with one final line in exactly this form:\n"
        f"DECISION: <{' or '.join(ROLE_ACTIONS[agent.role])}> <BUY or SELL> <qty> AT <price>\n"
        f"or, if you post no order:\n"
        f"DECISION: <{' or '.join(ROLE_ACTIONS[agent.role])}> NONE"
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


ORDER_RE = re.compile(r"\b(BUY|SELL)\s+(\d+)\s*(?:FOOD\s*)?(?:@|AT|FOR)?\s*\$?(\d+)", re.IGNORECASE)


DECISION_RE = re.compile(r"DECISION\s*:\s*(.*)", re.IGNORECASE)


def parse_reply(text, role):
    """Reasoning first, then a DECISION line. Only the last DECISION line counts,
    so orders mentioned while thinking are ignored. No DECISION line means REST and no order.
    Returns (action, side, qty, price, reason, parsed_ok)."""
    if not text.strip():
        return "REST", None, 0, 0, "(empty reply)", False
    hits = DECISION_RE.findall(text)
    reasoning = " ".join(DECISION_RE.sub("", text).split())[:200]
    if not hits:
        return "REST", None, 0, 0, f"(no DECISION line: {' '.join(text.split())[:150]})", False
    decision = " ".join(hits[-1].replace("*", " ").split())
    head = decision.split(" ", 1)[0] if decision else ""
    word = re.sub(r"[^A-Za-z]", "", head).upper()
    ok = word in ROLE_ACTIONS[role]
    action = word if ok else "REST"

    side, qty, price = None, 0, 0
    m = ORDER_RE.search(decision)
    if m:
        side = m.group(1).upper()
        qty = int(m.group(2))
        price = max(MIN_PRICE, int(m.group(3)))

    reason = f"[{decision[:40]}] {reasoning}"
    return action, side, qty, price, reason, ok


def decide(agent, turn, snapshot, prices, last_fill, book):
    try:
        raw = ask_model(system_prompt(agent), user_prompt(agent, turn, snapshot, prices, last_fill, book))
    except Exception as e:
        agent.parse_failures += 1
        return "REST", None, 0, 0, f"(model error: {e})"[:120]
    action, side, qty, price, reason, ok = parse_reply(raw, agent.role)
    if not ok:
        agent.parse_failures += 1
    return action, side, qty, price, reason


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------
def in_shock(turn):
    return SHOCK_START > 0 and SHOCK_START <= turn <= SHOCK_END


def produce(agent, action, turn):
    agent.harvest = 0
    if action == "WORK":
        agent.cash += WORK_PAY
    elif action == "FARM":
        agent.harvest = SHOCK_YIELD if in_shock(turn) else FARM_YIELD
        agent.food += agent.harvest
    agent.counts[action] += 1


def make_order(agent, side, qty, price):
    """Cap orders to what the agent can actually cover. Returns an Order or None."""
    if side is None or qty <= 0:
        return None
    if side == "BUY":
        qty = min(qty, agent.cash // price)
    else:
        qty = min(qty, agent.food)
    return Order(agent, side, qty, price) if qty > 0 else None


def clear_market(orders, rng):
    """Single-price call auction. Returns (price, volume). price is None if nothing traded.
    Lines up buy units from highest bid down and sell units from lowest ask up,
    matches while bid >= ask, and sets one price halfway between the last matched pair."""
    rng.shuffle(orders)                                    # random tie-break
    buys = sorted([o for o in orders if o.side == "BUY"], key=lambda o: -o.price)
    sells = sorted([o for o in orders if o.side == "SELL"], key=lambda o: o.price)
    buy_units = [o for o in buys for _ in range(o.qty)]
    sell_units = [o for o in sells for _ in range(o.qty)]

    matched = 0
    while (matched < len(buy_units) and matched < len(sell_units)
           and buy_units[matched].price >= sell_units[matched].price):
        matched += 1
    if matched == 0:
        return None, 0

    price = (buy_units[matched - 1].price + sell_units[matched - 1].price) // 2
    for i in range(matched):
        b, s = buy_units[i], sell_units[i]
        b.filled += 1
        s.filled += 1
        b.agent.cash -= price
        b.agent.food += 1
        b.agent.bought += 1
        b.agent.spent += price
        s.agent.cash += price
        s.agent.food -= 1
        s.agent.sold += 1
        s.agent.earned_from_sales += price
    return price, matched


def eat(agent):
    if agent.food >= EAT_PER_TURN:
        agent.food -= EAT_PER_TURN
        agent.starve_turns = 0
    else:
        agent.starve_turns += 1


def spoil(agent):
    if STORAGE_CAP and agent.food > STORAGE_CAP:
        agent.spoiled += agent.food - STORAGE_CAP
        agent.food = STORAGE_CAP


def check_death(agent, turn):
    if agent.cash < 0 or agent.starve_turns >= STARVE_TURNS_TO_DIE:
        agent.alive = False
        agent.died_on = turn


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def order_str(side, qty, price):
    return "NONE" if side is None else f"{side} {qty}@{price}"


def fmt_line(turn, agent, action, order_txt, filled, reason):
    tag = "" if agent.alive else "  ** DIED **"
    return (f"T{turn:02d} {agent.name:<5}({agent.role:<6}) {action:<4} {order_txt:<11} "
            f"filled {filled:>2}  cash {agent.cash:>3} food {agent.food:>2}{tag} | {reason[:110]}")


def avg(xs):
    xs = [x for x in xs if x is not None]
    return f"{sum(xs) / len(xs):.1f}" if xs else "n/a"


def print_summary(agents, prices, volumes, elapsed):
    print("\n=== Summary ===")
    ranked = sorted(agents, key=lambda a: (a.alive, a.cash), reverse=True)
    for a in ranked:
        status = "alive" if a.alive else f"dead T{a.died_on}"
        acts = " ".join(f"{k}:{v}" for k, v in a.counts.items() if k in ROLE_ACTIONS[a.role])
        print(f"{a.name:<5}({a.role:<6}) {status:<9} cash {a.cash:>3} food {a.food:>2}  {acts}  "
              f"bought:{a.bought} sold:{a.sold} spoiled:{a.spoiled} no_order:{a.no_order_turns} parse_fail:{a.parse_failures}")

    series = " ".join("-" if p is None else str(p) for p in prices)
    print(f"\nPrices by turn (- = no trade): {series}")
    if SHOCK_START > 0:
        before = prices[:SHOCK_START - 1]
        during = prices[SHOCK_START - 1:SHOCK_END]
        after = prices[SHOCK_END:]
        print(f"Avg price  before shock: {avg(before)}  during (T{SHOCK_START}-T{SHOCK_END}): {avg(during)}  "
              f"after: {avg(after)}")
    print(f"Turns with a trade: {sum(1 for p in prices if p is not None)} of {len(prices)}. "
          f"Food traded: {sum(volumes)}.")
    print(f"Model: {MODEL}. Elapsed: {elapsed:.0f}s. Logs: {LOG_PATH}, {PRICE_LOG_PATH}")


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
    rng = random.Random(SEED)
    agents = [Agent(name, role) for name, role in ROLES.items()]
    prices, volumes = [], []
    last_fill = {a.name: "you posted no order." for a in agents}
    book = None
    start = time.time()

    with open(LOG_PATH, "w", newline="") as f, open(PRICE_LOG_PATH, "w", newline="") as pf:
        writer = csv.writer(f)
        writer.writerow(["turn", "agent", "role", "action", "order", "filled",
                         "cash", "food", "alive", "reason", "harvest", "spoiled_total"])
        pwriter = csv.writer(pf)
        pwriter.writerow(["turn", "shock", "price", "volume", "buy_orders", "sell_orders"])

        for turn in range(1, TURNS + 1):
            living = [a for a in agents if a.alive]
            if not living:
                print(f"\nTurn {turn}: everyone is dead. Stopping early.")
                break

            print(f"\n--- Turn {turn}{'  (drought)' if in_shock(turn) else ''} ---")
            for a in living:
                a.cash -= THINK_COST
            snapshot = public_table(agents)   # everyone decides against the same view

            # 1. Everyone decides against the same snapshot.
            decisions = {}
            for a in living:
                decisions[a.name] = decide(a, turn, snapshot, prices, last_fill[a.name], book)

            # 2. Production, then orders are capped to what each agent now holds.
            orders = {}
            for a in living:
                action, side, qty, price, reason = decisions[a.name]
                produce(a, action, turn)
                if side is None:
                    a.no_order_turns += 1
                orders[a.name] = make_order(a, side, qty, price)

            # 3. Market clears once.
            live_orders = [o for o in orders.values() if o is not None]
            price, volume = clear_market(list(live_orders), rng)
            prices.append(price)
            volumes.append(volume)
            buys_ = [o for o in live_orders if o.side == "BUY"]
            sells_ = [o for o in live_orders if o.side == "SELL"]
            book = (sum(o.qty for o in buys_), max((o.price for o in buys_), default=0),
                    sum(o.qty for o in sells_), min((o.price for o in sells_), default=0))
            n_buy = sum(1 for o in live_orders if o.side == "BUY")
            n_sell = sum(1 for o in live_orders if o.side == "SELL")
            pwriter.writerow([turn, in_shock(turn), "" if price is None else price, volume, n_buy, n_sell])
            pf.flush()

            # 4. Eat, check death, log.
            for a in living:
                action, side, qty, p, reason = decisions[a.name]
                o = orders[a.name]
                filled = o.filled if o else 0
                if o is None:
                    last_fill[a.name] = "you posted no order." if side is None else "your order was empty (you couldn't cover it)."
                elif filled:
                    last_fill[a.name] = f"you {'bought' if o.side == 'BUY' else 'sold'} {filled} food at {price} each."
                else:
                    last_fill[a.name] = f"your {o.side} {o.qty} AT {o.price} did not fill."
                eat(a)
                spoil(a)
                check_death(a, turn)
                otxt = order_str(side, qty, p)
                writer.writerow([turn, a.name, a.role, action, otxt, filled,
                                 a.cash, a.food, a.alive, reason, a.harvest, a.spoiled])
                print(fmt_line(turn, a, action, otxt, filled, reason))
            f.flush()

            mkt = "no trade" if price is None else f"price {price}, {volume} food traded"
            print(f"MARKET T{turn:02d}: {mkt}  (buy orders {n_buy}, sell orders {n_sell})")

    elapsed = time.time() - start
    print_summary(agents, prices, volumes, elapsed)
    return agents, prices, volumes, elapsed


if __name__ == "__main__":
    main()
