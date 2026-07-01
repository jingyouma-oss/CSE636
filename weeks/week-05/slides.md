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

# Week 5: Intelligent Monitoring, Observability & Agent Telemetry
## See everything — including the AI agents themselves
### CSE636 — DevOps with AI

Qingsong Zhang, Ph. D.

---

## Where Week 5 Sits

- Weeks 1–3: you built **pipelines**
- Week 4: you taught the system to **predict** the future
- **Week 5: you give the system eyes** — watch now, detect wrong, find root cause
- Critically: observe the **AI agents** doing the watching
- Week 6: agents *act* on what they see

| | |
|---|---|
| **Prerequisites** | Week 4 + the agent loop from Week 1 |
| **Time budget** | 2 sessions: ~2 hrs + ~1.5 hrs |
| **By the end** | Three pillars · unsupervised anomaly detection · agentic RCA · observe agents with OTel GenAI |
| **You'll build** | Isolation-forest detector + OTel-instrumented agent (`project/anomaly/`) |

---

## Monitoring vs. Observability

Car dashboard analogy: the speedometer is **monitoring**; reading fault codes to find *why* the engine light is on is **observability**.

| | Monitoring | Observability |
|---|---|---|
| **Question** | "Is it healthy?" | "Why is it behaving this way?" |
| **You need** | Dashboards, thresholds, alerts | Rich, queryable internal data |
| **Reactive to** | Known failure modes | Unknown / unexpected modes |
| **Tools** | Prometheus + Grafana | OpenTelemetry, tracing, structured logs |

Observability **enhances** monitoring — it doesn't replace it.

---

## The Three Pillars

```
 METRICS            LOGS               TRACES
 "vital signs"      "the diary"        "journey map"
 numbers/time       timestamped        one request,
 CPU, err, p99      events + errors    all hops (spans)
 cheap & fast       forensic detail    + timing
 "Is it healthy?"   "What happened?"   "Where did it fail?"
```

**Detective story:** a metric alert fires → read **logs** for the error text → pull a **trace** to see which call failed. OpenTelemetry instruments all three, vendor-neutral.

- **Logs:** structure as JSON, ship to Elasticsearch / Splunk.
- **Metrics:** histograms, gauges, counters. Prometheus scrapes; Grafana draws. An **SLO** targets a metric ("99.9% under 200 ms"); breach → **alert**.
- **Traces:** one request across services; each hop = a **span** (start, duration, attributes). Export to Jaeger, Datadog, Honeycomb…

---

## Quiz: Which Pillar?

**Q:** A metric alert says "checkout error rate jumped to 5%." Which pillar tells you *exactly what* failed, and which tells you *where in the path*?

<br>

- **Logs** → *what*: the specific error messages / stack traces
- **Traces** → *where*: follow one failing request to the exact span
- The **metric** was just the smoke alarm that started the investigation

---

## Unsupervised Learning — Intuition

- **Supervised** = labelled examples ("normal" / "anomaly"). Labelled anomalies are rare and expensive.
- **Unsupervised** = finds patterns with **no labels** — learns what "normal" looks like on its own.

| Technique | Intuition |
|---|---|
| **Clustering** (k-means, DBSCAN) | Rice grains clump; points outside clumps = outliers |
| **Isolation Forest** | Random cuts to isolate a point; anomalies isolate in *few* cuts |

Key win for ops: novel failures are, by definition, things you've never labelled.

---

<!-- _class: lead invert -->

# Session 9
## AI-Driven Anomaly Detection
### ~2 hours

---

## Session 9 — Learning Objectives

1. Explain the three pillars and how anomaly detection applies to each.
2. Distinguish supervised vs. unsupervised — and when to use each.
3. Apply isolation forests and clustering to a log/metric dataset.
4. Contrast real-time (streaming) vs. batch detection.
5. Describe the noise / false-positive problem + mitigations.
6. Explain why AI agents must be observed (OTel GenAI conventions).

---

## Why Not Just Thresholds?

An anomaly deviates significantly from learned "normal":
- Sudden spike in HTTP 500s
- Long tail on DB latency
- A log template never seen before
- A trace call 10× its usual time

**Threshold problems:**
- A human must pick the number in advance (varies by service, time, season)
- They miss *relative* anomalies — 75% CPU is fine, unless it usually idles at 5%

ML learns the baseline from the data, not from a hand-crafted number.

---

## Applying ML to Each Pillar

| Pillar | Feed the model | Detects |
|---|---|---|
| **Metrics** | Time series of numeric values | Spikes, dips, trend & seasonal deviations |
| **Logs** | Parsed templates or embeddings | Rare templates, error bursts, new patterns |
| **Traces** | Span-duration vectors, dep graphs | Slow calls, unusual paths, missing spans |

**Log pipeline:** Parse → Drain to a template (Drain3) → Vectorize → Score.

---

## Isolation Forest in Code

```python
from sklearn.ensemble import IsolationForest
import pandas as pd

df = pd.read_csv("metrics_sample.csv", parse_dates=["timestamp"])
features = df[["cpu_pct", "mem_pct", "req_per_sec", "error_rate"]]

# contamination = expected fraction of anomalies
model = IsolationForest(n_estimators=100, contamination=0.02, random_state=42)
model.fit(features)

df["anomaly_score"] = model.decision_function(features)  # lower = more anomalous
df["is_anomaly"]    = model.predict(features)            # -1 = anomaly, 1 = normal

anomalies = df[df["is_anomaly"] == -1]
```

- `contamination`: start 0.01–0.05 · `n_estimators`: 100–200 usually enough

---

## Clustering with DBSCAN

```python
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN

scaler = StandardScaler()
X_scaled = scaler.fit_transform(features)

# eps = neighborhood radius; min_samples = points to form a core
db = DBSCAN(eps=0.5, min_samples=10)
labels = db.fit_predict(X_scaled)

df["cluster"] = labels
outliers = df[df["cluster"] == -1]   # DBSCAN labels outliers as -1
```

Useful when anomalies are isolated points and normal data forms dense clusters.

---

## LLM-Based Log Anomaly Detection

```python
def detect_log_anomalies(log_window: str) -> str:
    message = client.messages.create(
        model="claude-opus-4-5", max_tokens=512,
        messages=[{"role": "user", "content": (
            "You are an SRE reviewing application logs. Identify any lines that "
            "suggest an error, unusual behaviour, or security concern... "
            f"LOG WINDOW:\n{log_window}")}])
    return message.content[0].text
```

| Use an LLM when… | Use a statistical model when… |
|---|---|
| *Semantic* anomalies in NL logs ("admin login from odd IP at 3 AM") | Numeric time-series; faster & cheaper |

**In practice: combine** — stats for streaming, LLM for the top-N flagged windows.

---

## Real-Time vs. Batch

| | Real-Time (Streaming) | Batch |
|---|---|---|
| **Timing** | Score as data arrives | Periodic (15 min, hourly, nightly) |
| **Use for** | Cascade failures, auto-remediation, sub-min SLOs | Slow trends, cross-service correlation, retraining |
| **Context** | Little per decision → sliding windows | More context, heavier models |

Streaming platforms: Kafka + Flink, Kinesis + Lambda, GCP Dataflow.

---

## The Noise & False-Positive Problem

Hundreds of services × 1% false-positive rate = dozens of spurious alerts/day → **alert fatigue**.

| Strategy | How it works |
|---|---|
| **Dynamic baselines** | Adjust "normal" as the system changes |
| **Minimum duration** | Fire only if the anomaly persists N minutes |
| **Alert grouping / dedup** | Merge related alerts into one incident |
| **Feedback loops** | On-call marks false positives → retrain |
| **Seasonality-aware** | Model each hour / day separately |
| **Confidence thresholds** | Surface only high-confidence anomalies |

---

## Anomaly Detection in the Pipeline

```
 App/Infra ─► OTel Collector ─┬─► Metrics (Prometheus) ─► Anomaly
                              ├─► Traces  (Jaeger/Tempo)   Detection ─► Alert
                              └─► Logs    (Elasticsearch)  (iso-forest)  Mgr
                                                                          │
                                                              PagerDuty / Slack
```

**Best practices:**
1. Start with the **four golden signals** — Latency, Traffic, Errors, Saturation
2. **Version** your anomaly models
3. **Separate detection from response** (remediation → Week 6)
4. **Test** the pipeline with synthetic anomalies

---

## Observability for AI Agents — The New Blind Spot

Agents are a new class of "service": they call **LLM APIs** ($/token, latency), use **tools** (may fail silently), and **decide autonomously**.

Without instrumentation, an agent is a **black box** — you see the action, not the *why*, the tokens, or the confusing tool result.

Real failures:
- Misconfigured agent burns thousands of $ in minutes
- A slow agent becomes the pipeline bottleneck
- Hallucinated tool params → incorrect remediation

**Principle: treat agents as first-class services with their own telemetry.**

---

## OTel GenAI Semantic Conventions

Standardized span attributes for LLM calls:

| Attribute | Meaning |
|---|---|
| `gen_ai.system` | Provider — `anthropic`, `openai` |
| `gen_ai.request.model` | Model requested |
| `gen_ai.response.model` | Model actually used |
| `gen_ai.usage.input_tokens` | Prompt tokens |
| `gen_ai.usage.output_tokens` | Completion tokens |
| `gen_ai.operation.name` | `chat`, `embeddings`, `tool_call` |

**Compute:** cost = tokens × $/token · latency = span duration · tool success rate · context efficiency = output/input.

---

## Instrumenting an Agent

```python
def call_llm_with_telemetry(prompt, model="claude-opus-4-5"):
    with tracer.start_as_current_span("gen_ai.chat") as span:
        span.set_attribute("gen_ai.system", "anthropic")
        span.set_attribute("gen_ai.operation.name", "chat")
        span.set_attribute("gen_ai.request.model", model)
        start = time.time()
        response = client.messages.create(model=model, max_tokens=1024,
            messages=[{"role": "user", "content": prompt}])
        span.set_attribute("gen_ai.usage.input_tokens",  response.usage.input_tokens)
        span.set_attribute("gen_ai.usage.output_tokens", response.usage.output_tokens)
        span.set_attribute("llm.latency_ms", (time.time()-start)*1000)
        return response.content[0].text
```

Parent span `sre_agent.investigate` + child `gen_ai.chat` (tokens, latency, model).

**Never log full prompts/completions in prod** — PII/secrets. Truncate or hash.

---

## Quiz: The Silent Cost Spike

**Q:** All app dashboards are green, but the cloud bill spiked overnight — an agent burned thousands in LLM calls. Why didn't normal observability catch it, and what would?

<br>

- Standard metrics don't see *inside* the agent — it's a **black box** that calls an LLM API
- Emit **OTel GenAI telemetry**: `input/output_tokens` (→ cost), span duration (→ latency), tool-call success spans
- Then **alert on token-spend / call-rate in real time** — not on the monthly invoice

---

## Session 9 — Common Pitfalls

- **Training on data that already contains anomalies** → model thinks the crash is normal
- **Ignoring seasonality** → every Saturday flagged; use per-hour/day baselines
- **`contamination` too high** → finds 20% anomalies even in healthy data (start 1–3%)
- **Logging full prompts/completions** → PII & secrets leak
- **LLM on every log line** → prohibitively expensive; reserve for flagged windows
- **No baseline period after deploy** → normal changes flagged; widen bounds 15–30 min

---

## Discussion — Session 9

1. **Threshold vs. ML alerts:** 200 threshold alerts, 80% acked without investigating. What changes with ML to cut noise without missing incidents?
2. **Cost surprise:** an agent spent $3,000 overnight, unnoticed until the invoice. What guardrails catch it in real time?
3. **Vendor lock-in:** Datadog + Splunk vs. an open-source OTel-native stack — trade-offs?
4. **Model drift:** iso-forest trained last month; traffic changed after an upgrade. How do you detect drift and remediate?

---

<!-- _class: lead invert -->

# Session 10
## Root Cause Analysis with AI Agents
### ~1.5 hours

---

## Session 10 — Learning Objectives

1. Explain how service dependency graphs trace a failure's origin.
2. Describe how LLMs/NLP correlate logs and traces to find root causes.
3. Explain alert grouping & incident summarization at scale.
4. Describe prioritizing incidents by business impact.
5. Design a simple agentic RCA pipeline that investigates and reports.

---

## Service Dependency Graph

```
 frontend ──► checkout ──► payment ──► postgres-db
  0.2% err     4% err       4% err      ROOT CAUSE
  (healthy)   (symptom)    (symptom)    (DB failed)
```

- **Nodes** = services / DBs / queues · **Edges** = caller → callee · attributes: rate, errors, p99
- **Rule of thumb:** high error rate **+ no failing upstream** = likely the cause, not a symptom
- The graph emerges automatically from traces (`service.name`, `parent_span_id`)

---

## Quiz: Root Cause vs. Symptom

**Q:** `checkout`, `payment`, and `postgres-db` all show high error rates at once. How does the dependency graph pick the root cause?

<br>

- Walk **upstream**: the root is the failing node whose own upstream is **healthy**
- `checkout → payment → postgres-db`: the first two error *because* the DB is down → symptoms
- `postgres-db` has high errors and nothing healthy upstream explains them → **root**

---

## Building & Analyzing the Graph

```python
def find_error_source(G, threshold_error_rate=0.05):
    culprits = []
    for node in G.nodes():
        high_error = any(d["error_rate"] > threshold_error_rate
                         for _, _, d in G.out_edges(node, data=True))
        if not high_error: continue
        upstream_error = any(
            any(d["error_rate"] > threshold_error_rate
                for _, _, d in G.out_edges(pred, data=True))
            for pred in G.predecessors(node))
        if not upstream_error: culprits.append(node)   # high err, healthy upstream
    return culprits
```

| Graph algorithm | RCA use |
|---|---|
| Shortest path (BFS/DFS) | How an error propagates A → B |
| Topological sort | Investigate leaf dependencies first |
| PageRank / centrality | Most influential services (cascade risk) |
| Anomaly subgraph | Minimal set of simultaneously-anomalous services |

---

## Log & Trace Correlation with LLMs / NLP

Thousands of lines, hundreds of traces around the anomaly. You must: find *causally* related evidence, order events, separate root cause from symptoms.

- **Template matching (Drain3):** templates appearing more than usual in the incident window = signal
- **TF-IDF anomaly scoring:** words frequent in the incident window, rare normally = incident-specific
- **Embedding similarity:** cluster semantically-similar log lines (failed payments cluster together)

---

## LLM-Powered RCA Summary

```python
system_prompt = """You are an expert SRE performing a root cause analysis.
Output a structured report:
1. SUMMARY  2. TIMELINE  3. ROOT CAUSE  4. CONTRIBUTING FACTORS
5. REMEDIATION  6. PREVENTION
Be concise, factual, and cite specific log lines or trace IDs as evidence."""

response = client.messages.create(
    model="claude-opus-4-5", max_tokens=2048,
    system=system_prompt,
    messages=[{"role": "user", "content": user_content}])  # alerts + graph + logs + traces
```

**LLMs hallucinate** → require cited evidence (lines, span IDs, timestamps); a **human validates** the reasoning. LLM correlates; human confirms.

---

## Alert Grouping & Summarization

One root cause → dozens/hundreds of alerts in seconds. SREs report **40+ pages per major incident** — grouping can cut it to **1–3**.

| Approach | Signal |
|---|---|
| **Rule-based** | Same service / known deps within a time window |
| **Temporal** | Alerts firing within N seconds |
| **Topological** | Alerts from connected graph nodes |
| **Semantic** | Similar alert-message embeddings |
| **Historical** | "These always fire together" |
| **LLM-powered** | Ask the model to group by probable root cause (JSON) |

**Summarize** the incident in plain English: what's broken · when it started · what's been tried · current status.

---

## Prioritizing by Impact

Not all incidents are equal — 1% on internal analytics ≠ 0.1% on checkout.

| Dimension | Examples |
|---|---|
| **User impact** | How many users? Critical journey (checkout, login)? |
| **Revenue impact** | Revenue flow? $ per minute of downtime? |
| **SLO budget burn** | How fast is the error budget draining? |
| **Data integrity** | Data lost/corrupted (usually highest) |
| **Blast radius** | One region or cascading across all? |

---

## SLO Error-Budget Burn Rate

```python
def compute_burn_rate(current_error_rate, slo_target, budget_window_days=30):
    allowed = 1.0 - slo_target          # 0.001 for a 99.9% SLO
    return current_error_rate / allowed  # >14.4 ⇒ budget gone in <2 hrs
```

- Converts abstract reliability into **time**: "budget exhausted in 4 hours"
- Burn rate **> 14.4** (Google SRE page threshold) → wake someone up now
- Concrete urgency, independent of the absolute error count

---

## Quiz: Smaller Error, Higher Priority?

**Q:** 1% error on an internal analytics API vs. 0.2% on the checkout flow. Why might the *smaller* rate be the higher priority?

<br>

- Raw error rate ≠ impact
- Checkout is **critical, revenue-generating** with a tight SLO — 0.2% can burn the budget fast and hit real users/revenue
- Prioritize by **impact dimensions** (user/revenue, SLO burn, data integrity, blast radius) — burn rate makes it urgency, not a raw number

---

## Agentic RCA — Human-on-the-Loop

Traditional RCA is manual: page → log in → pull logs → check graphs → hypothesize → postmortem. Hours, and expertise you may lack at 3 AM.

An **agentic RCA system** automates the *investigation*, producing a draft report a human reviews. Human stays **on the loop** — decides whether to act.

```
 Alert ─► 1 Gather context ─► 2 Correlate ─► 3 Assess impact
         (perceive: metrics,  (plan: LLM      (SLO burn,
          logs, deploys,       proposes causes  users, severity)
          dep graph)           w/ evidence)          │
                                                      ▼
   5 Human review gate ◄──── 4 Generate Markdown RCA report (act)
   (edit, approve)           (log excerpts, trace IDs)
```

---

## Agentic RCA in Code

```python
RCA_TOOLS = [ get_metrics, get_logs, get_recent_deployments ]  # MCP-style defs

def run_rca_agent(incident_description):
    messages = [{"role": "user", "content":
        f"INCIDENT: {incident_description}\nInvestigate. Use tools to gather "
        "evidence, then produce a structured RCA report."}]
    while True:                                   # agentic loop
        response = client.messages.create(
            model="claude-opus-4-5", max_tokens=2048,
            tools=RCA_TOOLS, messages=messages)
        if response.stop_reason == "tool_use":
            tool_results = [run(block) for block in response.content
                            if block.type == "tool_use"]
            messages += [{"role": "assistant", "content": response.content},
                         {"role": "user", "content": tool_results}]
        else:
            return final_text(response)
```

Same **perceive → plan → act → observe → repeat** loop from Week 1, now for incidents.

---

## Session 10 — Common Pitfalls

- **Correlation ≠ causation** — require the LLM to explain the causal mechanism, not just overlap
- **Stale dependency graphs** — refresh often; old maps mislead the agent
- **Too much data** — pre-filter to the most anomalous lines before the LLM
- **Skipping the human review gate** — one wrong auto-rollback can beat the original incident
- **Optimizing MTTR without accuracy** — fast-but-wrong 30% is worse than slow-but-right 95%
- **Priority inversion from noisy SLOs** — audit SLO definitions regularly

---

## Discussion — Session 10

1. **Trust:** the agent blames a DB config change; the engineer disagrees. The report cites specific log lines. How do you resolve it?
2. **Blast radius vs. speed:** should the agent auto-apply rollback when burn rate > 14.4×? What guardrails first?
3. **Graph evolution:** a new payment processor was added yesterday; the graph is a week old. How could that mislead the agent?
4. **Multi-tenancy:** 50 of 10,000 customers hit — but the top 10% by revenue. Is pure SLO burn the right signal?

---

## Recap & Connections

**In one sentence:** you gave the system eyes — observability, ML anomaly detection, AI-driven RCA, and OTel instrumentation of the agents doing the observing.

| Earlier week | Connection |
|---|---|
| **Week 1** (agent loop) | perceive–plan–act is exactly what the RCA agent runs |
| **Week 2** (MCP, tools) | RCA tools are MCP-style tool definitions |
| **Week 3** (CI/CD) | anomaly detection catches post-deploy regressions |
| **Week 4** (forecasting) | anomaly detection flags deviations from the forecast |

---

## Looking Ahead — Week 6

From *seeing* problems to *fixing* them autonomously:

- **Self-healing systems** that respond to this week's anomalies
- **Agentic SRE workflows** that run runbooks and open remediation PRs
- **Blast-radius guardrails** that keep autonomy safe
- **ITSM integration** (PagerDuty, ServiceNow) for human escalation

Week 5 = sensing layer · Week 6 = actuation layer → a closed feedback loop.

---

<!-- _class: lead invert -->

# Questions?

Head to `week-05-lab.md` and build the isolation-forest detector + OTel-instrumented agent in `project/anomaly/`.
