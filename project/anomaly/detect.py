"""
Run an Isolation Forest over the synthetic metrics and score it against the
ground-truth labels — the core of the Week 5 anomaly-detection lab.

Run `python generate_data.py` first to create metrics_sample.csv.

Usage:
    python detect.py
    python detect.py --contamination 0.02
"""
from __future__ import annotations

import argparse
import sys

import pandas as pd

from evaluation import score

try:
    from sklearn.ensemble import IsolationForest
except ImportError:  # pragma: no cover - environment guidance
    print(
        "scikit-learn is not installed. Run `make setup` "
        "(or `pip install -r requirements.txt`).\n"
        "Note: the precision/recall logic in evaluation.py is tested separately "
        "via `make test` and needs no extra deps.",
        file=sys.stderr,
    )
    raise

FEATURES = ["cpu_pct", "mem_pct", "req_per_sec", "error_rate"]


def main():
    ap = argparse.ArgumentParser(description="Isolation Forest anomaly detection + scoring.")
    ap.add_argument("--data", default="metrics_sample.csv")
    ap.add_argument("--contamination", type=float, default=0.02,
                    help="expected fraction of anomalies (start 0.01–0.05)")
    args = ap.parse_args()

    df = pd.read_csv(args.data, parse_dates=["timestamp"])
    print(f"Loaded {len(df)} rows; {int(df['is_anomaly'].sum())} are labelled anomalies.")

    model = IsolationForest(
        n_estimators=100, contamination=args.contamination, random_state=42
    )
    model.fit(df[FEATURES])

    # IsolationForest: predict returns -1 for anomalies, 1 for normal.
    pred = model.predict(df[FEATURES])
    df["pred_anomaly"] = (pred == -1).astype(int)

    s = score(df["is_anomaly"], df["pred_anomaly"])
    print(f"\nDetector scored against ground truth:\n  {s}")
    print("\nReminder: on imbalanced data, judge by precision/recall/F1 on the "
          "anomaly class — NOT raw accuracy (always-'normal' would look ~98% accurate).")

    found = df[df["pred_anomaly"] == 1]
    print(f"\nTop flagged rows (showing up to 5 of {len(found)}):")
    cols = ["timestamp", "cpu_pct", "error_rate", "is_anomaly"]
    print(found[cols].head().to_string(index=False))


if __name__ == "__main__":
    main()
