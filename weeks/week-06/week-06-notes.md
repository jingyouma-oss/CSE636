# Week 6: Autonomous Incident Response & Agentic SRE

> 📝 **Lecture notes.** The hands-on lab and assignment for this week live in **[week-06-lab.md](week-06-lab.md)**.


**Theme:** From detecting problems to *fixing* them — building self-healing systems, agentic on-call helpers, and the guardrails that keep autonomous action safe.

**Arc placement:** This is the climax of the "agents in operations" arc. Over the past five weeks you have learned to build CI/CD pipelines ([Week 3](week-03-notes.md)), predict failures ([Week 4](week-04-notes.md)), and detect anomalies and perform root-cause analysis ([Week 5](week-05-notes.md)). This week, the agent stops *reporting* and starts *acting*. That shift — from passive observer to active remediator — is where autonomy pays off most, and where the stakes are highest.

**Builds on:**
- [Week 5](week-05-notes.md): Anomaly detection, AI-driven RCA, and alert grouping feed directly into the triage logic here.
- [Week 2](week-02-notes.md): MCP (Model Context Protocol), tool permissions, and least-privilege agent design are the safety layer around every action this week.

**Prepares for:** [Week 7](week-07-notes.md) — Agentic IaC, platform engineering, security governance, and the capstone project, which asks you to wire together everything from Weeks 1–6 end-to-end.

---

## 🧱 Foundations Primer

Before diving into autonomous incident response, three foundational areas need a plain-language primer: Site Reliability Engineering (SRE), Kubernetes Operators, and Reinforcement Learning. None of these require prior expertise — read the explanations below and return here as a reference throughout the week.

### What is SRE (Site Reliability Engineering)?

Imagine a hospital. Doctors diagnose and treat patients; a separate team of engineers keeps the building's power, plumbing, and medical equipment running so doctors can do their work. SRE is that second team — but for software systems.

Google coined the term in the mid-2000s. An SRE team is responsible for keeping a service *reliable*: up, fast, and correct. Here are the key concepts you will encounter this week:

| Term | Plain-language meaning |
|---|---|
| **SLI** (Service Level Indicator) | A specific metric you measure, e.g., "percentage of HTTP requests that succeed". |
| **SLO** (Service Level Objective) | The target you set for that metric, e.g., "99.9% of requests must succeed over a rolling 30-day window". |
| **SLA** (Service Level Agreement) | The contractual promise to customers, usually slightly weaker than the SLO. |
| **Error budget** | The allowed amount of *unreliability* before you breach the SLO. If your SLO is 99.9%, you have 0.1% of requests — about 43 minutes per month — to spend on failures. |
| **MTTR** | Mean Time To Recover. How long it takes from the moment a failure starts until the service is back to normal. Reducing MTTR is the primary goal of autonomous incident response. |
| **On-call rotation** | A rota of engineers who carry a pager (or phone) and are expected to respond to alerts outside working hours. High-alert volume burns out on-call engineers fast. |
| **Incident lifecycle** | Detect → Triage → Diagnose → Mitigate → Resolve → Postmortem. |
| **Runbook / Playbook** | A documented, step-by-step procedure for responding to a known type of incident. Traditionally a wiki page; this week, we turn runbooks into executable agent workflows. |
| **Toil** | Repetitive, manual operational work that scales linearly with traffic. SRE philosophy is to automate away toil. |

The key insight for this course: almost everything in the incident lifecycle — detecting the alert, correlating it with similar alerts, looking up the runbook, restarting a service, filing a ticket — is *structured, repeatable work* that an agent can assist with or automate.

### Kubernetes Operators: The Controller Pattern

In [Week 4](week-04-notes.md) and [Week 5](week-05-notes.md) you deployed workloads to Kubernetes. This week we extend that with **Operators**, a Kubernetes pattern that lets you encode operational knowledge as code.

The core idea of Kubernetes is the **control loop**: Kubernetes constantly compares *desired state* (what you said you want in YAML) to *actual state* (what is actually running), and takes action to close any gap. For example, if you say "I want 3 replicas of my web server" and one crashes, Kubernetes starts a new one automatically.

A **Kubernetes Operator** extends this control loop for *application-specific* knowledge. Whereas built-in controllers know how to restart a crashed Pod, an Operator knows, say, how to perform a rolling upgrade of a database cluster, or how to trigger a failover when a health check fails in a specific way.

Structurally, an Operator is:
1. A **Custom Resource Definition (CRD)** — a new resource type you add to Kubernetes, e.g., `SelfHealingPolicy`.
2. A **controller** — a small program (usually Go or Python) that watches for changes to those custom resources and reconciles actual state toward desired state.

The analogy: built-in Kubernetes is like a building's fire suppression system (sprinklers respond to heat automatically). A Kubernetes Operator is like a smart building management system that *also* knows when to evacuate a specific floor, notify the fire department, reroute HVAC, and document what happened.

Session 11 shows how agents can work *alongside* Operators — the Operator handles low-level cluster mechanics (restart this Pod), while an LLM-powered agent handles reasoning (is this the right thing to do given current traffic, the error budget, and the on-call schedule?).

### Reinforcement Learning — Intuition Only

Reinforcement learning (RL) is a style of machine learning where an agent learns by *doing* — it takes actions, observes what happens, and receives rewards or penalties. Over many trials, it learns which actions lead to good outcomes.

Think of training a dog: you don't explain the rule in words; you give treats when the dog does the right thing and withhold them when it does not. The dog gradually figures out the rules from feedback.

In the context of incident response:
- The RL *agent* takes actions such as "restart this service" or "scale up this deployment."
- The *environment* is the live system.
- The *reward signal* could be: MTTR decreased (+1), error budget was not wasted (+0.5), an unnecessary restart caused a brief outage (−2).

**Important caveat for this course:** RL on live production systems is extremely risky and still largely research-level. In practice, teams use RL-trained models as *recommendation engines* (they suggest actions; a human approves) rather than fully autonomous actors. We mention RL here because it appears in vendor literature and research papers on self-healing systems. The Week 6 lab uses a much simpler and safer approach: a scripted LLM agent with explicit guardrails.

---

## Session 11: Self-Healing Systems & Agentic SRE

**Session budget: ≈ 2 hours**

---

### Learning Objectives

By the end of Session 11, students will be able to:

1. Describe the architecture of a self-healing system and where AI agents fit within it.
2. Explain the ReAct reasoning loop (Reason → Act → Observe → repeat) and apply it to an incident scenario.
3. Identify the five levels of autonomy for incident response and choose the appropriate level for a given context.
4. Define blast-radius control and name at least three concrete techniques for limiting it.
5. Explain how Kubernetes Operators and LLM agents complement each other for autonomous remediation.

---

### Timed Agenda

| Time | Block | Notes |
|---|---|---|
| 0:00–0:10 | Welcome, recap of Week 5 | Ask: "What did your anomaly detector find?" |
| 0:10–0:30 | Concept: Self-healing architecture & virtual SRE | Slides + whiteboard diagram |
| 0:30–0:55 | Concept: ReAct loop + levels of autonomy | Live trace-through with an example incident |
| 0:55–1:10 | Concept: Blast-radius control & guardrails | Tabletop exercise: "What could go wrong?" |
| 1:10–1:35 | Demo: Kubernetes Operator + Python agent | Instructor live-codes a minimal self-healing policy |
| 1:35–1:50 | 💬 Discussion & case questions | See below |
| 1:50–2:00 | Key terms review + preview of Session 12 | |

---

### Concept: Self-Healing Architecture & AI as a "Virtual SRE"

#### What does "self-healing" mean?

A self-healing system detects that something is wrong and corrects itself — without requiring a human to wake up and type commands at 3 a.m.

The simplest version of self-healing already exists in every Kubernetes cluster: if a Pod crashes, Kubernetes restarts it. But that handles only a narrow class of failures. Real-world incidents are messier:

- A service is running (the Pod is healthy) but returning slow or wrong responses.
- A database is overloaded because one downstream service is misbehaving.
- A deployment just rolled out and a canary's error rate is climbing — should you roll back?
- Three separate alerts fired, but they are all symptoms of one upstream DNS misconfiguration.

To handle these, you need a system that can *reason* about what is happening, not just react to a binary up/down signal.

#### The Virtual SRE Mental Model

Picture a highly experienced on-call engineer who has memorized every runbook and can read logs faster than you can scroll. The "virtual SRE" agent plays this role:

1. **Perceives** alerts, logs, metrics, and traces — assembled by the observability stack from [Week 5](week-05-notes.md).
2. **Reasons** about what is likely happening and what the runbook says to do.
3. **Acts** using tools (restart a Pod, scale a deployment, roll back a release, open a ticket).
4. **Observes** whether the action helped.
5. **Escalates** to a human if the situation is outside its confidence level or if it is about to do something irreversible.

This is not science fiction — commercial platforms like PagerDuty AI, Dynatrace Davis, and Datadog Bits AI already do parts of this. This week you build a simplified version from first principles so you understand what is under the hood.

#### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                 Observability Layer                  │
│  Metrics (Prometheus) + Logs (Loki) + Traces (Tempo) │
└────────────────────┬────────────────────────────────┘
                     │  alert / anomaly signal
                     ▼
┌─────────────────────────────────────────────────────┐
│              Incident Intake Layer                   │
│  Alert manager → de-duplicate → correlate → enrich  │
└────────────────────┬────────────────────────────────┘
                     │  structured incident context
                     ▼
┌─────────────────────────────────────────────────────┐
│              Agentic SRE Layer  (NEW this week)      │
│  LLM agent  ←→  MCP tools (kubectl, runbooks, ITSM) │
│  ReAct loop + guardrails + approval gate             │
└───────────┬────────────────────┬────────────────────┘
            │ safe action        │ needs approval
            ▼                    ▼
  Kubernetes / Cloud API    Human on-call (PagerDuty)
```

The key insight: the agentic layer sits *between* your observability stack and your remediation tools. It reasons, but it does not have unbounded permission to act.

---

### Concept: The ReAct Reasoning Loop

**ReAct** (Reason + Act) is a prompting and agent-architecture pattern introduced in a 2022 research paper. It has become the dominant mental model for how LLM-powered agents work through multi-step tasks.

#### The Loop

```
┌──────────┐
│  Observe │◄──────────────────────────────┐
└────┬─────┘                               │
     │  (what do I know so far?)            │ (what did the tool return?)
     ▼                                      │
┌──────────┐                        ┌───────┴──────┐
│  Reason  │                        │  Tool result │
│ (Thought)│                        └──────────────┘
└────┬─────┘                               ▲
     │  (what should I do next?)            │
     ▼                                      │
┌──────────┐                               │
│   Act    │───────────────────────────────┘
│ (Action) │  (call a tool)
└──────────┘
     │  (if answer found, stop)
     ▼
  Final Answer
```

In plain language:
- **Thought:** The agent writes out its reasoning in natural language. "The error rate on the payment service spiked 5 minutes ago. The most recent deployment was 8 minutes ago. This looks like a regression."
- **Action:** The agent calls a tool. "Check the canary deployment status."
- **Observation:** The tool returns data. "Canary error rate: 12%. Stable baseline error rate: 0.3%."
- **Thought again:** "The canary is clearly bad. The runbook says to roll back if error rate exceeds 5%. I should roll back."
- **Action:** The agent calls the rollback tool — but first checks whether this requires human approval.

The loop repeats until the agent either resolves the incident or determines it cannot.

#### Why ReAct matters for safety

Because the agent writes out its reasoning *before* acting, you can:
- Log every thought for audit purposes.
- Insert an approval gate between "Thought says roll back" and "actually calling the rollback API."
- Set confidence thresholds: only auto-execute if the agent's stated confidence is above a threshold.

This transparency is what makes ReAct suitable for production operations work, where blind action is dangerous.

#### Reflection and Multi-Step Agents

A more advanced variant adds a **reflection** step: after completing a remediation, the agent reviews what it did, checks whether the metrics improved, and writes a summary. This summary becomes the seed of an automated postmortem. We cover this in Session 12.

---

### Concept: Autonomous Rollback, Failover, and Approval Gates

#### Autonomous Rollback

A rollback undoes a deployment and reverts to the previous known-good version. This sounds safe — you are going *backward* — but it is not always so:

- The previous version may have a security vulnerability that the new version fixed.
- The rollback itself can cause a brief outage during the version switch.
- Database migrations may not be reversible.

Therefore, even rollback needs guardrails.

**A safe autonomous rollback policy:**

```
IF  canary error rate > threshold   (5%)
AND duration > grace period         (3 minutes — avoids reacting to spikes)
AND no schema migration pending     (checked via metadata flag)
AND error budget remaining > 10%    (don't burn the budget on a rollback outage)
THEN auto-rollback
ELSE page the human on-call
```

This is sometimes called a **policy-as-code** approach — you encode the conditions under which automation is allowed to act, just like you would encode security policies in OPA (Open Policy Agent, which you will use in [Week 7](week-07-notes.md)).

#### Autonomous Failover

Failover is bigger than rollback: it redirects all traffic from a failing region or availability zone to a healthy one. The blast radius is larger (all users in a region) and the action is harder to undo. Failover therefore almost always requires at least "human-on-the-loop" oversight: the agent can *recommend* failover and even pre-stage everything, but a human approves the actual traffic shift.

#### Approval Gates

An approval gate is a deliberate pause where the agent asks a human before proceeding. Implementation options, in increasing friction:

| Gate type | Mechanism | Best for |
|---|---|---|
| Soft approval | Slack message: "I'm about to roll back `payment-svc`. Reply `yes` to confirm." | Low-stakes, trusted automation |
| Hard approval | PagerDuty acknowledgment required before any destructive API call | High-stakes, irreversible actions |
| Timeout escalation | Agent waits N minutes; if no response, escalates to secondary on-call | After-hours operations |
| Dry-run first | Agent executes in `--dry-run` mode, shows the diff, then asks for confirmation | First-time runbook execution |

In the Week 6 lab you will implement a simple soft-approval gate using a command-line confirmation prompt (simulating the Slack message).

---

### Concept: Levels of Autonomy & Blast-Radius Control

#### The Five Levels (Applied to Incident Response)

The course introduced levels of autonomy in [Week 1](week-01-notes.md). Here is how they map specifically to incident response:

| Level | Name | What the agent does | Human role |
|---|---|---|---|
| 0 | Alert only | Sends a notification with context | Human does everything |
| 1 | Recommend | Suggests actions with confidence scores and runbook links | Human decides and acts |
| 2 | Draft & confirm | Pre-stages the action (writes the kubectl command, opens a ticket draft), waits for approval | Human approves, agent executes |
| 3 | Act with notification | Executes safe, reversible actions (restart a Pod, scale up), sends a notification after | Human reviews async |
| 4 | Fully autonomous | Executes any action without human involvement | Human reviews postmortem |

**Most production systems today operate at Level 2–3 for well-understood, reversible actions, and Level 1 for complex or irreversible actions.**

Level 4 is rare and should only apply to extremely well-understood, low-risk actions (e.g., clearing a cache) in mature organizations with extensive testing of the automation.

#### Blast-Radius Control

"Blast radius" is the maximum damage that can be done if something goes wrong. An explosion in a small room causes less damage than the same explosion in a city square. The same principle applies to autonomous agents.

Concrete techniques to limit blast radius:

1. **Scope permissions tightly.** The agent's service account should only have permission to restart Pods in the `staging` namespace, not `production` — until the automation is proven reliable.

2. **Rate limits.** Allow at most one automated remediation action per 10 minutes on the same service. This prevents a malfunctioning agent from flapping a service into unavailability.

3. **Dry-run mode.** All agent actions have a `--dry-run` flag that shows what would happen without doing it. Always test in dry-run first.

4. **Canary execution.** Before rolling back all instances, roll back 5% of them and verify the error rate improves.

5. **Kill switch.** A single environment variable or feature flag that, when set, disables all autonomous remediation immediately. Every autonomous system must have one.

6. **Error budget gate.** If the error budget for a service is below a threshold, block automated actions entirely and require human involvement — because you cannot afford any more risk.

7. **Working-hours-only mode.** Limit fully autonomous actions to working hours when the team is available to intervene. After hours, drop to Level 2 (confirm before acting).

---

### Concept: Orchestration with Kubernetes Operators and Agents

Kubernetes Operators and LLM agents occupy different layers of the self-healing stack:

| | Kubernetes Operator | LLM Agent |
|---|---|---|
| Strength | Fast, deterministic, API-native | Flexible reasoning, handles novel situations |
| Weakness | Can only do what was explicitly programmed | Slower, can hallucinate, non-deterministic |
| Best for | Known, well-defined remediations (restart Pod, scale Deployment) | Diagnosis, runbook selection, escalation decisions |
| Triggered by | Kubernetes watch events (resource changes) | Alerts, human requests, anomaly signals |

A well-designed self-healing stack uses both:

1. The **Operator** watches for a `SelfHealingPolicy` CRD with rules like "if Pod restarts > 5 in 5 minutes, fire an incident event."
2. The **LLM agent** receives the incident event via MCP, reasons about the context, chooses an action, checks the blast-radius policy, and either auto-executes (Level 3) or pages a human (Level 2).
3. If the agent decides to restart the service, it calls the Operator's API — the Operator handles the mechanics safely.

```yaml
# Example: A minimal SelfHealingPolicy CRD
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

### Worked Demo: A Minimal Self-Healing Agent

The instructor will walk through this code live. Students should read it now as a preview.

```python
# demo_self_healing.py
# Minimal ReAct-style agent that evaluates a deployment health event
# and decides whether to roll back (with approval gate).

import json

# --- Simulated tool functions (real versions would call Kubernetes API) ---

def get_canary_metrics(deployment: str) -> dict:
    """Fetch current error rate and p99 latency for a deployment."""
    # In production: query Prometheus
    return {"error_rate": 0.08, "p99_latency_ms": 450, "deployment": deployment}

def get_last_deployment_time(deployment: str) -> str:
    """Return when the last deploy happened."""
    return "8 minutes ago"

def check_migration_pending(deployment: str) -> bool:
    """Return True if a database migration is in progress."""
    return False

def get_error_budget_remaining(service: str) -> float:
    """Return fraction of error budget remaining (0.0–1.0)."""
    return 0.42   # 42% remaining

def dry_run_rollback(deployment: str) -> str:
    """Show what a rollback would do, without executing it."""
    return f"Would revert {deployment} from v1.4.2 → v1.4.1 (previous stable)"

def execute_rollback(deployment: str) -> str:
    """Execute the rollback (requires prior approval)."""
    return f"Rollback of {deployment} initiated. ETA: 45 seconds."

# --- Approval gate ---

def request_approval(action_description: str) -> bool:
    """
    In production: send a Slack message and wait for a 'yes' reply.
    In this demo: ask the user at the terminal.
    """
    print(f"\n[APPROVAL GATE] The agent wants to: {action_description}")
    answer = input("Approve? (yes/no): ").strip().lower()
    return answer == "yes"

# --- The agent loop ---

def run_sre_agent(deployment: str):
    print(f"\n=== Agentic SRE: evaluating incident for '{deployment}' ===\n")

    # Step 1: Gather context
    metrics = get_canary_metrics(deployment)
    deploy_time = get_last_deployment_time(deployment)
    migration = check_migration_pending(deployment)
    budget = get_error_budget_remaining(deployment)

    print(f"[Observation] Metrics: {json.dumps(metrics, indent=2)}")
    print(f"[Observation] Last deploy: {deploy_time}")
    print(f"[Observation] Migration pending: {migration}")
    print(f"[Observation] Error budget remaining: {budget:.0%}")

    # Step 2: Reason
    error_rate = metrics["error_rate"]
    thought = []
    thought.append(f"Error rate is {error_rate:.1%}, well above 5% threshold.")
    thought.append(f"Last deployment was {deploy_time} — temporal correlation is high.")

    if migration:
        thought.append("WARNING: migration is pending. Rollback is NOT safe. Escalate to human.")
        print("\n[Thought] " + " ".join(thought))
        print("[Action] Paging on-call engineer (escalation, no auto-action).")
        return

    if budget < 0.10:
        thought.append("Error budget critically low. Any action risks further depletion. Escalate.")
        print("\n[Thought] " + " ".join(thought))
        print("[Action] Paging on-call engineer (budget gate).")
        return

    thought.append("No migration pending. Error budget healthy. Rollback appears safe.")
    thought.append("Runbook: high-error-rate-after-deploy → rollback. Confidence: HIGH.")
    print("\n[Thought] " + " ".join(thought))

    # Step 3: Show dry run
    dry_run_result = dry_run_rollback(deployment)
    print(f"\n[Dry Run] {dry_run_result}")

    # Step 4: Approval gate (Level 2 autonomy)
    approved = request_approval(f"roll back {deployment} from v1.4.2 → v1.4.1")

    if approved:
        result = execute_rollback(deployment)
        print(f"\n[Action] {result}")
        print("[Observation] Monitoring error rate for next 5 minutes...")
        print("[Done] Incident remediation in progress. Postmortem to follow.")
    else:
        print("\n[Action] Rollback declined by operator. Paging on-call for manual review.")

if __name__ == "__main__":
    run_sre_agent("payment-svc")
```

**What to notice in this code:**

- The agent collects observations before reasoning (ReAct pattern).
- It writes out its reasoning (`thought` list) before acting — this is loggable and auditable.
- It has two blast-radius gates before even asking for approval: migration check and error budget check.
- It does a dry run before requesting approval.
- The approval gate is a single function — in production you would swap the `input()` call for a Slack webhook call, but the logic is the same.

---

### 💬 Discussion & Case Questions

1. **Amazon 2021 Christmas outage** — A misconfigured automated remediation script triggered a cascade that took down AWS US-EAST-1. What blast-radius controls might have prevented the cascade? At what autonomy level should that script have been running?

2. **Level of autonomy debate** — Your team's payment service is down. The automated agent has 95% confidence it should roll back. Should it act immediately (Level 3) or wait for approval (Level 2)? What additional context would change your answer?

3. **The pager fatigue problem** — Your on-call engineer receives 200 alerts per night, most of which are noise. How does an agentic SRE help? What risks does it introduce?

4. **ReAct vs. scripted runbook** — Traditional runbooks are scripts with if/else logic (deterministic). ReAct agents reason in natural language (probabilistic). What are the tradeoffs? When would you prefer a scripted runbook?

5. **Kubernetes Operator vs. LLM agent** — For a simple "restart if crash-looping" scenario, is a Kubernetes Operator enough? When do you need the LLM layer on top?

---

### 🔑 Key Terms — Session 11

| Term | Definition |
|---|---|
| **Self-healing system** | A system that detects failures and corrects them automatically, without human intervention. |
| **Virtual SRE** | An AI agent that performs the reasoning and decision-making tasks of an on-call SRE engineer. |
| **ReAct loop** | Reason → Act → Observe → repeat. The core reasoning pattern for LLM agents doing multi-step tasks. |
| **Thought** | The agent's written-out reasoning before an action. Enables auditability and logging. |
| **Approval gate** | A deliberate pause where the agent requests human confirmation before a consequential action. |
| **Blast radius** | The maximum damage that can result if an autonomous action goes wrong. |
| **Blast-radius control** | Techniques to limit blast radius: scope, rate limits, dry-run, canary execution, kill switch. |
| **Kubernetes Operator** | An extension of the Kubernetes control loop that encodes application-specific operational knowledge. |
| **Custom Resource Definition (CRD)** | A new resource type you add to Kubernetes to represent custom operational concepts (e.g., `SelfHealingPolicy`). |
| **Levels of autonomy** | A spectrum from "alert only" (Level 0) to "fully autonomous" (Level 4), describing how much an agent acts independently. |
| **Error budget gate** | A guardrail that blocks automated actions when the SLO error budget falls below a threshold. |
| **Reinforcement learning (RL)** | A machine-learning approach where an agent learns optimal actions through reward signals. In incident response, typically used as a recommendation engine rather than a direct actor. |
| **Rollback** | Reverting a deployment to the previous known-good version. |
| **Failover** | Redirecting traffic from a failing component (region, zone, instance) to a healthy one. |

---

### ⚠️ Common Pitfalls — Session 11

- **⚠️ Alert on the alert system:** If your autonomous remediation agent crashes, who fixes it? Always have a human fallback — the agent should never be the only path to resolution.
- **⚠️ Trusting confidence scores blindly:** LLMs can be confidently wrong. A "HIGH confidence: rollback" thought is not a guarantee. Always back up reasoning with deterministic checks (migration flag, error budget).
- **⚠️ Forgetting schema migrations:** Rolling back application code while leaving a forward-migrated database schema in place is a common cause of catastrophic failures. Build a migration check into every rollback gate.
- **⚠️ Cascading actions:** If the agent rolls back one service and that causes a second service to alert, and the agent rolls back that one too — you can trigger a cascade. Rate limits and per-service blast-radius budgets prevent this.
- **⚠️ No kill switch:** Every autonomous system must have a single, simple, well-known way to disable it immediately. Document where the kill switch is and test it regularly.
- **⚠️ Logging the thoughts but not the actions:** Auditability requires logging both what the agent *thought* and what it *did*. Logging only actions misses the reasoning chain needed for postmortems.

---

## Session 12: Alert Triage, Runbooks & ITSM Integration

**Session budget: ≈ 1.5 hours**

---

### Learning Objectives

By the end of Session 12, students will be able to:

1. Explain why alert volume and noise are major problems in production operations, and describe how suppression and correlation reduce them.
2. Describe how an agentic runbook differs from a traditional scripted runbook.
3. Identify the key integration points between an agentic SRE and ITSM tools (PagerDuty, ServiceNow, Opsgenie).
4. Describe how to measure whether automated remediation is actually working.
5. Explain how AI-assisted postmortems close the feedback loop from incidents back to system improvement.

---

### Timed Agenda

| Time | Block | Notes |
|---|---|---|
| 0:00–0:05 | Recap of Session 11 | Quick quiz: what are the 5 levels of autonomy? |
| 0:05–0:25 | Concept: Alert suppression & correlation | Slides + live alert-storm demo |
| 0:25–0:45 | Concept: Agentic runbooks & ITSM integration | Whiteboard: agent ↔ PagerDuty ↔ ServiceNow flow |
| 0:45–1:00 | Concept: Postmortems & remediation effectiveness | Case study: SRE feedback loop |
| 1:00–1:20 | Demo: Extending the agent to file a ticket and draft a postmortem | Code walkthrough |
| 1:20–1:30 | 💬 Discussion & case questions | |
| 1:30–1:30 | Wrap-up, lab preview | |

---

### Concept: Intelligent Alert Suppression and Correlation

#### The Alert Storm Problem

When a major component fails — say, a database goes down — dozens or hundreds of downstream services begin alerting. Each service fires its own alert: "payment-svc latency high," "cart-svc error rate elevated," "checkout-svc timeout," and so on. The on-call engineer receives 150 pages in 5 minutes. This is called an **alert storm**, and it is one of the leading causes of on-call burnout.

In this situation, all 150 alerts share a single root cause. The correct response is: fix the database.

**Alert suppression** means silencing redundant alerts that are clearly caused by a known ongoing incident. If you already have an open incident for "database-primary is down," you suppress all downstream service alerts that have a causal dependency on that database.

**Alert correlation** is the step before suppression: grouping alerts that are likely symptoms of the same root cause into a single incident. You learned the graph-based and ML approaches to correlation in [Week 5](week-05-notes.md). This week we focus on *acting* on the correlated result.

#### How an Agent Handles Correlation

```
Incoming alerts (last 5 minutes):
  - payment-svc: error rate 15%
  - cart-svc: p99 latency 3200ms
  - checkout-svc: timeout on database calls
  - order-history-svc: "connection refused" to postgres-primary

Agent thought:
  "Four alerts, all services that depend on postgres-primary.
   The order-history-svc alert mentions 'connection refused' to the database.
   High probability: postgres-primary is the root cause.
   Creating one incident: 'postgres-primary connectivity failure'.
   Suppressing downstream alerts for 30 minutes or until root cause resolved."

Agent action:
  - Create one PagerDuty incident (not four)
  - Tag payment-svc, cart-svc, checkout-svc, order-history-svc as related
  - Set suppression window for those services
  - Begin triage runbook: postgres-primary
```

This reduces 150 pages to 1, and gives the on-call engineer a clear starting point.

#### Noise Reduction Techniques

| Technique | Description |
|---|---|
| **Deduplication** | Multiple firings of the same alert → one notification |
| **Flap detection** | Alert that fires, clears, fires, clears repeatedly → suppressed until stable |
| **Dependency-aware suppression** | If parent service is alerting, suppress child service alerts |
| **Time-of-day windowing** | Lower alert sensitivity during known high-traffic windows (Black Friday) |
| **ML-based anomaly scoring** | Only page when anomaly score exceeds adaptive threshold (not fixed threshold) |

---

### Concept: Agentic Runbooks and Playbooks

#### Traditional Runbooks: The Problem

A traditional runbook is a wiki page like:

> **Runbook: payment-svc high error rate**
> 1. Check the error logs: `kubectl logs -n production deployment/payment-svc | tail -200`
> 2. If you see "timeout connecting to postgres", follow the postgres runbook.
> 3. If you see "null pointer exception", check the last deployment and consider rollback.
> 4. If you see "rate limit exceeded", check the upstream API quota dashboard.

This is fine when the on-call engineer has time to read it. At 2 a.m., after being woken by 30 alerts, this is not fine.

#### Agentic Runbooks: What Changes

An agentic runbook is the same knowledge, but encoded so that an agent can *execute* it rather than a human. The agent:

1. Reads the structured incident context (from the alert correlation step above).
2. Selects the appropriate runbook from a vector database of runbooks (semantic search: "which runbook matches this incident?").
3. Executes the diagnostic steps as tool calls.
4. Interprets the outputs and chooses the next step (or escalates).

The human on-call shifts from *executing* the runbook to *reviewing the agent's execution* and approving the final remediation action.

```
Traditional:   Human reads runbook → Human runs commands → Human decides
Agentic:       Agent reads runbook → Agent runs commands → Agent proposes action
                                                         → Human approves
                                                         → Agent executes
```

This reduces the cognitive load on the on-call engineer and significantly cuts MTTR.

#### Structured Runbook Format

To make runbooks machine-executable, they need structure. A simple YAML format:

```yaml
# runbook: payment-svc-high-error-rate.yaml
name: "payment-svc: high error rate"
triggers:
  - metric: error_rate_5m
    service: payment-svc
    threshold: 0.05
steps:
  - id: check_logs
    description: "Fetch recent error logs"
    tool: kubectl_logs
    args:
      namespace: production
      deployment: payment-svc
      tail: 200
    on_result:
      contains "timeout connecting to postgres":
        goto: postgres_runbook
      contains "null pointer exception":
        goto: check_recent_deploy
      contains "rate limit exceeded":
        goto: check_api_quota

  - id: check_recent_deploy
    description: "Get last deployment time and diff"
    tool: get_deployment_history
    args:
      deployment: payment-svc
    on_result:
      deployed_within: "30m"
        action: propose_rollback
      else:
        escalate: true

escalation:
  page: on-call-primary
  message_template: "Agent could not auto-resolve. Context: {context}"
```

The agent reads this YAML as part of its prompt context, then executes each step using MCP-exposed tools.

---

### Concept: ITSM and On-Call Integration

**ITSM** stands for IT Service Management — the umbrella category of tools that track incidents, changes, and service requests. The three most common on-call/ITSM tools in cloud operations are:

| Tool | Primary role | Key agent integration |
|---|---|---|
| **PagerDuty** | On-call alerting, escalation, incident management | Create/resolve incidents, acknowledge alerts, add timeline notes, trigger escalations |
| **ServiceNow** | Enterprise ITSM, change management, CMDB | Create/update change requests, look up CMDB for service dependencies, file incident tickets |
| **Opsgenie** | On-call scheduling, alert routing, escalation | Similar to PagerDuty; strong schedule/override API |

#### The Agent-ITSM Integration Loop

```
Alert fires
    │
    ▼
Agent correlates & creates PagerDuty incident
    │
    ▼
Agent executes runbook diagnostics
    │
    ├─── auto-resolved ──► Agent resolves PagerDuty incident
    │                      Agent posts timeline summary
    │
    └─── needs human ───► Agent sends detailed summary to on-call engineer
                          (via PagerDuty notification)
                          On-call approves or takes over
                          │
                          ▼
                      If resolved: Agent files ServiceNow incident record
                                   Agent drafts postmortem
```

#### MCP Tool Exposure for ITSM

In the Week 6 lab, you will expose these operations as MCP tools:

```python
# mcp_tools/pagerduty.py  (illustrative — not production code)
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("pagerduty-tools")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="create_incident",
            description="Create a new PagerDuty incident",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "severity": {"type": "string", "enum": ["critical", "error", "warning"]},
                    "body": {"type": "string"},
                    "service_id": {"type": "string"}
                },
                "required": ["title", "severity", "service_id"]
            }
        ),
        Tool(
            name="resolve_incident",
            description="Resolve an open PagerDuty incident by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "incident_id": {"type": "string"},
                    "resolution_note": {"type": "string"}
                },
                "required": ["incident_id"]
            }
        ),
        Tool(
            name="add_timeline_note",
            description="Add a note to a PagerDuty incident timeline",
            inputSchema={
                "type": "object",
                "properties": {
                    "incident_id": {"type": "string"},
                    "note": {"type": "string"}
                },
                "required": ["incident_id", "note"]
            }
        )
    ]
```

The agent calls these tools just like it calls `kubectl_logs` or `execute_rollback`. From the agent's perspective, "file a ticket" and "restart a Pod" are both just tool calls. The MCP server handles the actual API calls.

---

### Concept: Tracking Remediation Effectiveness

How do you know whether your autonomous incident response is actually working? You measure it.

#### Key Metrics

| Metric | How to measure | Good trend |
|---|---|---|
| **MTTR (automated)** | Time from alert fire to agent-resolved | Decreasing |
| **Auto-resolution rate** | % of incidents resolved without human involvement | Increasing (up to a safe ceiling) |
| **False positive rate** | % of automated remediations that did not actually help | Decreasing |
| **Rollback success rate** | % of rollbacks that caused error rate to return to baseline | Should be > 95% |
| **Alert noise reduction** | # pages per on-call shift before vs. after | Decreasing |
| **Mean time to escalate** | Time from incident start to human being paged (when escalation needed) | Decreasing |
| **Error budget impact of automation** | How much error budget was consumed by *failed* automated actions | Should be < 10% of total budget consumed |

The last metric is particularly important: if your automation is consuming a significant fraction of your error budget through failed remediations, it is making things worse, not better.

---

### Concept: AI-Assisted Postmortems

A **postmortem** (also called an incident review or after-action review) is a structured document that answers:
- What happened?
- Why did it happen?
- What did we do to fix it?
- How do we prevent it from happening again?

Postmortems are high-value but time-consuming. SREs often delay writing them because by the time the incident is resolved, they are exhausted.

An AI agent has a significant advantage here: it was *present* for the entire incident. It observed every alert, ran every diagnostic, and executed (or proposed) every action. It can produce a first-draft postmortem automatically.

#### What an Agent Can Draft

```markdown
## Incident Postmortem — Draft (AI-generated, requires human review)

**Incident ID:** INC-2025-1142
**Service:** payment-svc
**Severity:** SEV-2
**Duration:** 18 minutes (14:32 – 14:50 UTC)
**Auto-resolved:** Yes (rollback)

### Timeline
- 14:32 — payment-svc error rate crossed 5% threshold (canary deployment)
- 14:32 — Agent correlated with cart-svc latency spike (common deployment window)
- 14:33 — Agent retrieved last deployment: v1.4.2 deployed at 14:24 UTC
- 14:33 — Dry-run rollback confirmed: revert v1.4.2 → v1.4.1
- 14:34 — Operator approved rollback via Slack
- 14:35 — Rollback initiated
- 14:38 — Error rate returned to baseline (0.3%)
- 14:50 — Incident resolved; monitoring window closed

### Root Cause
Regression introduced in v1.4.2: null-pointer exception in payment processing
path when cart total exceeds $10,000 (edge case not covered by unit tests).

### Action Items
1. [Engineering] Add unit test for cart total > $10,000 edge case
2. [Reliability] Add this failure mode to the canary smoke-test suite
3. [Process] Review why edge case was not caught in staging

### Agent Performance
- MTTR: 18 minutes (vs. 47-minute team average for this class of incident)
- Approval gate used: Yes (operator approved rollback)
- False diagnostic steps: 0
```

The human on-call reviews this draft, corrects any inaccuracies, and publishes it. Time spent: 10 minutes instead of 90.

The action items from postmortems feed back into:
- Runbook updates (encode the new diagnostic steps).
- Test suite additions (catch the edge case earlier).
- Threshold adjustments (maybe the canary smoke test should catch this).

This creates a **feedback loop**: incidents improve the system, which reduces future incidents.

---

### Concept: On-Call Augmentation and Escalation Policies

#### The On-Call Problem

On-call work is one of the most common sources of SRE burnout. Teams with poor on-call hygiene see:
- Engineers woken multiple times per night.
- Alert fatigue — engineers stop investigating alerts carefully because there are too many.
- Knowledge concentration — only one or two engineers know how to respond to specific incidents.

An agentic SRE helps with all three:

1. **Fewer pages:** Agent handles or suppresses the noise.
2. **Faster resolution:** Agent runs the first diagnostic steps while the engineer is waking up.
3. **Knowledge democratization:** Runbooks encoded in the agent are available to any on-call engineer, not just the one who originally wrote them.

#### Escalation Policies — What the Agent Controls

An escalation policy defines:
- Who gets paged first (primary on-call)?
- If they don't respond in N minutes, who is paged next (secondary)?
- After what duration does a SEV-2 become a SEV-1 (management notification)?

The agent can make intelligent decisions about escalation:

- If the incident matches a known runbook and the agent has high confidence in the diagnosis → page primary on-call with a rich summary (not just "alert fired").
- If the incident is novel (no matching runbook, low confidence) → escalate faster, include more diagnostic context.
- If it is 3 a.m. on a Sunday and the action required is low-risk → agent resolves autonomously (Level 3) and notifies async.
- If the incident is cross-service (multiple teams involved) → open a war-room bridge and page multiple teams simultaneously.

---

### Demo Extension: Agent Files a Ticket and Drafts a Postmortem

```python
# Extension of demo_self_healing.py — Session 12 additions

def create_pagerduty_incident(title: str, body: str, severity: str) -> str:
    """Simulate creating a PagerDuty incident (real version calls PD API)."""
    incident_id = "INC-2025-DEMO-001"
    print(f"[PagerDuty] Created incident {incident_id}: {title} [{severity}]")
    return incident_id

def add_timeline_note(incident_id: str, note: str):
    """Simulate adding a note to a PagerDuty incident."""
    print(f"[PagerDuty] [{incident_id}] Timeline: {note}")

def draft_postmortem(incident_id: str, timeline: list, root_cause: str,
                     resolution: str) -> str:
    """Generate a postmortem draft using an LLM (simplified here as a template)."""
    postmortem = f"""
## Postmortem Draft — {incident_id}

### Timeline
""" + "\n".join(f"- {entry}" for entry in timeline) + f"""

### Root Cause (AI hypothesis — requires human verification)
{root_cause}

### Resolution
{resolution}

### Action Items
[ ] Review agent reasoning log for accuracy
[ ] Update runbook with any new diagnostic steps discovered
[ ] Add regression test for identified failure mode
"""
    return postmortem

def resolve_pagerduty_incident(incident_id: str, note: str):
    """Simulate resolving a PagerDuty incident."""
    print(f"[PagerDuty] Incident {incident_id} resolved. Note: {note}")

# --- Extended agent run with ITSM integration ---

def run_sre_agent_with_itsm(deployment: str):
    timeline = []

    # Create incident immediately
    incident_id = create_pagerduty_incident(
        title=f"{deployment}: high error rate post-deployment",
        body="Automated triage in progress.",
        severity="error"
    )

    timeline.append(f"Agent created PagerDuty incident {incident_id}")

    # ... (same diagnostic logic as Session 11 demo) ...
    metrics = get_canary_metrics(deployment)
    deploy_time = get_last_deployment_time(deployment)
    timeline.append(f"Error rate: {metrics['error_rate']:.1%}. Last deploy: {deploy_time}")

    add_timeline_note(incident_id, "Agent completed initial diagnostics. Proposing rollback.")
    timeline.append("Agent proposed rollback. Awaiting approval.")

    approved = request_approval(f"roll back {deployment}")
    if approved:
        result = execute_rollback(deployment)
        timeline.append(f"Rollback executed: {result}")
        add_timeline_note(incident_id, f"Rollback executed: {result}")

        # Draft postmortem
        pm = draft_postmortem(
            incident_id=incident_id,
            timeline=timeline,
            root_cause=f"Regression in {deployment} introduced in latest deployment, "
                       "causing elevated error rate on affected code path.",
            resolution="Rollback to previous stable version. Error rate returned to baseline."
        )
        print("\n=== POSTMORTEM DRAFT ===")
        print(pm)

        resolve_pagerduty_incident(incident_id, "Resolved via automated rollback.")
    else:
        add_timeline_note(incident_id, "Rollback declined. Escalating to secondary on-call.")

# Reuse tool functions from Session 11 demo
from demo_self_healing import (get_canary_metrics, get_last_deployment_time,
                                 dry_run_rollback, execute_rollback, request_approval)

if __name__ == "__main__":
    run_sre_agent_with_itsm("payment-svc")
```

---

### 💬 Discussion & Case Questions

1. **Alert fatigue is cultural, not just technical.** Even with an agentic SRE reducing pages by 70%, the remaining 30% might still be too many. What organizational and process changes complement the technical solution?

2. **The postmortem feedback loop.** An AI-generated postmortem draft is published without human review. What are the risks? Under what conditions (if any) is fully automated postmortem publishing acceptable?

3. **PagerDuty AI vs. home-built agent.** PagerDuty's commercial AI does much of what you built this week, out of the box. Why would a team choose to build their own instead of buying? What are the tradeoffs?

4. **Runbook rot.** Runbooks go out of date. A microservice's behavior changes but nobody updates the runbook. The agent follows the old runbook and makes things worse. How do you prevent runbook rot?

5. **On-call equity.** If the agent handles most incidents autonomously, junior engineers lose the opportunity to learn from incident response. How would you design an agentic SRE system that also serves as a learning tool for the team?

---

### 🔑 Key Terms — Session 12

| Term | Definition |
|---|---|
| **Alert storm** | A flood of alerts triggered by a single root cause event, where each downstream service fires independently. |
| **Alert suppression** | Silencing redundant alerts that are symptoms of a known, already-open incident. |
| **Alert correlation** | Grouping related alerts into a single incident based on causal dependencies or temporal co-occurrence. |
| **Agentic runbook** | A runbook encoded in structured (e.g., YAML) or natural-language form that an agent can execute as a series of tool calls. |
| **ITSM** | IT Service Management — tools and processes for tracking and managing incidents, changes, and service requests. |
| **PagerDuty** | A popular on-call alerting and incident management platform, with APIs the agent can call to create, update, and resolve incidents. |
| **ServiceNow** | An enterprise ITSM platform used for change management, incident tracking, and CMDB (Configuration Management Database). |
| **Postmortem** | A structured document reviewing what happened during an incident, why, how it was resolved, and what actions prevent recurrence. |
| **Escalation policy** | Rules defining who gets paged, in what order, and after how long, when an incident is not acknowledged or resolved. |
| **MTTR** | Mean Time To Recover — average time from incident start to resolution. The primary metric for incident response effectiveness. |
| **Auto-resolution rate** | The percentage of incidents resolved by the agent without human intervention. |
| **Alert noise** | Alerts that fire frequently but do not require (or do not receive) meaningful human action. Contributes to on-call fatigue. |
| **Runbook rot** | The gradual degradation of runbook accuracy as the system changes but the runbook is not updated. |
| **Feedback loop** | The cycle where postmortem action items improve the system, which reduces future incidents. |

---

### ⚠️ Common Pitfalls — Session 12

- **⚠️ Auto-resolving tickets without human verification.** If the agent resolves a PagerDuty incident automatically but the underlying issue is actually still present (false resolution), the customer impact continues while the team believes it is fixed. Always require at least a brief observation window after remediation before closing the incident.
- **⚠️ Publishing AI postmortems verbatim.** AI-generated postmortems may contain hallucinated "facts" about the incident timeline or root cause. Always mark them as drafts and require human sign-off before publishing to the team.
- **⚠️ Runbook coverage gaps.** The agent only performs as well as the runbooks it has access to. A runbook library with 80% coverage means 20% of incidents are handled without guidance — which increases the risk of bad autonomous decisions.
- **⚠️ ITSM credentials with too broad scope.** If the agent's PagerDuty API token can close *any* incident (not just the ones it opened), a bug in the agent could accidentally suppress real critical incidents. Scope ITSM credentials to the agent's service domain only.
- **⚠️ Ignoring the feedback loop.** Collecting postmortem action items and then not acting on them wastes the value of the postmortem entirely. Assign owners and deadlines; track them in a project management tool.

---

## Recap & Looking Ahead

### What You Accomplished This Week

This week completed the "agents in operations" arc of the course. You moved from *detecting* problems (Week 5) to *autonomously resolving* them — with the discipline to do so safely.

Key themes reinforced this week:
- **Guardrails are not optional.** Every autonomous action needs a blast-radius analysis, a rate limit, and a kill switch. This is as important as the action itself.
- **Transparency enables trust.** The ReAct loop's "thought" text makes agent reasoning auditable — this is what allows you to increase autonomy over time as you verify the agent is reasoning correctly.
- **The human stays in the loop for irreversible actions.** Approval gates are not a sign of distrust in the technology; they are responsible engineering practice.
- **Feedback loops compound.** Postmortems → runbook improvements → better agent performance → faster future resolutions. The value of the system grows over time.

### Looking Ahead: Week 7

[Week 7](week-07-notes.md) is the final week and the capstone of the course. You will apply everything you have learned to:

1. **Agentic Infrastructure-as-Code (IaC):** Using agents to generate, review, and apply Terraform/CloudFormation configurations — with Policy-as-Code (OPA) as a guardrail, similar to the approval gates you built this week.
2. **Internal Developer Platforms:** How organizations expose golden-path tooling through platforms like Backstage, and how agents integrate with them.
3. **AI Agent Security and Governance:** Prompt injection attacks, tool permission scoping, audit trails, and compliance — the governance layer that wraps everything you have built.
4. **Capstone presentation:** Demonstrating an end-to-end agentic DevOps pipeline — from commit, through CI/CD, to deployment, observability, and autonomous incident response — with appropriate guardrails at every stage.

The self-healing agent you built this week will be a component of that end-to-end capstone. Start thinking now about how you would wire it to your Week 3 CI/CD pipeline and your Week 5 anomaly detector.

---

## References

### Course Materials

- Syllabus: [`../syllabus/CSE636_Syllabus_v2.md`](../syllabus/CSE636_Syllabus_v2.md) — Week 6 section
- Kubernetes slides: [`../slides/Kubernetes.md`](../slides/Kubernetes.md) — controller pattern, Pods, architecture
- Automation overview: [`../slides/AI_Automation.md`](../slides/AI_Automation.md) — workflow automation, AI agent patterns

### External References

- **Anthropic — "Building Effective Agents"** (essential reading for this week — covers ReAct, tool use, guardrails, and agent design patterns): https://www.anthropic.com/engineering/building-effective-agents
- **Model Context Protocol (MCP)** — specification, Python SDK, and server examples: https://modelcontextprotocol.io
- **PagerDuty AI / Automated Incident Response**: https://www.pagerduty.com/platform/aiops/
- **PagerDuty API documentation** (for ITSM integration): https://developer.pagerduty.com/api-reference/
- **Google SRE Book** (free online, Chapter 14 on Managing Incidents, Chapter 15 on Postmortems): https://sre.google/sre-book/table-of-contents/
- **Kubernetes Operators — Official documentation**: https://kubernetes.io/docs/concepts/extend-kubernetes/operator/
- **OperatorHub.io** — catalog of community Kubernetes Operators: https://operatorhub.io
- **Anthropic Claude API — Tool Use documentation**: https://docs.anthropic.com/en/docs/build-with-claude/tool-use
- **ReAct: Synergizing Reasoning and Acting in Language Models** (original paper): https://arxiv.org/abs/2210.03629
- **OpenTelemetry GenAI semantic conventions** (for instrumenting your SRE agent): https://opentelemetry.io/docs/specs/semconv/gen-ai/
