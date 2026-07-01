---
marp: true
theme: gaia
paginate: true
style: |
  pre {
    font-size: 0.72rem;
  }
  table {
    font-size: 0.82rem;
  }
  td {
    padding: 0.4em 0.7em;
  }
---

<!-- _class: lead -->

# Week 4: Predictive Analytics & Capacity Intelligence
## Predict failures, forecast demand, and let agents act on the forecast
### CSE636 — DevOps with AI

Qingsong Zhang, Ph. D.

---

## Where This Week Sits in the Arc

```
0 Setup → 1 Basics → 2 Tooling → 3 CI/CD → [4 Predict] → 5 Observe → 6 Respond → 7 Govern
```

- Weeks 1–3: built the pipeline, put agents **inside** it.
- This week: turn agents **forward-looking** — predict problems before they happen.

| | |
|---|---|
| **Builds on** | Week 3 — agentic CI/CD, approval gates, self-healing |
| **Time budget** | 2 sessions (~2 hrs + ~1.5 hrs) |
| **You'll build** | A Prophet CPU forecast → scaling recommendation |

---

## Mid-term Checkpoint

**Mid-term exam (15%) covers Weeks 1–4.** Closed-book, 60 min: MC + short-answer + one scenario.

| Area | Key concepts |
|---|---|
| Foundations | DevOps lifecycle, CI/CD, perceive–plan–act, autonomy levels |
| AI/ML basics | Supervised vs. unsupervised, features/labels, overfitting |
| LLMs & agents | Tool calling, RAG, context engineering, guardrails, gates |
| Agent protocols | MCP servers/tools/resources, least privilege |
| Agentic CI/CD | Build-failure prediction, test gen, self-healing, blast radius |
| Predictive | Change-risk, canary/blue-green gating, forecasting, HPA, KEDA, FinOps |

Review lab notes + the per-week "Key terms" glossaries.

---

<!-- _class: lead invert -->

# Foundations Primer

---

## Kubernetes in Plain Language

Docker runs *one* container. Kubernetes runs *hundreds* — keeps them healthy and scales them, automatically, across a cluster.

| Machine type | Role |
|---|---|
| **Control plane (master)** | The "brain" — schedules work, watches for problems |
| **Worker nodes** | The "muscles" — run your application containers |

Analogy: control plane = kitchen manager; worker nodes = line cooks. The manager keeps replacing a cook who calls in sick.

---

## Kubernetes Core Objects & HPA

- **Pod** — smallest unit; 1+ containers, shared IP. **Deployment** — desired-state ("3 copies, restart crashes"). **Service** — stable "front door" to healthy pods. **Node** — a machine running a **kubelet**.
- Control plane: `kube-apiserver` (API gateway), `etcd` (state store), `kube-scheduler` (placement), `kube-controller-manager` (control loops).

```yaml
kind: HorizontalPodAutoscaler        # autoscaling/v2
spec:
  scaleTargetRef: { kind: Deployment, name: my-app }
  minReplicas: 2
  maxReplicas: 20
  metrics: [{ type: Resource, resource: { name: cpu,
    target: { type: Utilization, averageUtilization: 60 } } }]  # up when >60%
```

Checks every ~15s. **The catch: it reacts** — pods added *after* the spike hurts users. Session 8 fixes this with **predictive** autoscaling.

---

## Supervised ML + Time Series

Teach a new hire to estimate ticket resolution from 1,000 past tickets:
- **Features** = the facts (type, product area, tier). **Label** = the outcome.
- Feed **(features, label)** pairs → algorithm fits a **model** mapping features → labels.
- **Overfitting** = memorizes training data, fails on new data. **Evaluation** = held-out test set.

A **time series** = measurements over time (CPU/min); forecasting = predicting from history.

| Pattern | Example |
|---|---|
| **Trend** — steady drift | Growing users → rising baseline CPU |
| **Seasonality** — repeating cycles | Nightly batch spike at 2 AM |
| **Noise** — random fluctuation | Random request bursts |
| **Spikes** — sudden short peaks | Viral event → 10× traffic |

---

## Forecasting Algorithms (Preview)

| Algorithm | Analogy | Best for |
|---|---|---|
| **Moving average** | Average last N readings | Smoothing noise, short baselines |
| **Exp. smoothing (ETS)** | Recent points count more | Moderate horizon, single season |
| **Prophet** | Auto trend + seasonality + holidays | Daily/weekly cycles, missing data |
| **ARIMA / SARIMA** | Models autocorrelation | Smooth stationary series |
| **LSTM / Transformer** | NN learns long-range patterns | Complex multivariate; lots of data |

This week's lab uses **Prophet** — beginner-friendly, handles gaps, gives confidence intervals.

---

<!-- _class: lead invert -->

# Session 7
## Risk Prediction & Deployment Intelligence
### Wednesday evening — ~2 hours

By the end: explain why deploys fail · canary vs. blue-green + AI gating ·
agentic rollback + guardrails · deployment-scoring features · the labeling challenge

---

## Why Do Deployments Fail?

Works on the laptop, breaks in prod. Common causes:

- Bugs introduced by the change (logic errors, regressions).
- **Configuration drift** — prod differs from staging subtly.
- Dependency issues — a downstream API changed.
- Insufficient capacity — new version OOMs.
- Human error in deployment procedures.

Catching failures *after* full rollout hits **all** users. **Progressive delivery** = roll out to a small slice first, measure, widen only if healthy.

---

## Canary & Blue-Green

**Canary** (mine-canary early warning): route a small % to the new version, watch, widen or abort.
```
stable 100% → deploy canary 5% → watch errors/latency
   healthy?  → 5% → 25% → 50% → 100%      degraded? → all back to stable
```

**Blue-green**: two identical envs; deploy to green, smoke-test, flip the LB instantly; blue stays as rollback target. Automated by **Argo Rollouts**, **Flagger**, **Spinnaker**; the AI layer replaces the human watching dashboards.

| | Canary | Blue-Green |
|---|---|---|
| Rollout / rollback | Gradual (reroute) | Instant (flip) |
| Blast radius | Small (canary %) | All users |
| Infra cost | Low | Higher (two envs) |
| Best for | High-traffic, risk-averse | Zero-downtime cutover |

**Quiz:** A payment service needs zero-downtime cutover + fast rollback, but you fear exposing all users to a bad release.

<details><summary>Which strategy trades which risk?</summary>

**Blue-green** = instant cutover + instant rollback, but exposes **all** users on flip. **Canary** limits blast radius (5% first) at the cost of a slower rollout. Many teams combine: deploy to green, then shift traffic canary-style.

</details>

---

## AI Gating: Scoring a Deployment

A model/agent watches canary metrics and recommends advance/abort.

- **Features:** error-rate delta, p99 delta, CPU/mem increase, change volume, time of day, # dependencies, historical fail rate, security files touched.
- **Label:** succeeded (1) vs. rollback/hotfix within 24h (0).
- **Train:** gradient-boosted tree (XGBoost) or logistic regression on history.
- **Infer:** after 15 min → "78% healthy". Below threshold (70%) → recommend abort.

**The autonomy dial** — same score, three policies:

| Policy | Behavior |
|---|---|
| **Human-in-the-loop** | Posts recommendation to Slack; a human approves |
| **Human-on-the-loop** | Auto-aborts unless a human overrides within 5 min |
| **Autonomous** | Aborts immediately, notifies on-call after |

---

## Agentic Rollback: Perceive → Reason → Act → Observe

**Perceive** metrics · **Reason** (this deploy vs. unrelated incident?) · **Act** if confident, else escalate · **Observe** recovery. **Guardrail (Week 3):** act only if confidence > threshold AND no other system is already acting (race prevention).

```
[Agent] get_metrics(service="checkout", window="15m")
  → error_rate=4.2%, p99=820ms, baseline_error=0.3%, baseline_p99=210ms
[Agent] check_related_incidents() → none affecting checkout's dependencies
[Agent] Reasoning: error_rate +14x, p99 +4x. No external cause.
  Confidence 0.91. Threshold 0.80. Action: rollback.
[Agent] trigger_rollback(deployment="checkout-v2.3.1") → ETA 45s
[Agent] notify_oncall(summary="Rolled back checkout-v2.3.1, 14x error spike.")
```

**Human-on-the-loop** — the agent acts, then notifies a human who can reverse it.

---

## Change-Risk Scoring

A **change-risk score** (0–100) is assigned *before* deployment — flag high-risk changes for extra review. DORA-backed signals that predict failure:

- **Large diffs** (many files/lines) · **decreased test coverage** · **Friday-afternoon deploys** · **time since last deploy** (drift) · **service coupling** (many deps).

Train a gradient-boosted classifier on org history; score every PR.

---

## Data Labeling & Evaluation Challenges

| Challenge | Problem |
|---|---|
| **Label noise** | "Failed" = rollback? incident? complaint? Inconsistent definitions |
| **Survivorship bias** | Canary safety net hides what a full bad rollout would have done |
| **Class imbalance** | 95% succeed → "always predict success" gets 95% accuracy, catches 0 failures |
| **Concept drift** | Model trained on last year ≠ today's architecture; retrain on rolling window |
| **Evaluation** | Time-ordered data → **temporal CV** (train past, test future); never shuffle |

---

## Quiz: The 95% Accuracy Trap

**Q:** Your risk model reports **95% accuracy**, and 95% of historical deploys succeeded. Why might it be worthless, and what would you measure instead?

<details><summary>Discuss, then reveal</summary>

A model that **always predicts "success"** scores 95% on **class-imbalanced** data while catching **zero** real failures. Measure **precision, recall, and F1 on the failure class**: recall = fraction of real failures caught, precision = how many alarms are real. Also train with class weighting / balanced sampling.

</details>

---

## Worked Example: Train (18 mo, 2,400 deploys, 120 rollbacks)

```python
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report

# features: files_changed, lines_added/deleted, test_coverage_delta,
#   hour_of_day, day_of_week, num_dependencies, days_since_last_deploy,
#   team_rollback_rate_30d   (label: 0=success, 1=rollback)

# Temporal split: train first 80%, test last 20% (df sorted chronologically)
split_idx = int(len(df) * 0.8)
train, test = df.iloc[:split_idx], df.iloc[split_idx:]

model = GradientBoostingClassifier(
    n_estimators=100, max_depth=4,
    class_weight="balanced")   # handle class imbalance
model.fit(train[features], train["label"])
print(classification_report(test["label"], model.predict(test[features])))
```

---

## Worked Example: Score & Gate

```python
risk_score = model.predict_proba(new_deploy)[0][1]  # P(rollback)
print(f"Deployment risk score: {risk_score:.2%}")

if risk_score > 0.5:
    print("HIGH RISK: staged canary + extra approval.")
elif risk_score > 0.25:
    print("MEDIUM RISK: canary rollout.")
else:
    print("LOW RISK: standard deployment.")
```

The score maps to a graduated deployment policy — not a hard yes/no.

---

## Common Pitfalls — Session 7

- **Accuracy alone on imbalanced data** — report precision/recall/F1 for the minority class.
- **Shuffling time-series for train/test** — leaks the future; split chronologically.
- **Threshold too low** — "rollback fatigue" erodes trust; calibrate false-positive rate.
- **Ignoring the human factor** — models encode past practices; retrain after process changes.
- **Autonomous rollback without race protection** — two agents rolling back at once conflict; use locks or one orchestrator.

---

## Key Terms — Session 7

| Term | Definition |
|---|---|
| **Progressive delivery** | Release gradually, measure, widen only when healthy |
| **Canary** | Route a small % to the new version; widen or abort on metrics |
| **Blue-green** | Two identical envs; switch instantly; old env is rollback target |
| **AI gate** | Model/agent that makes advance/abort decisions |
| **Change-risk score** | Pre-deploy predicted probability a change causes an incident |
| **Temporal cross-validation** | Train on past, test on future — never shuffle |
| **Concept drift** | Learned patterns no longer match reality |
| **DORA metrics** | Deploy frequency, lead time, change-fail rate, MTTR |

---

<!-- _class: lead invert -->

# Session 8
## Capacity & Performance Forecasting
### Saturday morning — ~1.5 hours

By the end: FinOps + AI cost control · find bottlenecks from forecasts ·
predictive HPA & KEDA · Prophet/ARIMA intuition · forecast → scaling policy

---

## The Cost of Getting Capacity Wrong + FinOps

Cloud is pay-per-use. Two failure modes:
- **Under-provisioning** → slow/unavailable → revenue lost (Slack 2021: 2-hr degradation).
- **Over-provisioning** → wasted spend (30–40% of enterprise capacity idles off-peak).

**FinOps** treats cloud spend as an operational metric:

| Phase | What you do |
|---|---|
| **Inform** | Measure & attribute spend by service/team/feature |
| **Optimize** | Right-sizing, reserved, spot |
| **Operate** | Embed cost awareness into culture |

AI contributes: anomaly detection on cost, **right-sizing** (request vs. usage), spot scheduling, and **predictive autoscaling** — this session's focus.

---

## Identifying Bottlenecks in Microservices

One slow service surfaces as slowness in a *different* dependent service.

1. Collect per-pod CPU / memory / network time series.
2. Correlate with latency/error — if A slows whenever B hits 80% CPU, **B is the bottleneck**.
3. Use dependency maps (tracing, Week 5) to see who depends on B.
4. Forecast B's CPU — trending to 80% in 2 hrs? Scale B **now**.

Per-service forecasting is targeted; cluster-level is simpler for node scaling.

---

## Forecasting Algorithms — Deeper Dive

**Prophet** — decomposes a business time series:
```
y(t) = trend(t) + seasonality(t) + holidays(t) + noise(t)
```
- Trend: linear or logistic (natural ceiling, e.g. % CPU). Seasonality: Fourier → auto daily/weekly. Holidays: known events. Gives **uncertainty intervals**.

**ARIMA** — classical: **AR** (weighted past values) + **I** (differenced to stationary) + **MA** (past errors). **SARIMA** adds seasonality; harder to tune than Prophet.

**LSTM** — recurrent NN for long-range multivariate patterns; needs **thousands** of points + GPU. For most K8s autoscaling, **Prophet or SARIMA is enough**. (Moving average = `mean(last N)` baseline; lags trends.)

---

## Reactive vs. Predictive HPA

**Reactive HPA** adds pods *after* CPU crosses the threshold:
```
threshold crossed → schedule pod → container start → readiness probe
                    └──────── typically 60–120s lag ────────┘   ← users hurt
```

**Predictive HPA** feeds a forecast into the decision *before* load arrives:
1. Forecast CPU for the next 5–15 min (e.g., Prophet on CPU history).
2. `desired_replicas = ceil(predicted_cpu / target_cpu_per_replica)`
3. Scale **now**, before load materializes.

Via custom controllers (Predictive HPA project) and **KEDA**. Keep a reactive floor for unforecastable spikes.

---

## KEDA — Event-Driven Autoscaling

Scales on **external** metrics (queues, custom Prometheus, cron), not just CPU/mem. **Predictive pattern:** emit the forecast as a metric → a `ScaledObject` scales on **predicted** future load.

```yaml
kind: ScaledObject                 # keda.sh/v1alpha1
spec:
  scaleTargetRef: { name: my-app }
  minReplicaCount: 2
  maxReplicaCount: 50
  triggers:
  - type: prometheus               # forecast-driven trigger
    metadata:
      metricName: predicted_cpu_next_15m
      threshold: "60"              # scale when predicted CPU > 60%
      query: predicted_cpu_next_15m{service="my-app"}
  - type: cron                     # business-hours floor
    metadata: { start: "0 7 * * 1-5", end: "0 21 * * 1-5", desiredReplicas: "10" }
```

Forecast trigger + cron floor = robust real-world pattern.

---

## Quiz: Why Predictive HPA?

**Q:** Reactive HPA already scales when CPU crosses 60%. What concrete problem does a *predictive* HPA solve that a reactive one cannot?

<details><summary>Discuss, then reveal</summary>

The **scale-up lag**. Reactive HPA only adds pods *after* the threshold, and new pods take 60–120s to schedule/start/pass readiness — so a sharp spike hurts users during that window. Predictive HPA forecasts load 5–15 min out and scales *before* it arrives. Keep a reactive floor for unforecastable spikes.

</details>

---

## Agents That Recommend Scaling Policies

An **agentic scaling advisor** reasons about full context:

- Scale **horizontally** (more pods) or **vertically** (bigger pods)?
- **Spot** (cheaper, interruptible) vs. **on-demand**?
- Is the bottleneck *here* or in a **dependency** — will scaling even help?

```
[Agent] get_forecast(service="payment-api", horizon="30m")
  → predicted_cpu: 78% in 15m, 91% in 30m (confidence: high)
[Agent] get_cost_estimate(scale_out=5, instance_type="on_demand") → $2.40/hr
[Agent] get_cost_estimate(scale_out=5, instance_type="spot")      → $0.70/hr (3.4x cheaper)
[Agent] check_spot_availability(region="us-west-2") → available (87% last 7d)
[Agent] Recommend: scale 8 → 13 replicas on spot. Save $1.70/hr. Rollback: on-demand.
[Agent] Awaiting human approval...
```

**Human-in-the-loop** — agent reasons, human confirms.

---

## Demo: Forecast → Scale Pipeline

```
1 CPU history      2 Prophet           3 Replica calc        4 Scale action
(ds/y 5-min    →   (trend +       →    ceil(replicas ×   →   "5 → 7 pods"
 samples)           seasonality,        cpu/target,           (pre-emptive)
                    +30 min forecast)   clamp min/max)
```

- **Evaluate first:** hold out last 24 hrs → check MAE/MAPE. MAPE < ~10% = safe to act.
- Use the **upper confidence bound** when under-provisioning costs more than over.

```bash
pip install prophet pandas matplotlib scikit-learn
```

---

## Demo: Train Prophet

```python
import pandas as pd
from prophet import Prophet

df = pd.read_csv("cpu_metrics.csv", parse_dates=["timestamp"])
df = df.rename(columns={"timestamp": "ds", "cpu_utilization": "y"})  # Prophet needs ds, y

model = Prophet(daily_seasonality=True, weekly_seasonality=True,
                yearly_seasonality=False,  # only a few weeks of data
                interval_width=0.80)       # 80% confidence interval
model.fit(df)
```

Always **plot your data first** — look for repeating patterns.

---

## Demo: Forecast → Scaling Decision

```python
import math
# 12 * 5 min = 60 min of future timestamps; yhat_upper = upper confidence bound
future = model.make_future_dataframe(periods=12, freq="5T")
forecast = model.predict(future)   # yhat, yhat_lower, yhat_upper

# Max predicted CPU over next 30 min (upper CI for safety)
horizon = pd.Timestamp.now() + pd.Timedelta("30min")
upcoming = forecast[(forecast.ds > pd.Timestamp.now()) & (forecast.ds <= horizon)]
max_cpu = upcoming["yhat_upper"].max()

current_replicas = 5
target_cpu_per_replica = 60
required = max(2, min(50, math.ceil(current_replicas * max_cpu / target_cpu_per_replica)))

if required > current_replicas:
    print(f"ACTION: Scale UP by {required - current_replicas} (pre-emptive)")
```
```
Max predicted CPU in next 30 min: 83.4%
Current: 5   Recommended: 7   ACTION: Scale UP by 2 replicas (pre-emptive)
```

---

## Demo: Evaluate on Held-Out Data

```python
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

cutoff = df["ds"].max() - pd.Timedelta("24h")   # hold out last 24 hrs
train_df, test_df = df[df.ds < cutoff], df[df.ds >= cutoff]

eval_model = Prophet(daily_seasonality=True, weekly_seasonality=True).fit(train_df)
fc = eval_model.predict(eval_model.make_future_dataframe(len(test_df), freq="5T"))
pred = fc[fc.ds.isin(test_df.ds)]["yhat"].values
print(f"MAE: {mean_absolute_error(test_df.y, pred):.2f}%  "
      f"MAPE: {mean_absolute_percentage_error(test_df.y, pred)*100:.1f}%")
```

**MAPE under 10%** on CPU is generally good enough to act on.

**Why split chronologically, not shuffle?** The data is time-ordered — shuffling leaks *future* points into training ("sees the answer") → over-optimistic score that collapses in prod. **Temporal CV** mirrors real use: predict forward from past only.

---

## Common Pitfalls — Session 8

- **No seasonality decomposition** — plot first; strong daily patterns must be modeled.
- **Scaling on a too-high confidence bound** — chronic over-provisioning; match CI to cost trade-off.
- **Ignoring scale-down** — draining + cooldown, or you drop active connections.
- **Bad training data** — capped/misconfigured periods teach the wrong baseline; inspect first.
- **Treating the forecast as ground truth** — keep safety margins + manual override.
- **Forgetting to retrain** — models drift; schedule retraining or trigger on error threshold.

---

## Key Terms — Session 8

| Term | Definition |
|---|---|
| **FinOps** | Financial accountability for cloud spend as an operational metric |
| **Right-sizing** | Match resource requests to actual usage |
| **Predictive HPA** | Scale on a forecast, not current metrics |
| **KEDA** | Event-driven autoscaling on external metrics (queues, custom, cron) |
| **Prophet** | Meta's forecasting lib; trend + seasonality + holidays |
| **MAE / MAPE** | Mean absolute error / as a percentage of actuals |
| **Confidence interval** | Range the true value should fall in (e.g., 80%) |
| **Spot / preemptible** | Deep-discount VM, terminable on short notice |
| **Vertical vs. horizontal** | Bigger pods vs. more replicas (K8s prefers horizontal) |

---

## Recap & Looking Ahead

Moved from **reactive** to **predictive** operations — historical data holds patterns ML extracts to act before users feel impact.

- **Deployment risk is quantifiable** — change-risk scores + AI-gated canaries cut blast radius.
- **Autoscaling lag is solvable** — forecasting gives a 15–30 min preview.
- **Cost and reliability are one coin** — FinOps eliminates *waste*, not performance.
- **Agents need forecasts** — accurate forecasting is the foundation for autonomous action.

**Week 5 — detecting anomalies in the present:** unsupervised ML (isolation forests), LLM log analysis, RCA agents, OpenTelemetry GenAI observability. Weeks 4–5 = the intelligence layer for Week 6's autonomous incident response.

---

<!-- _class: lead invert -->

# Questions?

Run the Prophet forecast in `project/forecasting/` — then bring your MAE/MAPE to the lab.
