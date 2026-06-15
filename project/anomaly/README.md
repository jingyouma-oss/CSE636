# Anomaly-detection starter — Week 5 (Observability)

A tiny, runnable companion to the [Week 5 lab](../../weeks/week-05/week-05-lab.md).
It builds the Session 9 loop: **labelled synthetic metrics → Isolation Forest →
score against ground truth with precision / recall / F1** — the metrics that
actually matter when anomalies are rare.

```
anomaly/
├── generate_data.py   # synthetic metrics WITH a ground-truth is_anomaly column
├── detect.py          # Isolation Forest → predictions → precision/recall/F1
├── evaluation.py      # PURE precision/recall/F1 logic (the heart of the lab)
├── tests/             # tests for evaluation.py — run without sklearn
├── requirements.txt
└── Makefile
```

## Run it

```bash
make setup      # venv + deps
make data       # writes metrics_sample.csv with labelled anomalies (stdlib only)
make detect     # fit Isolation Forest, print precision/recall/F1 vs ground truth
make test       # run the scoring-logic tests (no sklearn required)
```

Expected `make detect` output (numbers vary with `--contamination`):

```
Loaded 10080 rows; 201 are labelled anomalies.

Detector scored against ground truth:
  precision=0.78 recall=0.74 f1=0.76 (TP=149 FP=42 FN=52)

Reminder: on imbalanced data, judge by precision/recall/F1 on the anomaly
class — NOT raw accuracy (always-'normal' would look ~98% accurate).
```

## Why it's split this way

The **scoring logic** (`evaluation.py`) is pure and unit-tested — including the
"accuracy trap" case where predicting *all normal* scores ~98% accuracy yet
**zero recall**. That's the lesson the lab is teaching. `detect.py` is the driver
that fits a real `IsolationForest` and feeds its predictions into that scoring.

Tune the detector's sensitivity with `--contamination` (start 0.01–0.05) and
watch precision/recall trade off:

```bash
python detect.py --contamination 0.05
```
