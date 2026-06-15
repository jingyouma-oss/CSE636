"""
Train Prophet on CPU history, forecast the next hour, and turn the forecast
into a Kubernetes scaling recommendation — the full Week 4 loop.

Run `python generate_data.py` first to create cpu_metrics.csv.

Usage:
    python forecast.py
    python forecast.py --current-replicas 5 --target-cpu 60 --horizon-min 30
"""
from __future__ import annotations

import argparse
import sys

import pandas as pd

from scaling import decide

try:
    from prophet import Prophet
except ImportError:  # pragma: no cover - environment guidance
    print(
        "Prophet is not installed. Run `make setup` (or "
        "`pip install -r requirements.txt`).\n"
        "Note: the scaling logic in scaling.py is tested separately via "
        "`make test` and does not need Prophet.",
        file=sys.stderr,
    )
    raise


def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    return df.rename(columns={"timestamp": "ds", "cpu_utilization": "y"})


def evaluate(df: pd.DataFrame) -> None:
    """Hold out the last 24h and report MAE / MAPE (temporal split — no shuffle)."""
    from sklearn.metrics import (
        mean_absolute_error,
        mean_absolute_percentage_error,
    )

    cutoff = df["ds"].max() - pd.Timedelta("24h")
    train_df, test_df = df[df["ds"] < cutoff], df[df["ds"] >= cutoff]
    if test_df.empty:
        print("Not enough data to evaluate (need > 24h). Skipping eval.")
        return

    m = Prophet(daily_seasonality=True, weekly_seasonality=True, interval_width=0.80)
    m.fit(train_df)
    future = m.make_future_dataframe(periods=len(test_df), freq="5min")
    fc = m.predict(future)
    pred = fc[fc["ds"].isin(test_df["ds"])]["yhat"].values
    actual = test_df["y"].values
    print(f"  MAE:  {mean_absolute_error(actual, pred):.2f}% CPU")
    print(f"  MAPE: {mean_absolute_percentage_error(actual, pred) * 100:.1f}%  "
          f"(< ~10% is good enough to act on)")


def main():
    ap = argparse.ArgumentParser(description="Prophet CPU forecast → scaling recommendation.")
    ap.add_argument("--data", default="cpu_metrics.csv")
    ap.add_argument("--current-replicas", type=int, default=5)
    ap.add_argument("--target-cpu", type=float, default=60.0)
    ap.add_argument("--horizon-min", type=int, default=30)
    args = ap.parse_args()

    df = load(args.data)
    print(f"Loaded {len(df)} rows from {args.data}.")

    model = Prophet(daily_seasonality=True, weekly_seasonality=True,
                    yearly_seasonality=False, interval_width=0.80)
    model.fit(df)

    periods = max(1, args.horizon_min // 5)
    future = model.make_future_dataframe(periods=periods, freq="5min")
    forecast = model.predict(future)

    # Use the UPPER confidence bound for the horizon — safer for scale-up.
    horizon = forecast.tail(periods)
    max_pred = float(horizon["yhat_upper"].max())
    print(f"\nMax predicted CPU (upper 80% CI) in next {args.horizon_min} min: "
          f"{max_pred:.1f}%")

    d = decide(args.current_replicas, max_pred, target_cpu_per_replica=args.target_cpu)
    print(f"Current replicas:     {d.current_replicas}")
    print(f"Recommended replicas: {d.recommended_replicas}")
    print(f"ACTION: {d.action}")

    print("\nEvaluating forecast accuracy on held-out last 24h:")
    evaluate(df)


if __name__ == "__main__":
    main()
