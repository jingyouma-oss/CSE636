# Week 4 — Lab & Assignment

> 🧪 **Hands-on work for Week 4.** For the lecture notes, foundations primer, discussion questions, and references, see **[week-04-notes.md](week-04-notes.md)**.

---

## 🧪 Lab: Time-Series Forecasting for Autoscaling

**Objectives:**
- Load and explore a real CPU/memory metrics dataset.
- Train a Prophet forecasting model and evaluate its accuracy.
- Translate the forecast into an autoscaling recommendation.
- (Stretch) Emit the forecast as a Prometheus metric and configure a KEDA ScaledObject.

**Estimated time:** 2–3 hours (can be started in class, completed as homework)

---

### Step 0: Environment Setup

```bash
# Create a virtual environment
python3 -m venv venv-week4
source venv-week4/bin/activate   # Mac/Linux
# venv-week4\Scripts\activate    # Windows

pip install prophet pandas matplotlib scikit-learn requests
```

If you have a Kubernetes cluster available (Minikube, k3s, or a cloud cluster), also install:
```bash
pip install kubernetes
```

---

### Step 1: Get a Metrics Dataset

**Option A — Use a public dataset (easiest).**

The Alibaba Cloud 2018 cluster trace is a publicly available dataset of real cloud workload metrics:

```bash
# Download a sample (the full dataset is large; grab a single machine trace)
wget https://github.com/alibaba/clusterdata/raw/master/cluster-trace-v2018/machine_usage.csv
```

Alternatively, use the provided synthetic dataset in the course repo (simulated daily/weekly CPU cycles with noise), or generate your own:

```python
import pandas as pd
import numpy as np

np.random.seed(42)
n_points = 2016  # 7 days at 5-minute intervals

timestamps = pd.date_range(start="2025-10-01", periods=n_points, freq="5T")

# Simulate: base 30% CPU + daily seasonality + weekly seasonality + noise
t = np.arange(n_points)
daily_cycle = 20 * np.sin(2 * np.pi * t / (24 * 12))          # 24-hour cycle
weekly_cycle = 10 * np.sin(2 * np.pi * t / (7 * 24 * 12))     # 7-day cycle
noise = np.random.normal(0, 3, n_points)
trend = 0.005 * t                                              # slight upward trend

cpu = np.clip(30 + daily_cycle + weekly_cycle + noise + trend, 5, 95)
memory = np.clip(45 + 0.5 * daily_cycle + noise * 0.5, 20, 90)

df_sim = pd.DataFrame({"ds": timestamps, "cpu": cpu, "memory": memory})
df_sim.to_csv("synthetic_metrics.csv", index=False)
print("Generated synthetic_metrics.csv with", len(df_sim), "rows")
```

---

### Step 2: Explore and Preprocess

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("synthetic_metrics.csv", parse_dates=["ds"])
print(df.describe())

# Plot CPU and memory together
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 6), sharex=True)
ax1.plot(df["ds"], df["cpu"], linewidth=0.8, color="steelblue")
ax1.set_ylabel("CPU %")
ax1.set_title("CPU Utilization")
ax1.axhline(70, color="orange", linestyle="--", alpha=0.5, label="Scale-up threshold")
ax1.legend()

ax2.plot(df["ds"], df["memory"], linewidth=0.8, color="coral")
ax2.set_ylabel("Memory %")
ax2.set_title("Memory Utilization")
plt.tight_layout()
plt.savefig("metrics_overview.png", dpi=120)
plt.show()

# Check for missing values
print("\nMissing values:")
print(df.isnull().sum())
```

**What to look for:**
- Repeating daily peaks and troughs — confirms daily seasonality.
- Any sudden spikes that might be anomalies.
- Any gaps in data (timestamps with no reading).

---

### Step 3: Train the Prophet Model

```python
from prophet import Prophet

# Prepare for Prophet (needs 'ds' and 'y' columns)
cpu_df = df[["ds", "cpu"]].rename(columns={"cpu": "y"})

# Temporal split: use last 24 hours as test set
split_time = cpu_df["ds"].max() - pd.Timedelta("24h")
train = cpu_df[cpu_df["ds"] < split_time].copy()
test  = cpu_df[cpu_df["ds"] >= split_time].copy()

print(f"Training on {len(train)} points, evaluating on {len(test)} points")

# Train
model = Prophet(
    daily_seasonality=True,
    weekly_seasonality=True,
    yearly_seasonality=False,
    interval_width=0.80
)
model.fit(train)

# Predict over the full dataset range + 1-hour future
future = model.make_future_dataframe(periods=12, freq="5T")
forecast = model.predict(future)

# Plot
fig = model.plot(forecast)
plt.title("CPU Forecast")
plt.savefig("cpu_forecast.png", dpi=120)

fig2 = model.plot_components(forecast)
plt.savefig("cpu_forecast_components.png", dpi=120)
plt.show()
```

The **components plot** separates trend, daily seasonality, and weekly seasonality — one of Prophet's most useful diagnostic outputs.

---

### Step 4: Evaluate Forecast Accuracy

```python
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

# Align forecast with test set
test_forecast = forecast[forecast["ds"].isin(test["ds"])]
actual = test["y"].values
predicted = test_forecast["yhat"].values

mae  = mean_absolute_error(actual, predicted)
mape = mean_absolute_percentage_error(actual, predicted) * 100

print(f"Evaluation on held-out 24-hour test set:")
print(f"  MAE:  {mae:.2f}% CPU")
print(f"  MAPE: {mape:.1f}%")

# Visualize actual vs. predicted on test period
fig, ax = plt.subplots(figsize=(14, 4))
ax.plot(test["ds"], actual, label="Actual", color="steelblue")
ax.plot(test_forecast["ds"], predicted, label="Predicted", color="orange", linestyle="--")
ax.fill_between(test_forecast["ds"],
                test_forecast["yhat_lower"],
                test_forecast["yhat_upper"],
                alpha=0.2, color="orange", label="80% CI")
ax.axhline(70, color="red", linestyle=":", alpha=0.5, label="Scale-up threshold")
ax.set_title("CPU Forecast vs. Actual (Test Period)")
ax.legend()
plt.savefig("cpu_eval.png", dpi=120)
plt.show()
```

---

### Step 5: Translate Forecast into a Scaling Decision

```python
import math

def recommend_replicas(forecast_df, current_replicas, target_cpu_pct=60,
                       horizon_minutes=30, min_replicas=2, max_replicas=50):
    """
    Given a Prophet forecast DataFrame, recommend a replica count
    to handle the maximum predicted CPU load within the next horizon_minutes.
    """
    now = pd.Timestamp.now()
    cutoff = now + pd.Timedelta(minutes=horizon_minutes)

    upcoming = forecast_df[
        (forecast_df["ds"] > now) & (forecast_df["ds"] <= cutoff)
    ]

    if upcoming.empty:
        print("No future forecast points found. Using last known forecast.")
        upcoming = forecast_df.tail(horizon_minutes // 5)

    # Use the upper confidence bound as a conservative estimate
    max_cpu = upcoming["yhat_upper"].max()

    recommended = math.ceil(current_replicas * max_cpu / target_cpu_pct)
    recommended = max(min_replicas, min(max_replicas, recommended))

    return recommended, max_cpu


current = 4
recommended, max_cpu_pred = recommend_replicas(forecast, current_replicas=current)

print(f"\n--- Autoscaling Recommendation ---")
print(f"Current replicas:           {current}")
print(f"Max predicted CPU (30 min): {max_cpu_pred:.1f}% (upper 80% CI)")
print(f"Target CPU per replica:     60%")
print(f"Recommended replicas:       {recommended}")

if recommended > current:
    print(f"DECISION: Scale UP by {recommended - current} replica(s)")
elif recommended < current:
    print(f"DECISION: Scale DOWN by {current - recommended} replica(s)")
else:
    print("DECISION: No change")
```

---

### Step 6: (Stretch) Emit Forecast as a Prometheus Metric

If you have a Prometheus instance running (e.g., via `kube-prometheus-stack` in Minikube):

```python
from prometheus_client import Gauge, start_http_server
import time

# Start a simple HTTP server exposing Prometheus metrics on port 8000
start_http_server(8000)

predicted_cpu_gauge = Gauge(
    "predicted_cpu_next_30m",
    "Prophet-predicted max CPU % for next 30 minutes",
    ["service"]
)

print("Emitting Prometheus metrics on :8000/metrics ...")
while True:
    # Re-run forecast (in production: retrain periodically, not every loop)
    future = model.make_future_dataframe(periods=6, freq="5T")
    fresh_forecast = model.predict(future)
    _, max_pred = recommend_replicas(fresh_forecast, current_replicas=4)
    predicted_cpu_gauge.labels(service="my-app").set(max_pred)
    print(f"Emitted predicted_cpu_next_30m = {max_pred:.1f}%")
    time.sleep(300)  # update every 5 minutes
```

You can then configure a KEDA `ScaledObject` (as shown in Session 8) pointing to this metric to drive predictive autoscaling.

---

### Lab Deliverables

Submit a zip file containing:

1. **`forecast.ipynb`** — Jupyter notebook (or `.py` scripts) with all steps above completed and outputs visible.
2. **`metrics_overview.png`**, **`cpu_forecast.png`**, **`cpu_eval.png`** — the three plots.
3. **`lab_notes.md`** — a short (1–2 page) write-up answering:
   - What MAPE did you achieve? Is it good enough for autoscaling decisions?
   - What patterns did the Prophet components plot reveal?
   - If actual CPU hit 95% during a spike that the model did not forecast, what would happen with your scaling recommendation? How would you make the system more robust?

---

## Assignment: AI Forecasting for Kubernetes Autoscaling — Effectiveness Analysis

**Due:** Before Week 5 Session 9. Submit via the course portal.

### Prompt

Write a **4–6 page technical report** analyzing the effectiveness of AI-based time-series forecasting for autoscaling in Kubernetes clusters, including a cost-impact analysis. Your report should draw on the lab you completed, external literature, and vendor case studies.

---

### Suggested Report Structure

#### 1. Executive Summary (≈ half a page)

State your main finding: does AI forecasting improve on reactive HPA, and under what conditions? Lead with the answer; use the rest of the report to support it.

#### 2. Baseline: Reactive HPA vs. Predictive Autoscaling (≈ 1 page)

- Explain how standard Kubernetes HPA works and identify its key limitation (the reaction lag).
- Describe the scenarios where this lag causes the most harm (sharp spikes, slow-starting containers).
- Explain how a predictive approach addresses the lag.

#### 3. Your Forecasting Experiment (≈ 1.5 pages)

- Describe your dataset (source, duration, frequency, characteristics observed in exploration).
- Report your Prophet model's MAE and MAPE on the held-out 24-hour test set.
- Show at least one plot comparing actual vs. predicted.
- Analyze where the model was most accurate and where it failed. Relate failures to specific patterns in the data (e.g., unexpected spikes, weekends).
- Discuss at least one alternative approach (e.g., ARIMA, moving average) and explain why Prophet was or was not the best choice for your data.

#### 4. Cost-Impact Analysis (≈ 1 page)

- Estimate the cost difference between three scenarios on a sample workload:
  - **Static over-provisioning** (enough pods for peak load, 24/7)
  - **Reactive HPA** (target 60% CPU, standard HPA settings)
  - **Predictive autoscaling** (Prophet forecast, 30-minute horizon, upper CI)
- Use a simple cloud pricing model. For example: assume each replica costs $0.04/hour on AWS `t3.medium`. Estimate average replica count for each scenario over a simulated 7-day period.
- State your assumptions clearly. Acknowledge that real-world savings depend on workload predictability.

#### 5. Limitations and Failure Modes (≈ 0.5 page)

- When does forecasting-based autoscaling *fail* (cold starts, unpredictable traffic, model drift)?
- What mitigations would you apply in production?

#### 6. Recommendations (≈ 0.5 page)

- For what type of workload and organization would you recommend deploying predictive autoscaling today?
- What monitoring and governance would you put in place?

---

### Rubric Hints

| Criterion | Weight | What graders look for |
|---|---|---|
| Technical accuracy | 30% | Correct explanation of HPA, Prophet, and scaling math; no significant factual errors |
| Experiment quality | 25% | Clear description of data, quantitative evaluation metrics (MAE/MAPE), honest analysis of failures |
| Cost analysis | 20% | Structured comparison with stated assumptions; reasonable numbers; acknowledges uncertainty |
| Critical thinking | 15% | Identifies genuine limitations; doesn't just repeat lecture material; engages with failure modes |
| Clarity and structure | 10% | Well-organized, readable prose; plots labeled; sources cited |

**AI tool disclosure:** If you used an AI assistant (Claude, GPT-4, Copilot, etc.) for any part of this assignment, include a brief note describing what you used it for and how you verified its outputs.
