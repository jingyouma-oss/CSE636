# Week 4: Predictive Analytics & Capacity Intelligence

> 📝 **Lecture notes.** The hands-on lab and assignment for this week live in **[week-04-lab.md](week-04-lab.md)**.


**Theme:** Use machine learning to anticipate problems before they happen — predict whether a deployment will fail, forecast how much CPU and memory a cluster will need in an hour, and let an agent act on those forecasts to scale infrastructure and control costs.

**Where it sits in the arc:** Weeks 1–3 built your pipeline and put agents inside it. This week you turn the agents forward-looking: instead of reacting to problems, they *predict* them. The skills you build here feed directly into Week 5, where you learn to *detect* anomalies and do root-cause analysis after things go wrong.

**Builds on:** [Week 3](../week-03/week-03-notes.md) — agentic CI/CD, approval gates, and self-healing pipelines. You already have agents that can open PRs and fix failing builds; now you will give them forecasting data to decide *whether to deploy at all* and how many resources to reserve.

---

> ### Mid-term Checkpoint
>
> **The mid-term exam (15% of your grade) covers Weeks 1–4.** It will be held in the Session 8 time slot next week (check the schedule). Below are the key concepts to review before the exam.
>
> | Area | Key concepts to review |
> |---|---|
> | Foundations | DevOps lifecycle, CI/CD stages, the agent perceive–plan–act loop, levels of autonomy |
> | AI/ML basics | Supervised vs. unsupervised, features, labels, training vs. inference, overfitting |
> | LLMs & agents | Tool/function calling, RAG, context engineering, guardrails, approval gates |
> | Agent protocols | MCP servers/tools/resources, least-privilege permissions |
> | Agentic CI/CD | Build-failure prediction, test generation, pipeline self-healing, blast-radius limits |
> | Predictive analytics | Change-risk scoring, canary/blue-green with AI gating, time-series forecasting, HPA, KEDA, FinOps |
>
> The exam is **closed-book**, 60 minutes, and combines multiple-choice, short-answer, and one brief scenario. Reviewing your lab notes and the "Key terms" glossaries from each week is the most efficient preparation.

---

## 🧱 Foundations Primer

This primer covers two areas you need before diving into the sessions: **Kubernetes fundamentals** (the platform where most of this week's work happens) and **supervised ML + time-series forecasting** (the technique behind every prediction this week).

### Part A: Kubernetes in Plain Language

If you have used Docker before, you know how to run a container on your laptop. Kubernetes answers the question: *how do you run hundreds of containers, keep them healthy, and scale them up and down, across a cluster of machines — automatically?*

#### The big picture: a cluster

A **Kubernetes cluster** has two kinds of machines:

| Machine type | Role |
|---|---|
| **Control plane (master node)** | The "brain" — decides where to run things, watches for problems, responds to your commands |
| **Worker nodes** | The "muscles" — actually run your application containers |

Think of the control plane as the manager of a restaurant kitchen, and the worker nodes as the line cooks. The manager takes the order (your desired state), assigns tasks to cooks, and keeps replacing a cook who calls in sick with a new one.

#### Core objects

**Pod** — the smallest deployable unit. A pod wraps one (or a few tightly related) containers and gives them a shared IP address and storage. You rarely create pods directly; higher-level objects manage them.

**Deployment** — tells Kubernetes "run three copies of my web-server pod, and if any copy crashes, restart it." A deployment is a *desired-state declaration*: you describe what you want, and Kubernetes continuously reconciles reality to match.

**Service** — a stable network address that routes traffic to whichever pods are currently healthy. Because pod IPs change when pods restart, a Service is the fixed "front door."

**Node** — a physical or virtual machine in the cluster. Each node runs a small agent called the **kubelet** that talks to the control plane and ensures the right pods are running on that node.

#### Key control-plane components (from the Kubernetes deck)

- `kube-apiserver` — the HTTP API gateway; everything talks through it.
- `etcd` — a distributed key-value store holding all cluster state.
- `kube-scheduler` — picks which node to place a new pod on, based on available CPU/memory.
- `kube-controller-manager` — runs background control loops (e.g., the ReplicaSet controller that makes sure you always have three copies of your pod).

#### Horizontal Pod Autoscaler (HPA)

The **Horizontal Pod Autoscaler** is Kubernetes' built-in "scale out / scale in" controller. You configure it like this:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60   # scale up when average CPU > 60%
```

The HPA checks current CPU (or memory, or custom metrics) every 15 seconds and adjusts the number of pod replicas to stay near the target. The catch: *it reacts*. If a traffic spike happens, HPA adds pods only after the spike is already hurting users. This week's Session 8 introduces **predictive autoscaling** — giving the HPA (or a replacement) a forecast of CPU load so it can scale *before* the spike hits.

---

### Part B: Supervised ML and Time-Series Forecasting — From Scratch

You do not need a mathematics background for this week. What you need is a mental model of what "training a model" means and what "a forecast" is.

#### Supervised ML in one paragraph

Imagine you are teaching a new hire to estimate how long a customer support ticket will take to resolve. You show them 1,000 past tickets — each one has a set of facts (ticket type, product area, customer tier) called **features**, and the actual outcome (resolved in 2 hours, 8 hours, etc.) called the **label**. The new hire studies the patterns. Later, when a brand-new ticket arrives (features known, label unknown), they use those patterns to guess the resolution time.

That is supervised ML. You feed a **training dataset** of (features, label) pairs to an algorithm. The algorithm fits a mathematical function — the **model** — that maps features to predicted labels. After training, you hand the model new data and it outputs a prediction.

**Overfitting** is when the model memorizes the training data so precisely that it fails on new data — like a student who memorizes exam answers but cannot solve a slightly different problem.

**Evaluation** is how you check whether the model is actually useful. You hold out a **test set** of examples the model never saw during training, run predictions on it, and measure the error.

#### What is time-series forecasting?

A **time series** is any measurement taken repeatedly over time: CPU utilization every minute, memory used every 5 minutes, number of HTTP requests per second. The values form a sequence ordered by time.

**Time-series forecasting** means predicting future values of that sequence based on its history. Analogy: a weather forecast is time-series forecasting for temperature — today's reading, yesterday's reading, and seasonal patterns combine to predict tomorrow's high.

Common patterns in time series:

| Pattern | Description | Real example |
|---|---|---|
| **Trend** | Steady upward or downward drift | Growing user base → slowly rising baseline CPU |
| **Seasonality** | Repeating cycles (hourly, daily, weekly) | Nightly batch jobs spike CPU every night at 2 AM |
| **Noise** | Random fluctuation | Random HTTP request bursts |
| **Spikes** | Sudden, short-lived peaks | A viral event driving 10x traffic for 20 minutes |

#### Key forecasting algorithms (preview — Session 8 goes deeper)

| Algorithm | Analogy | Best for |
|---|---|---|
| **Moving average** | "Average the last N readings" | Smoothing noise, very short-horizon baselines |
| **Exponential smoothing (ETS)** | Like a moving average but recent points count more | Moderate-horizon, single-season data |
| **Prophet (Facebook/Meta)** | Decomposes into trend + seasonality + holidays automatically | Daily/weekly seasonality, missing data, business calendars |
| **ARIMA / SARIMA** | Statistical model of autocorrelation in the series | Smooth stationary series, short to medium horizon |
| **LSTM / Transformer** | Neural network that learns long-range temporal patterns | Complex multi-variate series; needs lots of data |

This week's lab uses **Prophet** because it is beginner-friendly, handles missing data gracefully, and produces confidence intervals with minimal tuning.

---

## Session 7: Risk Prediction & Deployment Intelligence

**Session length:** ≈ 2 hours (Wednesday evening online)

### Learning Objectives

By the end of Session 7, students will be able to:

1. Explain why some deployments fail and what historical signals predict failure.
2. Define canary and blue-green deployments and describe how an AI gate decides whether to proceed.
3. Describe how an agentic rollback system makes decisions, and what guardrails keep it safe.
4. Identify the features used in a deployment-success scoring model and understand how the model is trained and evaluated.
5. Articulate the data-labeling challenge in real-world DevOps ML and propose strategies to handle it.

---

### Timed Agenda (≈ 2 hours)

| Time | Block | Duration |
|---|---|---|
| 0:00 | Intro: why deployments fail | 10 min |
| 0:10 | Concept — progressive delivery (canary & blue-green) | 20 min |
| 0:30 | Concept — AI gating: how a model scores a deployment | 20 min |
| 0:50 | Demo — change-risk scoring walkthrough | 15 min |
| 1:05 | Concept — agentic rollback decisions | 15 min |
| 1:20 | Concept — data labeling and evaluation challenges | 15 min |
| 1:35 | Discussion + case questions | 20 min |
| 1:55 | Key terms recap | 5 min |

*Trim discussion to 10 min if the demo runs long.*

---

### Concept Explanations

#### 1. Why do deployments fail?

Every software deployment carries risk. A change that works on a developer's laptop may interact badly with production data volumes, network latency, or a dependency that changed since last week. Common causes of deployment failures:

- Bugs introduced by the change itself (logic errors, regressions).
- Configuration drift — the production environment differs from staging in a subtle way.
- Dependency issues — a downstream service changed its API.
- Insufficient capacity — the new version uses more memory than the old one and triggers OOM kills.
- Human error in deployment procedures.

The problem with catching failures *after* the full rollout is that all users are affected. **Progressive delivery** is the practice of rolling a change out to a small slice of users first, measuring what happens, and only widening the rollout if metrics look healthy.

#### 2. Canary Deployments

The name comes from the old mining practice of carrying a canary into a mine — if the canary died, miners knew the air was toxic before they breathed it. In software, a **canary deployment** works like this:

1. Your current version (**stable**) serves 100% of traffic.
2. You deploy the new version (**canary**) and route, say, 5% of requests to it.
3. You monitor error rates, latency, and business metrics for both versions side-by-side.
4. If the canary looks healthy, you gradually increase its traffic share (5% → 25% → 50% → 100%).
5. If the canary shows degraded metrics, you route all traffic back to stable and investigate.

Tools like **Argo Rollouts**, **Flagger**, and **Spinnaker** automate this traffic shifting. The AI layer adds an automated decision engine that checks whether to advance or abort, rather than requiring a human to watch dashboards.

#### 3. Blue-Green Deployments

A **blue-green deployment** maintains two complete, identical environments called *blue* (current live) and *green* (new version):

1. Blue is live; green is idle or staging.
2. You deploy the new version to green and run any smoke tests.
3. You flip the load balancer (or DNS) to send all traffic to green instantly.
4. Blue stays up for a few minutes as an instant rollback target; if green fails, flip back.
5. Once green is confirmed healthy, retire (or repurpose) blue.

The trade-off versus canary: blue-green is faster to switch but exposes all users simultaneously. It is lower risk than a straight deploy because rollback is a switch flip, but higher risk than a gradual canary.

| | Canary | Blue-Green |
|---|---|---|
| Rollout speed | Gradual (minutes to hours) | Instant (milliseconds) |
| Blast radius on failure | Small (only canary %) | All users |
| Rollback speed | Gradual (reroute traffic) | Instant (flip switch) |
| Infrastructure cost | Low (canary is small) | Higher (two full environments) |
| Best for | High-traffic services, risk-averse | Services needing zero-downtime cutover |

#### 4. AI Gating: Scoring a Deployment

Manually watching canary metrics is tedious and error-prone. An **AI gate** is a model (or agent) that watches the metrics automatically and makes — or recommends — the advance/abort decision.

A simple ML-based gate works like this:

1. **Features** (inputs the model sees):
   - Error-rate delta between canary and stable
   - P99 latency delta
   - CPU and memory increase
   - Recent change volume (number of files changed, lines added/deleted)
   - Time of day / day of week
   - Number of dependent services
   - Historical fail rate for this service or team
   - Whether the change touched security-sensitive files

2. **Label** (what was true in historical data):
   - Did this deployment eventually succeed (1) or require rollback/hotfix within 24 hours (0)?

3. **Training:** Feed historical deployment records with these features and labels to a gradient-boosted tree classifier (e.g., XGBoost) or a logistic regression. The model learns which combinations of features predict failure.

4. **Inference:** When a new canary has been running for 15 minutes, compute its current features and pass them to the model. The model outputs a probability, e.g., "78% chance this deployment is healthy." If it falls below a threshold (e.g., 70%), the gate recommends abort.

5. **Autonomy dial:** The gate can be:
   - *Human-in-the-loop* — posts a recommendation to Slack, a human approves.
   - *Human-on-the-loop* — automatically aborts unless a human overrides within 5 minutes.
   - *Autonomous* — aborts immediately, notifies on-call after the fact.

#### 5. Agentic Rollback Decisions

When an AI gate decides a deployment is failing, something must act. An **agentic rollback system** is an AI agent that:

1. **Perceives:** polls metrics (error rate, latency, saturation) via a metrics API (Prometheus, Datadog).
2. **Reasons:** evaluates whether the degradation is caused by the new deployment vs. an unrelated incident (e.g., a database going down). This context-check is critical — you don't want to rollback a healthy deployment because a downstream service is flaky.
3. **Acts (with guardrail):** if confident the deployment is the cause, triggers rollback via the deployment API. If unsure, escalates to a human and provides a summary.
4. **Observes:** confirms the rollback succeeded and metrics returned to baseline.

The key guardrail is the **blast-radius check** from Week 3: the agent should only act if (a) confidence is above a threshold and (b) no other automated system is already acting on the same incident (race-condition prevention).

An example agent tool-call sequence:

```
[Agent] Call tool: get_metrics(service="checkout", window="15m")
  → error_rate=4.2%, p99_latency=820ms, baseline_error=0.3%, baseline_p99=210ms

[Agent] Call tool: check_related_incidents()
  → no open incidents affecting checkout's dependencies

[Agent] Reasoning: error_rate increased 14x, p99 increased 4x. No external cause.
  Confidence: 0.91. Threshold: 0.80. Action: rollback.

[Agent] Call tool: trigger_rollback(deployment="checkout-v2.3.1", reason="auto: error_rate spike")
  → rollback initiated, ETA 45 seconds

[Agent] Call tool: notify_oncall(summary="Rolled back checkout-v2.3.1 due to 14x error-rate spike. Monitoring recovery.")
```

This is a *human-on-the-loop* design — the agent acts, but notifies a human who can reverse the action if needed.

#### 6. ML Models for Change-Risk Scoring

A **change-risk score** is a number (e.g., 0–100) assigned to a proposed change *before* deployment, based on the change's characteristics. The goal is to flag high-risk changes for extra review or staged rollout.

DORA research ([https://dora.dev](https://dora.dev)) has shown that certain signals reliably predict whether a change will cause a deployment failure:

- **Large diffs:** changes touching many files or many lines of code are statistically riskier.
- **Modified test coverage:** changes with decreased test coverage are riskier.
- **Friday afternoon deployments:** empirically, deployments on Friday evenings have higher rollback rates.
- **Time since last deployment:** longer gaps between deployments correlate with more drift.
- **Service coupling:** services with many upstream/downstream dependencies are riskier to change.

You can train a gradient-boosted classifier on your organization's historical deployment data (features above, label = "caused incident: yes/no") and use it to score every new pull request or deployment request.

#### 7. Data Labeling and Evaluation Challenges

Building a deployment-risk model sounds straightforward until you try to gather the training data. Real challenges include:

**Label noise.** How do you define "failed deployment"? A rollback? An incident? A user complaint? Teams use different definitions, making historical labels inconsistent.

**Survivorship bias.** If your team has been doing canary deployments for years, you never see what would have happened with a full bad rollout. Your "failures" are only the ones that got through the safety net — an unrepresentative sample.

**Class imbalance.** In a healthy team, 95% of deployments succeed. A naive model can achieve 95% accuracy by always predicting "success" — which is useless. You must use balanced sampling, class-weighted loss, or metrics like **precision/recall** and **F1 score** instead of raw accuracy.

**Concept drift.** The system changes over time — a model trained on last year's deployments may not reflect today's architecture. Models need retraining on a rolling window of recent data.

**Evaluation strategy.** Because deployment data is time-ordered, you must use **temporal cross-validation**: train on the first 80% of time, test on the last 20%. Randomly shuffling train/test splits would leak future information into the training set and produce overly optimistic accuracy numbers.

---

### Worked Example: Building a Simple Change-Risk Scorer

Scenario: your team has 18 months of deployment history — 2,400 deployments, 120 of which required rollback. You want a model that flags high-risk deployments before they go to production.

**Step 1: Feature engineering from a deployment event.**

```python
# Each row in your dataset looks like this
deployment = {
    "files_changed": 47,
    "lines_added": 312,
    "lines_deleted": 89,
    "test_coverage_delta": -2.1,   # coverage dropped 2.1%
    "hour_of_day": 16,             # 4 PM
    "day_of_week": 4,              # Friday (0=Monday)
    "num_dependencies": 8,
    "days_since_last_deploy": 12,
    "team_rollback_rate_30d": 0.06,  # 6% rollback rate this team, last 30 days
    "label": 0                     # 0=success, 1=rollback
}
```

**Step 2: Train a classifier.**

```python
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report

# Assume df is a DataFrame with features + 'label' column,
# sorted chronologically
features = [
    "files_changed", "lines_added", "lines_deleted",
    "test_coverage_delta", "hour_of_day", "day_of_week",
    "num_dependencies", "days_since_last_deploy",
    "team_rollback_rate_30d"
]

# Temporal split: train on first 80%, test on last 20%
split_idx = int(len(df) * 0.8)
train, test = df.iloc[:split_idx], df.iloc[split_idx:]

X_train, y_train = train[features], train["label"]
X_test, y_test = test[features], test["label"]

model = GradientBoostingClassifier(
    n_estimators=100,
    max_depth=4,
    class_weight="balanced"   # handle class imbalance
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))
```

**Step 3: Interpret and use the score.**

```python
# Score a new deployment before it goes live
new_deploy = pd.DataFrame([{
    "files_changed": 82,
    "lines_added": 640,
    "lines_deleted": 10,
    "test_coverage_delta": -4.0,
    "hour_of_day": 17,
    "day_of_week": 4,
    "num_dependencies": 11,
    "days_since_last_deploy": 21,
    "team_rollback_rate_30d": 0.09
}])

risk_score = model.predict_proba(new_deploy)[0][1]  # probability of rollback
print(f"Deployment risk score: {risk_score:.2%}")

# Gate logic
if risk_score > 0.5:
    print("HIGH RISK: Recommend staged canary rollout and extra approval.")
elif risk_score > 0.25:
    print("MEDIUM RISK: Recommend canary rollout.")
else:
    print("LOW RISK: Standard deployment.")
```

---

### 💬 Discussion & Case Questions

1. **The Friday deploy:** Your change-risk model flags all Friday-afternoon deployments as high risk because the training data shows higher rollback rates on Fridays. Is this a useful signal, a causal relationship, or a proxy for something else (e.g., end-of-sprint pressure, reduced on-call staffing)? What could go wrong if you enforce a hard no-deploy-on-Friday rule based on this signal?

2. **The blame problem:** If an AI gate automatically rolls back a deployment and later it turns out the problem was an unrelated database issue, how should the postmortem assign responsibility? What organizational and technical changes would reduce this kind of false rollback?

3. **Industry case — Uber:** Uber's engineering blog describes a deployment risk system that considers over 50 features including the author's historical deploy success rate. What are the fairness and psychological implications of scoring *individual engineers* rather than just changes?

4. **Autonomous vs. advisory gates:** For what types of services and organizations does a *fully autonomous* AI rollback make sense? Where should the gate always require human approval? What is the minimum amount of human oversight you would consider acceptable?

5. **The cold-start problem:** You are joining a startup that has zero historical deployment failure data. How would you bootstrap a change-risk model? (Hint: consider public datasets like DORA benchmarks, or heuristic rules while you collect data.)

---

### 🔑 Key Terms — Session 7

| Term | Definition |
|---|---|
| **Progressive delivery** | Strategy of releasing software gradually to a subset of users, measuring impact, and widening only when healthy |
| **Canary deployment** | Routes a small percentage of traffic to a new version; widens or aborts based on metrics |
| **Blue-green deployment** | Runs two identical environments; switches traffic instantly; old environment is rollback target |
| **AI gate** | A model or agent that evaluates deployment health and makes advance/abort decisions |
| **Change-risk score** | A pre-deployment ML-predicted probability that a change will cause an incident |
| **Agentic rollback** | An AI agent that autonomously detects deployment failure and triggers rollback, with guardrails |
| **Feature** | An input variable fed to an ML model |
| **Label** | The known output/outcome used to train a supervised model |
| **Class imbalance** | When one outcome (e.g., "success") occurs far more often than the other; requires special handling |
| **Temporal cross-validation** | Evaluating a time-ordered model by training on past data and testing on future data — never shuffling randomly |
| **Concept drift** | When the real-world patterns a model learned no longer match current reality, degrading performance |
| **DORA metrics** | Four key DevOps metrics from the DORA research program: deployment frequency, lead time, change failure rate, MTTR |

---

### ⚠️ Common Pitfalls — Session 7

- **Using accuracy as your only metric on imbalanced data.** A model that always predicts "success" gets 95% accuracy on a dataset where 95% of deployments succeed — and catches zero failures. Always report precision, recall, and F1 for the minority class.
- **Shuffling time-series data for train/test split.** Randomly splitting deployment records allows future data to leak into training, inflating accuracy. Always split chronologically.
- **Setting the threshold too low.** A gate that fires on any risk > 10% will create "rollback fatigue" — engineers start overriding it constantly, eroding trust. Calibrate thresholds against acceptable false-positive rates.
- **Ignoring the human factor.** Models trained on past behavior encode past team practices. If you recently improved your test suite or deploy process, retrain the model on recent data or it will be systematically miscalibrated.
- **Autonomous rollback without race-condition protection.** If two agents both observe the same alert and both try to roll back simultaneously, you can get conflicting actions. Use distributed locks or a single orchestrator agent.

---

## Session 8: Capacity & Performance Forecasting

**Session length:** ≈ 1.5 hours (Saturday morning onsite)

### Learning Objectives

By the end of Session 8, students will be able to:

1. Explain what FinOps is and why AI-driven forecasting is central to cloud cost control.
2. Identify bottlenecks in microservice performance using resource utilization forecasts.
3. Describe how predictive HPA and KEDA extend Kubernetes autoscaling beyond reactive thresholds.
4. Explain the Prophet and ARIMA forecasting algorithms at an intuitive level.
5. Describe how an agent translates a forecast into a concrete scaling policy recommendation.

---

### Timed Agenda (≈ 1.5 hours)

| Time | Block | Duration |
|---|---|---|
| 0:00 | Intro: the cost of under- and over-provisioning | 10 min |
| 0:10 | Concept — FinOps and AI-driven cost optimization | 15 min |
| 0:25 | Concept — time-series forecasting algorithms | 20 min |
| 0:45 | Concept — predictive HPA and KEDA | 15 min |
| 1:00 | Demo — Prophet forecast → scaling decision | 15 min |
| 1:15 | Discussion + case questions | 10 min |
| 1:25 | Key terms recap | 5 min |

---

### Concept Explanations

#### 1. The Cost of Getting Capacity Wrong

Cloud infrastructure is pay-per-use. Every pod you run costs money. This creates two failure modes:

- **Under-provisioning:** not enough pods → service gets slow or unavailable → users complain → revenue lost. In 2021, Slack reported a 2-hour degradation caused by a capacity shortfall during an unexpected traffic spike.
- **Over-provisioning:** too many pods → waste money on idle compute. Studies of enterprise cloud bills regularly find 30–40% of provisioned capacity sits idle during off-peak hours.

The challenge is that demand fluctuates: daily cycles (lunch-hour traffic spikes), weekly cycles (Monday morning email opens), seasonal cycles (holiday shopping), and unpredictable events (viral posts, news mentions). Manual capacity planning cannot keep up.

**AI-driven forecasting** addresses both failure modes: predict demand far enough in advance to scale up before users feel pain, and scale down when demand drops to avoid waste.

#### 2. FinOps and AI-Driven Cost Optimization

**FinOps** (Financial Operations) is the practice of managing cloud costs with the same discipline as any other operational metric. The FinOps Foundation ([https://www.finops.org](https://www.finops.org)) defines three phases:

| Phase | What you do |
|---|---|
| **Inform** | Measure and attribute cloud spend by service, team, and feature |
| **Optimize** | Find and act on savings opportunities (right-sizing, reserved instances, spot instances) |
| **Operate** | Embed cost awareness into engineering culture and workflows |

AI contributes to FinOps in several ways:

- **Anomaly detection on the cost time series** — flag when a service's spend suddenly doubles.
- **Right-sizing recommendations** — compare a pod's requested CPU/memory against its actual usage histogram; if it consistently uses only 20% of its request, recommend reducing the request.
- **Spot/preemptible instance scheduling** — predict which workloads can tolerate interruption and automatically schedule them on cheaper spot instances.
- **Predictive autoscaling** — the main topic of this session: scale out just-in-time and scale in immediately after demand drops, minimizing both latency and idle cost simultaneously.

#### 3. Identifying Bottlenecks in Microservices

Before you can forecast and scale a bottleneck, you need to find it. In a microservice architecture with dozens of services, a performance issue in one service can manifest as slowness in an entirely different service that depends on it.

**Bottleneck identification** using resource metrics:

1. Collect per-pod CPU, memory, and network utilization time series for all services.
2. Correlate with latency/error-rate time series. If service A's latency spikes every time service B's CPU hits 80%, B is probably the bottleneck.
3. Use dependency maps (from distributed tracing — covered in Week 5) to understand which services depend on B.
4. Forecast B's CPU usage forward: if it is on a trend to hit 80% in two hours, scale B now.

Forecasting models can be applied per-service, per-pod, or at the cluster level. Per-service forecasting is more targeted; cluster-level forecasting is simpler and better for overall node scaling.

#### 4. Time-Series Forecasting Algorithms — Deeper Dive

##### Moving Average Baseline

The simplest forecast: the prediction for the next time step is the average of the last *N* observations.

```
predicted(t+1) = mean(actual[t-N+1 : t])
```

Good for: establishing a sanity-check baseline. Not good for: trends (it always lags behind growth) or seasonality (it treats all time windows identically).

##### Prophet (Meta / Facebook Open Source)

Prophet ([https://facebook.github.io/prophet/](https://facebook.github.io/prophet/)) is designed for business time series with daily/weekly/yearly seasonality, missing data, and holiday effects. It decomposes the series as:

```
y(t) = trend(t) + seasonality(t) + holidays(t) + noise(t)
```

- **Trend** can be linear or logistic (for series with a natural ceiling, like "% CPU used").
- **Seasonality** is modeled using Fourier series (a way of representing repeating patterns as sums of sine and cosine waves — you don't need to understand the math, just that it automatically captures daily and weekly cycles).
- **Holidays** lets you add known events (e.g., product launch dates, year-end sales) that cause irregular spikes.

Prophet is accessible to beginners because it requires minimal configuration and its output includes **uncertainty intervals** — it tells you not just "CPU will be 62%" but "CPU will be between 55% and 70% with 80% confidence."

##### ARIMA / SARIMA

**ARIMA** (AutoRegressive Integrated Moving Average) is a classical statistical model. Think of it as answering: "how much does today's value depend on yesterday's, the day before's, etc., and on past prediction errors?"

- **AR** (AutoRegressive): today's value is a weighted sum of past values.
- **I** (Integrated): the series has been "differenced" to remove trends and make it stationary.
- **MA** (Moving Average): today's value also depends on past prediction errors.

**SARIMA** adds a seasonal component. ARIMA/SARIMA requires the series to be roughly stationary (no strong trend) and works best for short to medium horizons. It requires more statistical expertise to tune than Prophet.

##### LSTM (Long Short-Term Memory Neural Network)

An LSTM is a type of recurrent neural network designed to remember patterns across long time spans. It can learn complex, multi-variate dependencies — e.g., "CPU spikes whenever memory is above 70% AND it's a weekday morning."

LSTMs are powerful but require:
- Much more training data (thousands of data points vs. hundreds for Prophet).
- More hyperparameter tuning.
- GPU or longer CPU training time.

For most Kubernetes autoscaling use cases, Prophet or SARIMA is sufficient and far easier to deploy.

#### 5. Predictive HPA and KEDA

##### The Problem with Reactive HPA

Standard Kubernetes HPA is **reactive**: it adds pods *after* CPU exceeds the threshold. The lag between "threshold crossed" and "new pods are fully running and receiving traffic" is typically 60–120 seconds (time to schedule pod + container startup + readiness probe). For a sharp traffic spike, that lag means real user-facing impact.

##### Predictive HPA

**Predictive HPA** feeds a time-series forecast into the scaling decision *before* the load arrives:

1. A forecasting model (e.g., Prophet trained on CPU history) predicts CPU utilization for the next 5–15 minutes.
2. A controller converts the predicted CPU into a required replica count: `desired_replicas = ceil(predicted_cpu / target_cpu_per_replica)`.
3. Kubernetes scales to `desired_replicas` now, before the load materializes.

The Kubernetes community has implemented this via custom controllers (e.g., the **Predictive Horizontal Pod Autoscaler** project) and via integration with KEDA.

##### KEDA (Kubernetes Event-Driven Autoscaling)

**KEDA** ([https://keda.sh](https://keda.sh)) extends Kubernetes HPA to scale on *external* metrics — not just CPU/memory, but:

- Queue length (scale up when a Kafka topic has 1,000+ messages queued)
- Custom Prometheus metrics
- Cloud provider metrics (AWS SQS queue depth, Azure Service Bus, GCP Pub/Sub)
- Cron-based schedule (scale up every day at 8 AM, scale down at 11 PM)

For predictive autoscaling, KEDA is particularly powerful because you can:
1. Emit your forecast as a custom Prometheus metric (e.g., `predicted_cpu_next_15m`).
2. Configure a KEDA `ScaledObject` that scales based on that metric.
3. The result: pods scale up based on the *predicted* future load, not the current actual load.

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: my-app-predictive
spec:
  scaleTargetRef:
    name: my-app
  minReplicaCount: 2
  maxReplicaCount: 50
  triggers:
  - type: prometheus
    metadata:
      serverAddress: http://prometheus:9090
      metricName: predicted_cpu_next_15m
      threshold: "60"    # scale up when predicted CPU > 60%
      query: predicted_cpu_next_15m{service="my-app"}
  - type: cron
    metadata:
      timezone: America/Los_Angeles
      start: "0 7 * * 1-5"    # Monday–Friday 7 AM
      end: "0 21 * * 1-5"     # Monday–Friday 9 PM
      desiredReplicas: "10"   # minimum 10 replicas during business hours
```

This KEDA config combines a forecast-driven trigger with a cron-based floor — a robust real-world pattern.

#### 6. Agents That Recommend and Apply Scaling Policies

Beyond static thresholds, an **agentic scaling advisor** can reason about the full context of a scaling decision:

- "Should I scale horizontally (more pods) or vertically (bigger pods)?"
- "Is it cheaper to scale out using spot instances (10× more units at 1/3 the cost) or on-demand?"
- "Is the bottleneck in this service or in a dependency — will scaling this service actually help?"

An agent connects to multiple tools:

```
[Agent] Call tool: get_forecast(service="payment-api", horizon="30m")
  → predicted_cpu: 78% in 15 min, 91% in 30 min (confidence: high)

[Agent] Call tool: get_cost_estimate(scale_out=5, instance_type="on_demand")
  → $2.40/hour additional

[Agent] Call tool: get_cost_estimate(scale_out=5, instance_type="spot")
  → $0.70/hour additional (3.4x cheaper, ~10% interruption risk)

[Agent] Call tool: check_spot_availability(region="us-west-2")
  → availability: 87% in last 7 days, currently: available

[Agent] Recommendation: Scale payment-api from 8 to 13 replicas using spot instances.
  Estimated savings vs. on-demand: $1.70/hour. Rollback plan: switch to on-demand
  if spot instances are reclaimed.

[Agent] Awaiting human approval before applying...
```

This is a **human-in-the-loop** design — the agent gathers data, reasons about trade-offs, and presents a recommendation, but a human (or an auto-approval policy) must confirm before actual infrastructure change.

---

### Worked Example / Demo: Forecasting CPU with Prophet

This demo shows the full loop: train a Prophet model on historical CPU data, generate a 1-hour forecast, and translate it into a scaling recommendation.

**Setup:**

```bash
pip install prophet pandas matplotlib scikit-learn
```

**Step 1: Load and inspect the data.**

```python
import pandas as pd
import matplotlib.pyplot as plt
from prophet import Prophet

# Assume csv with columns: timestamp (ISO8601), cpu_utilization (0-100)
df = pd.read_csv("cpu_metrics.csv", parse_dates=["timestamp"])
df = df.rename(columns={"timestamp": "ds", "cpu_utilization": "y"})

print(df.head())
# ds                  y
# 2025-10-01 00:00   22.3
# 2025-10-01 00:05   23.1
# ...

# Quick plot — always look at your data first
df.set_index("ds")["y"].plot(figsize=(14, 4), title="CPU Utilization (%)")
plt.ylabel("CPU %")
plt.show()
```

**Step 2: Train the Prophet model.**

```python
# Prophet expects columns named exactly 'ds' (datetime) and 'y' (value)
model = Prophet(
    daily_seasonality=True,
    weekly_seasonality=True,
    yearly_seasonality=False,   # we only have a few weeks of data
    interval_width=0.80         # 80% confidence interval
)
model.fit(df)
print("Model trained successfully.")
```

**Step 3: Generate a 1-hour forecast.**

```python
# Create a dataframe of future timestamps at 5-minute intervals
future = model.make_future_dataframe(periods=12, freq="5T")   # 12 * 5 min = 60 min
forecast = model.predict(future)

# Key columns in forecast:
# ds = timestamp, yhat = prediction, yhat_lower = lower CI, yhat_upper = upper CI
print(forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(12))

# Plot
fig = model.plot(forecast)
plt.title("CPU Utilization Forecast (next 60 min)")
plt.axhline(y=70, color="orange", linestyle="--", label="Scale-up threshold")
plt.axhline(y=40, color="green", linestyle="--", label="Scale-down threshold")
plt.legend()
plt.show()
```

**Step 4: Translate forecast into a scaling decision.**

```python
# Get the maximum predicted CPU in the next 30 minutes
now = pd.Timestamp.now()
horizon = now + pd.Timedelta("30min")
upcoming = forecast[(forecast["ds"] > now) & (forecast["ds"] <= horizon)]
max_predicted_cpu = upcoming["yhat_upper"].max()  # use upper CI for safety

print(f"Max predicted CPU in next 30 min: {max_predicted_cpu:.1f}%")

# Current cluster state (in practice, query from Kubernetes API)
current_replicas = 5
target_cpu_per_replica = 60  # target CPU % per pod

# Calculate required replicas
# If max_predicted_cpu = 85% and target is 60%, we need ceil(5 * 85/60) = 8 replicas
required_replicas = max(
    2,  # minimum
    min(
        50,  # maximum
        -(-current_replicas * max_predicted_cpu // target_cpu_per_replica)  # ceiling division
    )
)

import math
required_replicas = max(2, min(50, math.ceil(current_replicas * max_predicted_cpu / target_cpu_per_replica)))

print(f"Current replicas: {current_replicas}")
print(f"Recommended replicas: {required_replicas}")

if required_replicas > current_replicas:
    print(f"ACTION: Scale UP by {required_replicas - current_replicas} replicas (pre-emptive)")
elif required_replicas < current_replicas:
    print(f"ACTION: Scale DOWN by {current_replicas - required_replicas} replicas")
else:
    print("ACTION: No change needed")
```

**Sample output:**

```
Max predicted CPU in next 30 min: 83.4%
Current replicas: 5
Recommended replicas: 7
ACTION: Scale UP by 2 replicas (pre-emptive)
```

**Step 5: Evaluate the forecast on held-out data.**

```python
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

# Hold out last 24 hours for evaluation
cutoff = df["ds"].max() - pd.Timedelta("24h")
train_df = df[df["ds"] < cutoff]
test_df = df[df["ds"] >= cutoff]

eval_model = Prophet(daily_seasonality=True, weekly_seasonality=True, interval_width=0.80)
eval_model.fit(train_df)

future_eval = eval_model.make_future_dataframe(periods=len(test_df), freq="5T")
forecast_eval = eval_model.predict(future_eval)
predicted = forecast_eval[forecast_eval["ds"].isin(test_df["ds"])]["yhat"].values
actual = test_df["y"].values

print(f"MAE:  {mean_absolute_error(actual, predicted):.2f}% CPU")
print(f"MAPE: {mean_absolute_percentage_error(actual, predicted)*100:.1f}%")
```

A MAPE under 10% on CPU forecasting is generally good enough to make reliable scaling decisions.

---

### 💬 Discussion & Case Questions

1. **FinOps trade-off:** An autoscaling policy keeps your service always at 40% average CPU (very comfortable). Your FinOps team says you're over-provisioned and requests you raise the target to 70%. Your SRE says 70% leaves no headroom for spikes. How do you resolve this? What data would you collect to make a principled decision?

2. **Spot instance risk:** The agent demo above recommended spot instances to save costs, accepting a ~10% interruption risk. For which services (payment processing, background jobs, ML training, user-facing dashboards) would you accept spot, and for which would you refuse? Where do you draw the line?

3. **Industry case — Netflix:** Netflix's "Scryer" system forecasts AWS EC2 demand 24 hours in advance and pre-purchases reserved capacity accordingly, saving millions annually. What are the risks of a 24-hour forward forecast vs. a 30-minute forecast? How would you manage forecast errors?

4. **KEDA cron vs. forecast:** A cron-based scale trigger (scale up at 8 AM, scale down at 10 PM) is simpler than a Prophet forecast and often works well. When would you prefer the ML-based forecast over the cron? When would cron be sufficient?

5. **The new workload problem:** You are launching a brand-new microservice with no historical data. You cannot train a forecasting model. What strategies would you use to set initial capacity and autoscaling parameters?

---

### 🔑 Key Terms — Session 8

| Term | Definition |
|---|---|
| **FinOps** | The practice of applying financial accountability to cloud costs; cloud spend is treated as an operational metric |
| **Right-sizing** | Matching pod/VM resource requests to actual usage to eliminate waste |
| **Predictive HPA** | Extends Kubernetes HPA by scaling based on a forecast rather than current observed metrics |
| **KEDA** | Kubernetes Event-Driven Autoscaling; scales pods based on external metrics (queues, custom metrics, cron) |
| **Prophet** | Meta's open-source time-series forecasting library; decomposes series into trend, seasonality, and holiday effects |
| **ARIMA/SARIMA** | Classical statistical time-series model; uses past values and prediction errors to forecast future values |
| **MAE** | Mean Absolute Error — average absolute difference between predicted and actual values |
| **MAPE** | Mean Absolute Percentage Error — MAE expressed as a percentage of actual values; useful for comparing across scales |
| **Confidence interval** | A range within which the true future value is expected to fall with a stated probability (e.g., 80%) |
| **Bottleneck** | The component in a system whose resource saturation most constrains overall throughput |
| **Spot / preemptible instance** | Cloud VM available at deep discount but can be terminated with short notice when capacity is needed by on-demand customers |
| **Vertical scaling** | Increasing the size (CPU/memory) of a single pod or node |
| **Horizontal scaling** | Increasing the number of pod replicas; typically preferred in Kubernetes |

---

### ⚠️ Common Pitfalls — Session 8

- **Forecasting without seasonality decomposition.** If your data has strong daily patterns but your model doesn't account for them, your forecasts will be systematically wrong during peak and off-peak hours. Always plot your data and look for repeating patterns before choosing a model.
- **Scaling too aggressively based on the upper confidence interval.** Using the 95th-percentile forecast to set replica counts will cause chronic over-provisioning. Match the confidence level to the cost of under- vs. over-provisioning for each service.
- **Ignoring the scale-down path.** Teams invest effort in "scale up fast" but forget "scale down safely." Scaling down too aggressively (removing pods while they still have active connections) causes errors. Use connection draining and a cooldown period.
- **Training on a bad dataset.** If your historical CPU data includes periods when the cluster was artificially capped (e.g., a misconfigured limit), the model will learn the wrong baseline. Always inspect your training data for anomalies before fitting.
- **Treating the forecast as ground truth.** No forecast is perfect. Build in safety margins and retain manual override capabilities. An agent that blindly trusts a forecast and ignores real-time signals will fail badly during unexpected events (viral traffic, DDoS, major product launches).
- **Forgetting to retrain.** A Prophet model trained six months ago on a different traffic pattern will drift. Schedule periodic retraining (e.g., weekly or monthly) or trigger retraining when forecast error exceeds a threshold.

---

## Recap & Looking Ahead

### What you learned this week

This week you moved from *reactive* to *predictive* operations. The central insight is that historical data — deployment records, CPU time series, team rollback rates — contains patterns that predict future problems. Machine learning lets you extract those patterns and act on them before users experience impact.

Key takeaways:

- **Deployment risk is quantifiable.** Change-risk scores and AI-gated canary deployments reduce the blast radius of bad changes without slowing down engineering velocity when used thoughtfully.
- **Autoscaling lag is a solvable problem.** Time-series forecasting (especially Prophet for most use cases) gives you a 15–30 minute preview of demand, enough time to scale preemptively.
- **Cost and reliability are two sides of the same coin.** FinOps is not about cutting costs at the expense of performance; it is about eliminating *waste* (idle over-provisioned resources) while meeting performance targets. Predictive autoscaling often *improves* both simultaneously.
- **Agents need forecasts to make smart decisions.** The agentic rollback system from Session 7 and the scaling advisor from Session 8 are only as good as the signals they consume. Accurate forecasting is the foundation for autonomous action.

### Looking ahead: Week 5

[Week 5](../week-05/week-05-notes.md) takes a different angle on the same operational data. Instead of predicting the future, you will learn to *detect anomalies in the present*:

- **AI-driven anomaly detection** on logs, metrics, and traces.
- **Unsupervised ML** (clustering, isolation forests) for detecting unusual patterns without labeled failure data.
- **LLM-based log analysis** — using an agent to read and summarize log streams.
- **Root-cause analysis (RCA) agents** that investigate an incident by correlating signals across the observability stack.
- **Observability for agents themselves** — using OpenTelemetry GenAI semantic conventions to trace your AI agent's actions, token costs, and latency.

The forecasting and anomaly-detection capabilities of Weeks 4–5 together provide the intelligence layer that Week 6's autonomous incident response system will depend on.

---

## References

- [v2 Syllabus](../../syllabus/CSE636_Syllabus_v2.md) — see Week 4 entries for session details and lab/assignment descriptions.
- [Kubernetes deck](../../slides/Kubernetes.md) — pod, deployment, node, and HPA concepts used throughout this week.
- [Week 3: Agentic CI/CD Pipelines](../week-03/week-03-notes.md) — approval gates, pipeline agents, blast-radius limits (prerequisites for Session 7).
- [Week 5: Intelligent Monitoring, Observability & Agent Telemetry](../week-05/week-05-notes.md) — anomaly detection and RCA (where this week's forecasts feed in).

### External resources

| Resource | URL | Relevance |
|---|---|---|
| **KEDA** — Kubernetes Event-Driven Autoscaling | https://keda.sh | Predictive/event-driven HPA extension |
| **DORA Research** — DevOps metrics and deployment risk | https://dora.dev | Change failure rate, deployment frequency; data for risk scoring |
| **Prophet** — Facebook/Meta open-source forecasting | https://facebook.github.io/prophet/ | Library used in this week's lab |
| **FinOps Foundation** | https://www.finops.org | FinOps principles, maturity model, cost optimization playbooks |
| **Alibaba Cluster Trace** — public cloud workload dataset | https://github.com/alibaba/clusterdata | Real CPU/memory time-series data for lab experiments |
| **Argo Rollouts** — progressive delivery controller | https://argoproj.github.io/rollouts/ | Canary and blue-green deployments with analysis gates |
| **Flagger** — GitOps-driven progressive delivery | https://flagger.app | KEDA + Argo + Prometheus integration for AI-gated rollouts |
| **kube-prometheus-stack** (Helm chart) | https://github.com/prometheus-community/helm-charts | Easy Prometheus + Grafana setup for lab metric emission |
| **Anthropic — Building Effective Agents** | https://www.anthropic.com/engineering/building-effective-agents | Agentic reasoning loops and guardrails pattern (relevant to rollback and scaling agents) |
| **OpenTelemetry GenAI conventions** | https://opentelemetry.io/docs/specs/semconv/gen-ai/ | Observing agents in production (preview of Week 5) |
