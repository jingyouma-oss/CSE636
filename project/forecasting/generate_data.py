"""
Generate a synthetic CPU-utilization time series for the Week 4 forecasting lab.

Produces realistic-looking data with a rising trend, a daily seasonality cycle,
random noise, and one injected spike — exactly the patterns Prophet decomposes.
No cloud account or real metrics needed: run this, then run forecast.py.

Usage:
    python generate_data.py            # writes cpu_metrics.csv (14 days, 5-min step)
    python generate_data.py --days 7   # shorter series
"""
from __future__ import annotations

import argparse
import csv
import math
from datetime import datetime, timedelta

# Deterministic pseudo-randomness so every student gets the same data
# (Math.random()/random without a seed would make results irreproducible).
import random


def generate(days: int = 14, step_minutes: int = 5, seed: int = 42):
    rng = random.Random(seed)
    start = datetime(2025, 10, 1, 0, 0, 0)
    n = days * 24 * (60 // step_minutes)

    rows = []
    for i in range(n):
        ts = start + timedelta(minutes=i * step_minutes)
        hours = i * step_minutes / 60.0

        baseline = 30.0                       # idle-ish baseline
        trend = 0.03 * hours                  # slow growth as "users" arrive
        # daily cycle: peak mid-afternoon, trough overnight
        daily = 18.0 * math.sin((ts.hour - 6) / 24.0 * 2 * math.pi)
        noise = rng.gauss(0, 3.0)

        cpu = baseline + trend + daily + noise

        # inject a viral spike on day 9 for ~90 minutes
        if days >= 9 and 9 * 24 + 14 <= hours <= 9 * 24 + 15.5:
            cpu += 35.0

        cpu = max(1.0, min(99.0, cpu))        # clamp to a sane 1–99%
        rows.append((ts.isoformat(), round(cpu, 1)))

    return rows


def main():
    ap = argparse.ArgumentParser(description="Generate synthetic CPU metrics CSV.")
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--step-minutes", type=int, default=5)
    ap.add_argument("--out", default="cpu_metrics.csv")
    args = ap.parse_args()

    rows = generate(days=args.days, step_minutes=args.step_minutes)
    with open(args.out, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["timestamp", "cpu_utilization"])
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {args.out} "
          f"({args.days} days @ {args.step_minutes}-min step).")


if __name__ == "__main__":
    main()
