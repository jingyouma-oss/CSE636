# Forecasting starter — Week 4 (Predictive Analytics)

A tiny, runnable companion to the [Week 4 lab](../../weeks/week-04/week-04-lab.md).
It walks the full loop from the lecture: **CPU history → Prophet forecast →
scaling recommendation**, and evaluates the forecast with a proper temporal
train/test split.

```
forecasting/
├── generate_data.py   # synthetic CPU time series (trend + daily cycle + noise + spike)
├── forecast.py        # train Prophet, forecast the next hour, recommend replicas
├── scaling.py         # PURE forecast→replicas logic (the heart of the lab)
├── tests/             # tests for scaling.py — run without Prophet
├── requirements.txt
└── Makefile
```

## Run it

```bash
make setup      # venv + deps (Prophet build can take a few minutes the first time)
make data       # writes cpu_metrics.csv (stdlib only — works even before setup finishes)
make forecast   # prints "Max predicted CPU …", a replica recommendation, and MAE/MAPE
make test       # runs the scaling-logic tests (no Prophet required)
```

Expected `make forecast` output (numbers vary):

```
Max predicted CPU (upper 80% CI) in next 30 min: 83.4%
Current replicas:     5
Recommended replicas: 7
ACTION: Scale UP by 2 replica(s) (pre-emptive)

Evaluating forecast accuracy on held-out last 24h:
  MAE:  3.1% CPU
  MAPE: 6.8%  (< ~10% is good enough to act on)
```

## Why it's split this way

The **scaling decision** (`scaling.py`) is pure, dependency-free, and unit-tested
— that's the concept the lab is really teaching, and `make test` proves it works
without the heavy Prophet install. `forecast.py` is the driver that feeds a real
Prophet forecast into that logic. Swap in the real Alibaba cluster trace (see the
lab's references) by pointing `--data` at a CSV with `timestamp,cpu_utilization`
columns.

> Tweak the decision: `python forecast.py --current-replicas 8 --target-cpu 70 --horizon-min 15`
