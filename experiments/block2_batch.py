"""
Block 2 batch runner. Confirms Runs 8 and 9 with repeats, unattended.

Runs block2_market.py several times per arm, alternating drought and control,
and ends with one results table. Each run's full screen output and logs go in runs/.

Run:  caffeinate -i python3 block2_batch.py
      (caffeinate stops the Mac sleeping mid-batch; about 90 minutes for 3 + 3 on qwen)
Out:  runs/<arm>_<n>.txt, runs/<arm>_<n>_log.csv, runs/<arm>_<n>_prices.csv, block2_batch.csv
"""

import contextlib
import csv
import os
import sys
import time

import block2_market as m

RUNS_PER_ARM = 3
MODEL = "qwen2.5:7b"
ARMS = {
    "drought": 15,     # SHOCK_START
    "control": 0,
}
OUT_DIR = "runs"
RESULTS_PATH = "block2_batch.csv"

# Price windows, matching the Run 8 vs Run 9 comparison.
WINDOWS = [("T1-14", 1, 14), ("T15-22", 15, 22), ("T23-40", 23, 40)]


def window_avg(prices, lo, hi):
    xs = [p for p in prices[lo - 1:hi] if p is not None]
    return round(sum(xs) / len(xs), 2) if xs else None


def one_run(arm, n):
    m.MODEL = MODEL
    m.SHOCK_START = ARMS[arm]
    tag = f"{arm}_{n}"
    m.LOG_PATH = os.path.join(OUT_DIR, f"{tag}_log.csv")
    m.PRICE_LOG_PATH = os.path.join(OUT_DIR, f"{tag}_prices.csv")
    with open(os.path.join(OUT_DIR, f"{tag}.txt"), "w") as out, contextlib.redirect_stdout(out):
        agents, prices, volumes, elapsed = m.main()
    workers = [a for a in agents if a.role == "worker"]
    farmers = [a for a in agents if a.role == "farmer"]
    row = {
        "arm": arm,
        "run": n,
        "survivors": sum(a.alive for a in agents),
        "workers_alive": sum(a.alive for a in workers),
        "trade_turns": sum(1 for p in prices if p is not None),
        "food_traded": sum(volumes),
        "farmer_cash": sum(a.cash for a in farmers),
        "worker_cash": sum(a.cash for a in workers),
        "no_order": sum(a.no_order_turns for a in agents),
        "rests": sum(a.counts["REST"] for a in agents),
        "parse_fail": sum(a.parse_failures for a in agents),
        "minutes": round(elapsed / 60, 1),
    }
    for name, lo, hi in WINDOWS:
        row[f"price_{name}"] = window_avg(prices, lo, hi)
    return row


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def fmt(x):
    return "n/a" if x is None else f"{x:.1f}"


def print_table(rows):
    print("\n=== Batch results ===")
    cols = ["arm", "run", "survivors", "workers_alive", "trade_turns", "food_traded",
            "price_T1-14", "price_T15-22", "price_T23-40", "no_order", "rests", "parse_fail", "minutes"]
    print("  ".join(f"{c:>12}" for c in cols))
    for r in rows:
        print("  ".join(f"{str(r[c]):>12}" for c in cols))

    print("\nMean price by window")
    print(f"{'window':<8} {'drought':>8} {'control':>8} {'gap':>6}")
    for name, _, _ in WINDOWS:
        d = mean([r[f"price_{name}"] for r in rows if r["arm"] == "drought"])
        c = mean([r[f"price_{name}"] for r in rows if r["arm"] == "control"])
        gap = None if d is None or c is None else d - c
        print(f"{name:<8} {fmt(d):>8} {fmt(c):>8} {fmt(gap):>6}")

    for arm in ARMS:
        ws = [r["workers_alive"] for r in rows if r["arm"] == arm]
        print(f"Workers alive at T40, {arm}: {ws} (of 3 each run)")
    print(f"\nFull rows: {RESULTS_PATH}. Per-run output and logs: {OUT_DIR}/")


def main():
    m.MODEL = MODEL
    m.check_ollama()
    os.makedirs(OUT_DIR, exist_ok=True)

    order = [(arm, n) for n in range(1, RUNS_PER_ARM + 1) for arm in ARMS]  # alternate arms
    rows = []
    start = time.time()
    for i, (arm, n) in enumerate(order, 1):
        print(f"[{time.strftime('%H:%M')}] run {i}/{len(order)}: {arm} #{n} ...", flush=True)
        try:
            row = one_run(arm, n)
        except Exception as e:
            print(f"    failed: {e}. Skipping.", flush=True)
            continue
        rows.append(row)
        print(f"    done in {row['minutes']} min. workers alive {row['workers_alive']}/3, "
              f"prices {row['price_T1-14']} / {row['price_T15-22']} / {row['price_T23-40']}", flush=True)
        with open(RESULTS_PATH, "w", newline="") as f:          # rewrite after every run
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    if not rows:
        sys.exit("No runs finished.")
    print_table(rows)
    print(f"Total time: {(time.time() - start) / 60:.0f} min.")


if __name__ == "__main__":
    main()
