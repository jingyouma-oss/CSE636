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

# Week 6: Autonomous Incident Response & Agentic SRE
## From detecting problems to safely fixing them
### CSE636 — DevOps with AI

Qingsong Zhang, Ph. D.

---

## At a Glance

**Theme:** The agent stops *reporting* and starts *acting* — self-healing systems, agentic on-call helpers, and the guardrails that keep autonomous action safe.

| | |
|---|---|
| **Prerequisites** | Week 5 (detection / RCA) + Week 2 (MCP, least-privilege) |
| **Time budget** | 2 sessions: ~2 hrs + ~1.5 hrs |
| **By the end** | Architect self-healing, run a ReAct loop, choose autonomy level, enforce guardrails, wire to ITSM |
| **You'll build** | A ReAct triage agent with MCP tools + a gated rollback |

Climax of the "agents in operations" arc → prepares for Week 7 (govern + capstone).

---

## Foundations Primer — SRE

An SRE team keeps a service *reliable*: up, fast, and correct.

| Term | Plain-language meaning |
|---|---|
| **SLI** | A metric you measure (e.g. % of requests that succeed) |
| **SLO** | The target for that metric (e.g. 99.9% over 30 days) |
| **SLA** | Contractual promise, usually weaker than the SLO |
| **Error budget** | Allowed unreliability before you breach the SLO (99.9% → ~43 min/month) |
| **MTTR** | Mean Time To Recover — the primary goal to reduce |
| **Toil** | Repetitive manual ops work; SRE philosophy = automate it away |

Incident lifecycle: **Detect → Triage → Diagnose → Mitigate → Resolve → Postmortem**

---

## Foundations Primer — Operators & RL

**Kubernetes Operator** — extends the control loop with app-specific knowledge:
- **CRD** — a new resource type (e.g. `SelfHealingPolicy`)
- **Controller** — watches custom resources, reconciles actual → desired

Built-in K8s = sprinklers (restart a crashed Pod). Operator = smart building system (knows *when* to fail over, evacuate, document).

**Reinforcement Learning (intuition only)** — agent learns by doing (action → reward). Like training a dog with treats.
- ⚠️ RL on live prod is research-level and risky. In practice: a *recommendation* engine, human approves.
- Week 6 lab uses the safer approach: a scripted LLM agent with explicit guardrails.

---

<!-- _class: lead invert -->

# Session 11
## Self-Healing Systems & Agentic SRE
### ≈ 2 hours

---

## Learning Objectives — Session 11

1. Describe self-healing architecture and where AI agents fit.
2. Explain the **ReAct** loop (Reason → Act → Observe) on an incident.
3. Identify the **five levels of autonomy** and pick the right one.
4. Define **blast-radius control** + name three techniques.
5. Explain how K8s Operators and LLM agents complement each other.

---

## What Does "Self-Healing" Mean?

Detect that something is wrong and correct it — without waking a human at 3 a.m.

The simplest version already exists: **Pod crashes → K8s restarts it.** But real incidents are messier:

- Pod is healthy but returns slow / wrong responses
- A database overloaded by one misbehaving downstream service
- A canary's error rate climbing after a rollout — roll back?
- Three alerts, all symptoms of one upstream DNS misconfig

You need a system that can *reason*, not just react to up/down.

---

## The Virtual SRE Mental Model

An agent that plays the experienced on-call engineer:

1. **Perceives** alerts, logs, metrics, traces (Week 5 observability stack)
2. **Reasons** about what's happening and what the runbook says
3. **Acts** using tools (restart, scale, roll back, open a ticket)
4. **Observes** whether the action helped
5. **Escalates** to a human when unsure or about to do something irreversible

Not sci-fi — PagerDuty AI, Dynatrace Davis, Datadog Bits AI already do parts of this.

---

## Self-Healing Architecture

```
  Observability (Week 5)   Prometheus / Loki / Tempo
          │  alert / anomaly signal
          ▼
  Incident intake          alert mgr → de-dup → correlate → enrich
          │  structured incident context
          ▼
  Agentic SRE (new!)       LLM agent + MCP tools (kubectl, runbooks,
          │                ITSM), ReAct loop, guardrails, approval gate
          ├──► safe reversible actions ─► K8s/Cloud API   (Level 3, auto)
          └──► irreversible actions ────► human on-call    (Level 2, approve)
```

Key insight: the agentic layer sits *between* observability and remediation. It reasons — but does **not** have unbounded permission to act.

---

## The ReAct Reasoning Loop

**ReAct** (Reason + Act) — the dominant mental model for multi-step LLM agents (2022 paper).

```
   ┌──────────────────────────────────────────┐
   │                                          │
   ▼                                          │
 Reason (Thought) ──► Act (Action) ──► Observe┘
 "errors spiked 5m    "check canary   "canary error
  ago, deploy 8m ago   status"          rate 12%"
  → regression"
```

Loop repeats until the incident is resolved or the agent determines it cannot.

---

## ReAct — A Worked Trace

- **Thought:** "Error rate on payment-svc spiked 5 min ago. Last deploy was 8 min ago. Looks like a regression."
- **Action:** "Check the canary deployment status."
- **Observation:** "Canary error rate: 12%. Baseline: 0.3%."
- **Thought:** "Canary is clearly bad. Runbook says roll back if > 5%. I should roll back."
- **Action:** call rollback tool — *but first check if human approval is required.*

---

## Why ReAct Matters for Safety

Because the agent writes reasoning *before* acting, you can:

- **Log every thought** for audit / postmortems
- **Insert an approval gate** between "Thought: roll back" and the actual API call
- **Set confidence thresholds** — only auto-execute above a bar

Transparency is what makes ReAct suitable for production ops, where blind action is dangerous.

An advanced variant adds a **reflection** step after remediation → seeds the automated postmortem (Session 12).

---

## Quiz: ReAct Safety

**Q:** ReAct makes the agent write a natural-language "Thought" before every action. Beyond readability, what two *safety* capabilities does that enable?

<details><summary>💡 Show answer</summary>

Because the reasoning is emitted *before* the tool call, you can (1) **log it for audit** — every decision has a recorded rationale — and (2) **insert an approval gate / confidence threshold between thought and action**. Blind action gives you neither.

</details>

---

## Autonomous Rollback

Going *backward* is not always safe:
- Previous version may have a security hole the new one fixed
- The version switch itself can cause a brief outage
- DB migrations may not be reversible

**A safe autonomous rollback policy (policy-as-code):**

```
IF  canary error rate > threshold   (5%)
AND duration > grace period         (3 min — avoids reacting to spikes)
AND no schema migration pending     (metadata flag)
AND error budget remaining > 10%    (don't burn budget on rollback outage)
THEN auto-rollback
ELSE page the human on-call
```

---

## Failover & Approval Gates

**Failover** redirects all traffic from a failing region/zone to a healthy one. Bigger blast radius, harder to undo → almost always needs human-on-the-loop. Agent can *recommend* and pre-stage; human approves the shift.

| Gate type | Mechanism | Best for |
|---|---|---|
| Soft approval | Slack: "roll back `payment-svc`? reply `yes`" | Low-stakes, trusted |
| Hard approval | PagerDuty ack before any destructive call | High-stakes, irreversible |
| Timeout escalation | Wait N min, else escalate to secondary | After-hours ops |
| Dry-run first | Run `--dry-run`, show diff, then confirm | First-time runbooks |

Lab: a simple soft-approval gate via CLI prompt.

---

## The Five Levels of Autonomy

| Lvl | Name | Agent does | Human role |
|---|---|---|---|
| 0 | Alert only | Sends notification w/ context | Does everything |
| 1 | Recommend | Suggests actions + confidence + runbook | Decides & acts |
| 2 | Draft & confirm | Pre-stages action, waits for approval | Approves |
| 3 | Act w/ notify | Executes safe reversible actions, notifies | Reviews async |
| 4 | Fully autonomous | Executes anything, no human | Reviews postmortem |

Most production: **Level 2–3** for reversible actions, **Level 1** for complex/irreversible. Level 4 is rare — only extremely low-risk actions (e.g. clearing a cache) in mature orgs.

---

## Blast-Radius Control

"Blast radius" = maximum damage if something goes wrong.

1. **Scope permissions tightly** — restart Pods in `staging`, not `production`
2. **Rate limits** — ≤ 1 remediation per service per 10 min (prevents flapping)
3. **Dry-run mode** — every action has `--dry-run`; test first
4. **Canary execution** — roll back 5%, verify, then the rest
5. **Kill switch** — one flag that disables all autonomy *now* (mandatory)
6. **Error budget gate** — block automation when budget is low
7. **Working-hours-only mode** — after hours, drop to Level 2

---

## Quiz: Runaway Restart Loop

**Q:** Your agent restarts a flapping service, which re-alerts, so it restarts again… in a loop that takes the service down. Which two controls stop this, and which control must *every* system have?

<details><summary>💡 Show answer</summary>

A **rate limit** and **loop/flap detection** would break the cycle. Regardless of anything else, every autonomous system must have a **kill switch**. (An error-budget gate is a good third layer.)

</details>

---

## Operators + Agents: Different Layers

| | Kubernetes Operator | LLM Agent |
|---|---|---|
| Strength | Fast, deterministic, API-native | Flexible reasoning, novel cases |
| Weakness | Only what's programmed | Slower, can hallucinate |
| Best for | Known remediations (restart, scale) | Diagnosis, runbook choice, escalation |
| Triggered by | K8s watch events | Alerts, requests, anomaly signals |

Flow: Operator fires an incident event → agent reasons via MCP, checks blast-radius policy → auto-execute (L3) or page human (L2) → agent calls the Operator's API for safe mechanics.

---

## SelfHealingPolicy CRD

```yaml
apiVersion: sre.example.com/v1
kind: SelfHealingPolicy
metadata:
  name: payment-svc-policy
spec:
  target:
    deployment: payment-svc
    namespace: production
  triggers:
    - metric: error_rate_5m
      threshold: 0.05        # 5%
      duration: 3m
  actions:
    - type: rollback
      autonomyLevel: 2       # draft and confirm
      requireApproval: true
    - type: scale_up
      autonomyLevel: 3       # act with notification
      maxReplicas: 10
```

---

## Quiz: Operator vs. LLM Agent

**Q:** For "restart a Pod that's crash-looping," is an Operator enough, or do you need the LLM agent?

<details><summary>💡 Show answer</summary>

A plain **Operator (or built-in K8s) is enough** for crash-loop → restart — fast, deterministic, well-defined. The **LLM earns its place on reasoning the Operator can't encode**: *should* we restart given traffic, budget, a pending migration? which runbook matches this novel symptom? do these four alerts share a root cause?

</details>

---

## Demo: Minimal Self-Healing Agent (1/2)

```python
# Simulated tools — real versions call the Kubernetes / Prometheus API
def get_canary_metrics(dep):        return {"error_rate": 0.08, ...}
def get_last_deployment_time(dep):  return "8 minutes ago"
def check_migration_pending(dep):   return False
def get_error_budget_remaining(s):  return 0.42          # 42% left
def dry_run_rollback(dep):          return "Would revert v1.4.2 → v1.4.1"
def execute_rollback(dep):          return "Rollback initiated. ETA 45s."

def request_approval(desc):         # prod: Slack + wait for 'yes'
    print(f"[APPROVAL GATE] agent wants to: {desc}")
    return input("Approve? (yes/no): ").strip().lower() == "yes"
```

---

## Demo: Minimal Self-Healing Agent (2/2)

```python
def run_sre_agent(dep):
    metrics = get_canary_metrics(dep)          # 1. Gather context
    migration = check_migration_pending(dep)
    budget = get_error_budget_remaining(dep)

    if migration:                              # 2. Blast-radius gate
        return page_oncall("migration pending — rollback NOT safe")
    if budget < 0.10:
        return page_oncall("error budget critically low")

    # Thought: error rate high, deploy recent, no migration, budget OK.
    print(dry_run_rollback(dep))               # 3. Dry run
    if request_approval("roll back v1.4.2 → v1.4.1"):   # 4. Level-2 gate
        print(execute_rollback(dep))
        print("Monitoring error rate for 5 min... postmortem to follow.")
    else:
        page_oncall("rollback declined")
```

---

## What to Notice in the Demo

- Collects **observations before reasoning** (ReAct pattern)
- Writes out reasoning (`thought`) before acting → loggable, auditable
- **Two blast-radius gates** before even asking: migration check + budget check
- Does a **dry run** before requesting approval
- Approval gate is a single function — swap `input()` for a Slack webhook in prod, same logic

---

## Pitfalls — Session 11

- **Alert on the alert system:** if the agent crashes, who fixes it? Always keep a human fallback.
- **Trusting confidence blindly:** LLMs can be confidently wrong. Back reasoning with deterministic checks.
- **Forgetting schema migrations:** rolling back code while schema is forward-migrated = catastrophe.
- **Cascading actions:** rate limits + per-service budgets prevent a chain of rollbacks.
- **No kill switch:** every system needs one, well-known and tested.
- **Logging thoughts but not actions:** audit needs *both* the reasoning and what was done.

---

<!-- _class: lead invert -->

# Session 12
## Alert Triage, Runbooks & ITSM Integration
### ≈ 1.5 hours

---

## Learning Objectives — Session 12

1. Explain why alert volume/noise is a problem; how suppression & correlation reduce it.
2. Describe how an agentic runbook differs from a scripted one.
3. Identify integration points between an agentic SRE and ITSM (PagerDuty, ServiceNow, Opsgenie).
4. Describe how to measure whether automated remediation is working.
5. Explain how AI-assisted postmortems close the feedback loop.

---

## The Alert Storm Problem

A database goes down → dozens/hundreds of downstream services alert. On-call gets **150 pages in 5 minutes** → burnout.

All 150 share one root cause. Correct response: fix the database.

- **Correlation** — group alerts that are likely symptoms of one root cause into a single incident. *(Comes first.)*
- **Suppression** — silence redundant downstream alerts once a root-cause incident is open.

```
150 alerts ──► correlation agent ──► 1 incident + suppress downstream
  (payment, cart, checkout... all depend on postgres-primary,
   one says "connection refused" → shared root cause)
```

---

## Noise Reduction Techniques

| Technique | Description |
|---|---|
| **Deduplication** | Many firings of same alert → one notification |
| **Flap detection** | Fires/clears repeatedly → suppress until stable |
| **Dependency-aware suppression** | Parent alerting → suppress child alerts |
| **Time-of-day windowing** | Lower sensitivity during known peaks (Black Friday) |
| **ML anomaly scoring** | Page only above adaptive threshold, not fixed |

---

## Quiz: Correlation vs. Suppression

**Q:** What's the difference, and why must correlation come first?

<details><summary>💡 Show answer</summary>

**Correlation** groups alerts likely from one root cause into a single incident; **suppression** then silences the downstream/redundant ones. Correlation must come first because you can only safely *suppress* an alert once you've established it's a symptom of an already-tracked incident — suppress first and you risk muting a genuinely independent problem.

</details>

---

## Traditional vs. Agentic Runbooks

Traditional runbook = a wiki page of `kubectl` commands + if/else prose. Fine when you have time; not fine at 2 a.m. after 30 alerts.

An **agentic runbook** encodes the same knowledge so an agent can *execute* it:
1. Reads structured incident context (from correlation)
2. Selects a runbook from a vector DB (semantic search)
3. Executes diagnostic steps as tool calls
4. Interprets outputs, picks next step or escalates

```
Traditional:  Human reads runbook → runs commands → decides
Agentic:      Agent reads runbook → runs commands → proposes action
                                                  → Human approves
                                                  → Agent executes
```

---

## Structured Runbook Format

```yaml
name: "payment-svc: high error rate"
triggers:
  - metric: error_rate_5m
    service: payment-svc
    threshold: 0.05
steps:
  - id: check_logs
    tool: kubectl_logs
    args: { namespace: production, deployment: payment-svc, tail: 200 }
    on_result:
      contains "timeout connecting to postgres": { goto: postgres_runbook }
      contains "null pointer exception":         { goto: check_recent_deploy }
      contains "rate limit exceeded":            { goto: check_api_quota }
escalation:
  page: on-call-primary
  message_template: "Agent could not auto-resolve. Context: {context}"
```

Agent reads this YAML as prompt context, then executes each step via MCP tools.

---

## ITSM and On-Call Integration

**ITSM** = IT Service Management — tools that track incidents, changes, requests.

| Tool | Primary role | Key agent integration |
|---|---|---|
| **PagerDuty** | On-call alerting, escalation | Create/resolve incidents, ack, timeline notes |
| **ServiceNow** | Enterprise ITSM, change mgmt, CMDB | Change requests, CMDB lookups, tickets |
| **Opsgenie** | On-call scheduling, routing | Like PagerDuty; strong schedule/override API |

Loop: alert → agent creates **one** PagerDuty incident → runs diagnostics → *resolved?* yes → resolve + timeline + draft postmortem; no → escalate w/ rich summary → postmortem action items feed runbooks/tests/thresholds.

---

## MCP Tool Exposure for ITSM

```python
# mcp_tools/pagerduty.py  (illustrative)
@server.list_tools()
async def list_tools():
    return [
        Tool(name="create_incident", description="Create a PagerDuty incident",
             inputSchema={"type": "object", "properties": {
                 "title": {"type": "string"},
                 "severity": {"enum": ["critical", "error", "warning"]},
                 "service_id": {"type": "string"}},
                 "required": ["title", "severity", "service_id"]}),
        Tool(name="resolve_incident", ...),
        Tool(name="add_timeline_note", ...),
    ]
```

From the agent's view, "file a ticket" and "restart a Pod" are both just tool calls. The MCP server handles the real API calls.

---

## Tracking Remediation Effectiveness

How do you know autonomy is working? Measure it.

| Metric | Good trend |
|---|---|
| **MTTR (automated)** | Decreasing |
| **Auto-resolution rate** | Increasing (to a safe ceiling) |
| **False positive rate** | Decreasing |
| **Rollback success rate** | > 95% |
| **Alert noise reduction** (pages/shift) | Decreasing |
| **Mean time to escalate** | Decreasing |
| **Error budget impact of automation** | < 10% of total consumed |

The last is critical: if failed remediations eat your budget, automation is making things *worse*.

---

## AI-Assisted Postmortems

A postmortem answers: what happened, why, how we fixed it, how we prevent recurrence.

High-value but time-consuming → SREs delay them when exhausted.

**The agent's advantage:** it was *present* for the whole incident — observed every alert, ran every diagnostic, executed/proposed every action. It can produce a first draft automatically.

Feeds back into: **runbook updates** · **test suite additions** · **threshold adjustments**.

→ A **feedback loop**: incidents improve the system, which reduces future incidents.

---

## What an Agent Can Draft

```markdown
## Incident Postmortem — Draft (AI-generated, requires human review)
Incident: INC-2025-1142 | payment-svc | SEV-2 | 18 min | Auto-resolved: Yes

### Timeline
- 14:32  error rate crossed 5% (canary)
- 14:33  last deploy v1.4.2 @ 14:24; dry-run rollback confirmed
- 14:34  operator approved via Slack   14:35  rollback initiated
- 14:38  error rate back to baseline (0.3%)   14:50  resolved

### Root Cause
Regression in v1.4.2: NPE when cart total > $10,000 (untested edge case).

### Action Items
1. [Eng] Add unit test for cart total > $10,000
2. [Reliability] Add failure mode to canary smoke-test suite
3. [Process] Review why staging missed it
```

Human reviews in ~10 min instead of 90.

---

## Quiz: Why "Requires Human Review"?

**Q:** An agent can draft a postmortem in seconds because it observed the whole incident. Why still mark it "requires human review"?

<details><summary>💡 Show answer</summary>

The LLM can **hallucinate** timeline details or assert a confident-but-wrong root cause, and a postmortem drives action items, test changes, and blame-free learning. The agent's advantage is *recall*; the human's job is to *verify* the cited evidence actually supports the conclusion before it becomes the official record.

</details>

---

## On-Call Augmentation & Escalation

On-call burnout: woken repeatedly, alert fatigue, knowledge concentrated in 1–2 people.

The agent helps with all three:
- **Fewer pages** — handles/suppresses noise
- **Faster resolution** — runs first diagnostics while you wake up
- **Knowledge democratization** — runbooks available to any on-call

**Agent-driven escalation decisions:**
- Known runbook + high confidence → page primary with a rich summary
- Novel / low confidence → escalate faster, more context
- 3 a.m. Sunday + low-risk → resolve autonomously (L3), notify async
- Cross-service → open a war-room bridge, page multiple teams

---

## Demo Extension: Ticket + Postmortem

```python
def run_sre_agent_with_itsm(dep):
    timeline = []
    incident_id = create_pagerduty_incident(          # create immediately
        title=f"{dep}: high error rate post-deployment", severity="error")
    timeline.append(f"Created incident {incident_id}")

    metrics = get_canary_metrics(dep)                 # same diagnostics as S11
    add_timeline_note(incident_id, "Diagnostics done. Proposing rollback.")

    if request_approval(f"roll back {dep}"):
        result = execute_rollback(dep)
        add_timeline_note(incident_id, f"Rollback executed: {result}")
        print(draft_postmortem(incident_id, timeline, root_cause, resolution))
        resolve_pagerduty_incident(incident_id, "Resolved via auto rollback.")
    else:
        add_timeline_note(incident_id, "Declined. Escalating to secondary.")
```

Same tool-call model — ITSM ops are just more tools alongside `execute_rollback`.

---

## Pitfalls — Session 12

- **Auto-resolving without verification:** false resolution → customer impact continues while team thinks it's fixed. Require an observation window before closing.
- **Publishing AI postmortems verbatim:** may contain hallucinated facts — mark as drafts, require sign-off.
- **Runbook coverage gaps:** 80% coverage means 20% of incidents handled with no guidance.
- **Over-broad ITSM credentials:** scope the token so the agent can only close *its own* incidents.
- **Ignoring the feedback loop:** assign owners + deadlines to action items, or the postmortem is wasted.

---

## Recap — What You Accomplished

Completed the "agents in operations" arc: from *detecting* problems (Week 5) to *autonomously resolving* them — safely.

- **Guardrails are not optional** — every action needs blast-radius analysis, a rate limit, a kill switch.
- **Transparency enables trust** — ReAct "thought" text makes reasoning auditable, so you can raise autonomy over time.
- **Humans stay in the loop for irreversible actions** — approval gates are responsible engineering.
- **Feedback loops compound** — postmortems → better runbooks → faster future resolutions.

---

## Looking Ahead: Week 7 (Capstone)

1. **Agentic IaC** — agents generate/review/apply Terraform, gated by Policy-as-Code (OPA).
2. **Internal Developer Platforms** — golden-path tooling (Backstage) + agent integration.
3. **AI Agent Security & Governance** — prompt injection, permission scoping, audit trails.
4. **Capstone** — end-to-end agentic DevOps: commit → CI/CD → deploy → observe → autonomous incident response, guardrails at every stage.

Your Week 6 self-healing agent becomes a component of that capstone. Start planning how it wires to your Week 3 pipeline + Week 5 anomaly detector.

---

<!-- _class: lead invert -->

# Questions?

Read Anthropic's "Building Effective Agents" — then head to the lab to build your ReAct triage agent.
