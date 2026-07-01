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

# Week 1: Foundations of AI-Assisted & Agentic DevOps
## From "what is DevOps?" to "what is an AI agent that does DevOps?"
### CSE636 — DevOps with AI

Qingsong Zhang, Ph. D.

---

## By the End of Week 1

| | |
|---|---|
| **Prerequisites** | None (Week 0 setup helps but isn't required) |
| **Time budget** | 2 sessions: ~2 hrs + ~1.5 hrs |
| **You can** | Explain DevOps & the CI/CD lifecycle; define LLM, AI agent, and the four *levels of autonomy*; describe how agents connect to tools via MCP |
| **You'll build** | A cloud DevOps lab and your first AI-agent run |

> The most important Foundations section of the course. Every concept here is reused every subsequent week.

---

<!-- _class: lead invert -->

# Part A: DevOps & the CI/CD Lifecycle

---

## The Problem DevOps Solved

**The silo problem (circa 2005):**
- Devs write code on laptops, hand it off to a separate Ops team
- Ops has never seen the code — it breaks in production
- Nobody knows whose fault it is; weeks to fix

**DevOps** = tearing down that wall
- Portmanteau of *development* + *operations*
- Not a product or tool — a set of **cultural practices, workflows, and tools**
- Development and operations become a **single, shared responsibility**

---

## CAMS & the Three Ways

**CAMS model** — the spirit of DevOps:
- **C**ulture — shared responsibility and trust
- **A**utomation — eliminate manual, repetitive work
- **M**easurement — decide with data
- **S**haring — transparent knowledge, postmortems, tooling

**The Three Ways** — guiding principles:
1. **Systems thinking & flow** — optimize the whole pipeline
2. **Amplify feedback loops** — move problems earlier, where they're cheap
3. **Continuous experimentation** — safe-to-fail, blameless postmortems

---

## The DevOps Lifecycle: 8 Stages in a Loop

| Stage | What happens | Representative tools |
|---|---|---|
| **Plan** | Requirements, backlog | Jira, Azure Boards, Trello |
| **Code** | Branch, review, merge | Git, GitHub, GitLab |
| **Build** | Compile, package, containerize | Maven, Gradle, Docker |
| **Test** | Unit, integration, security | JUnit, Selenium, Snyk |
| **Release** | Approve & version artifact | Jenkins, GitLab CI, Spinnaker |
| **Deploy** | Staging → production | Kubernetes, ArgoCD, Ansible |
| **Operate** | Infra, config | Terraform, Puppet, Chef |
| **Monitor** | Performance, errors, cost | Prometheus, Grafana, Datadog |

Drawn as an **∞ loop** — Monitor feeds back into Plan. Never "done."

---

## CI/CD: The Automation Spine

```
  commit ─→ [ CI ] ─→ [ CD prep ] ─→ (human click?) ─→ production
             pull        always
             build       deployable
             test        state
```

- **Continuous Integration** — every push: pull, build, test, report in minutes
- **Continuous Delivery** — software always kept *ready*; a human clicks "deploy"
- **Continuous Deployment** — no click; every passing commit ships automatically

**Analogy:** an assembly line for software — only vehicles passing every check roll out.

---

## Quiz: Delivery or Deployment?

**Q:** A team auto-tests every commit, but a human still clicks "deploy" to send a release to production. Which is it?

<br>

**A:** Continuous **Delivery**.
- The software is *always kept ready* (CI + automated prep)
- A human still triggers the actual production release
- Continuous **Deployment** removes that click — every passing commit ships

---

## DevSecOps: Shift Left

**Security woven into every stage**, not a final gate.
**Shifting left** = move checks earlier, where fixes are cheap.

| Stage | Security check | Tools |
|---|---|---|
| Commit | Dependency scanning | Snyk, WhiteSource |
| Build | Static code analysis | SonarQube, Checkmarx |
| Deploy | Dynamic app security testing | OWASP ZAP |
| Operate / Monitor | Runtime threat detection | — |

Security is **everyone's** responsibility, not just the security team's.

---

<!-- _class: lead invert -->

# Part B: LLMs & AI Agents

---

## Machine Learning in One Slide

An **ML model** learns patterns from examples instead of explicit rules.

| Category | Learns from | Used for |
|---|---|---|
| **Supervised** | Labeled examples (input → output) | Prediction, classification, regression |
| **Unsupervised** | Unlabeled data | Clustering, anomaly detection |
| **Reinforcement** | Actions + reward signal | Game-playing, robotics, agent training |

---

## What is a Large Language Model?

An **LLM** is an ML model trained on enormous amounts of text.
- "Large" = training data (100s of billions of words) + parameters (billions–trillions)
- Reads a **prompt / context**, predicts the next **token**, one at a time
- *Generates* new text — not retrieval from a database

**Why it matters for DevOps — an LLM can:**
- Read a log file and explain what went wrong
- Write a Dockerfile or YAML pipeline from plain language
- Suggest a fix for a failing test
- Explain a Kubernetes error

**Foundation models** (GPT-4, Claude, Gemini) — general, then prompted/fine-tuned.

---

## Assistant vs. Agent: The Key Leap

| **AI Assistant** | **AI Agent** |
|---|---|
| Waits, answers, stops | Takes *actions* in the world |
| You decide what to do | Runs commands, calls APIs, edits files, opens PRs |
| One shot | Acts in a *loop*, observing each result |
| Has a prompt | Has a **goal** |

**Analogy:** a GPS that shows a map (assistant) vs. a self-driving car that steers (agent).

> An agent is an **LLM + a loop + tools + a goal**.

---

## The Perceive → Plan → Act → Observe Loop

```
        ┌──────────────────────────────────────────┐
        │                                          │
        ▼                                          │
   1. PERCEIVE   ──→   2. PLAN / REASON            │
   task, logs,        (LLM decides next step)      │
   code, alerts                │                    │
                               ▼                    │
   4. OBSERVE   ◀──   3. ACT (call a tool:          │
   read result         run, edit, open a PR)  ──────┘
```

Repeat until the goal is achieved **or a safety limit is hit.**

---

## Levels of Autonomy

| Lvl | Name | What it means | Example |
|---|---|---|---|
| 1 | **AI assistant** | AI suggests; human decides & acts | Copilot suggestion you accept |
| 2 | **Human-in-the-loop** | Agent acts, pauses for approval | Agent proposes PR; you merge |
| 3 | **Human-on-the-loop** | Agent acts; human monitors | Agent patches; SRE watches |
| 4 | **Fully autonomous** | Agent acts, no human | Auto-scale, auto-heal 24/7 |

```
  L1 → L2 → L3 → L4   as autonomy rises, blast radius grows
```

Most enterprise deployments live at **levels 2–3**. *Choose the right level per task.*

---

## Quiz: Which Level, and Why Risky?

**Q:** An agent that *auto-merges its own PRs into `main` with no human review* sits at which level?

<br>

**A:** Level **4 (fully autonomous)** for that action.
- Merging to `main` has a **high blast radius** — a wrong change reaches everyone
- LLM agents occasionally reason incorrectly
- Most teams keep code-merge at **level 2**; reserve level 4 for low-blast-radius actions

---

<!-- _class: lead invert -->

# Session 1: From DevOps to Agentic DevOps

---

## Evolution: Why More Than DevOps?

DevOps solved Dev/Ops silos — but scale broke it:
- **Security** still bolted on late
- **Ops drowning in data** — millions of log lines/hour, alert fatigue
- **MTTR** not improving with scale
- **Cognitive load** climbing

```
DevOps      DevSecOps      AIOps          Agentic DevOps
2009–       2012–          2017–          2024–
collab +    security in    ML reads       agents that
CI/CD       every stage    telemetry      plan & act
                           (detects,
                            doesn't act)
```

---

## AIOps: Intelligence Before Agents

**AIOps** = ML applied to operational data (logs, metrics, events).

Core functions:
- **Anomaly detection** — spot deviations from normal
- **Alert correlation** — group related alerts into one incident
- **Root cause recommendation** — rank probable causes
- **Noise reduction** — suppress duplicate/low-priority alerts

Tools: Dynatrace Davis, Datadog Bits AI, New Relic AI.

> AIOps is *reactive* and *analytical* — it tells you what's wrong. **It does not autonomously fix it.**

---

## The Agentic DevOps Shift

| Capability | Traditional | AIOps | Agentic |
|---|---|---|---|
| Follows predefined rules | Yes | Yes | Yes |
| Learns from data | No | Yes | Yes |
| Multi-step goal-directed action | No | No | **Yes** |
| Natural-language instructions | No | Partially | **Yes** |
| Adapts to novel situations | No | Partially | **Yes** |

An agent reads the error → searches the code → proposes a fix → opens a PR → waits for CI → reports back. **That's "agentic."**

---

## Assistants vs. Agents vs. Autonomous: Meet Alex

On-call engineer "Alex" across the spectrum:

- **Assistant:** "What does this error mean?" Alex explains. *You* decide.
- **Human-in-the-loop:** "DB overloaded — restart the pool?" You say yes.
- **Human-on-the-loop:** At 2 AM, Alex rolls back the bad deploy, Slacks you a summary. You review in the morning.
- **Fully autonomous:** Alex detects, diagnoses, acts, validates, documents — nobody woken up.

All four modes exist in real teams. The art is **matching the mode to the problem.**

---

## The Key Question: Blast Radius

**If the agent makes a wrong decision, how bad can it get?**

| Action | Blast radius | Verdict |
|---|---|---|
| Restart a read-only process | Low | Autonomous probably fine |
| Roll back a DB migration | High | Keep a human in the loop |
| Delete production data | Catastrophic | Agent shouldn't have permission |

⚠️ **Pitfall — "just automate it":** giving full autonomy because it *usually* works. The agent *will* hit a case outside its training distribution. **Design for failure first, autonomy second.**

---

## Anatomy of an AI Agent: 5 Components

1. **Perception** — the input context (task, log, diff, alert, cluster state)
2. **Planning & reasoning** — the LLM decides; **chain-of-thought** = think out loud
3. **Tool use** — functions the agent may call (function calling / tool use)
4. **Memory** — what it knows and can recall
5. **Act–observe loop** — act, observe, repeat until goal or limit

> *Garbage in, garbage out* — what the agent perceives limits what it can do.

---

## Component 3: Tool Use

An agent without tools can only output text. **Tools** let it act.

```
read_file(path)               # read source code or config
run_command(cmd)              # execute a shell command
create_pull_request(...)      # open a GitHub PR
query_metrics(query, range)   # query Prometheus
search_docs(query)            # search internal documentation
```

- The LLM decides *when* and *how* to call each tool, then reads the result
- **Function calling** (OpenAI) = **tool use** (Anthropic)

---

## Component 4: Memory

| Type | What it is | Example |
|---|---|---|
| **In-context (working)** | Current conversation/session | The log you pasted this session |
| **External (retrieved)** | Docs fetched when needed | Runbooks, architecture diagrams |
| **Persistent (episodic)** | State surviving sessions | Past incidents investigated |

**RAG (Retrieval-Augmented Generation)** = external memory: retrieve relevant chunks from a vector DB, inject into context before reasoning.

> How an agent "knows" a 500-page runbook without holding it all in context.

---

## Quiz: Match the Component

**Q:** Match each to its component:
(a) "read this 500-page runbook when relevant"
(b) "the agent calls `kubectl get pods`"
(c) "the LLM thinks step by step before acting"

<br>

**A:**
- (a) → **Memory** (external / retrieved, via **RAG**)
- (b) → **Tool use / function calling**
- (c) → **Planning & reasoning** (chain-of-thought)

Remaining: **Perception** (the input) and the **act–observe loop**.

---

## Key Challenges Agents Target

| Challenge | What it is | How agents help |
|---|---|---|
| **Toil** | Manual, repetitive, scales linearly | Handles pattern-based tasks in minutes |
| **Scale** | 1 platform team, 100 dev teams | Available to all at ~zero marginal cost |
| **MTTR** | Detect → diagnose → act (a DORA metric) | Compresses the loop from hours to minutes |
| **Cognitive load** | Systems too big for one head | A "second brain" that's read all the docs |

---

## Industry Landscape

| Agent | Vendor | Notable |
|---|---|---|
| **Claude Code** | Anthropic | Terminal agent; reads whole repo; human-on-the-loop by default; course reference |
| **Copilot Agent Mode** | GitHub | From autocomplete → *task*-level: issue → multi-file fix → PR |
| **Cursor** | — | VS Code fork; whole-codebase context; 30-file refactor from one instruction |
| **Devin** | Cognition AI | Highly autonomous: issue → env → fix → tests → PR, no intervention |

⚠️ **Benchmark ≠ production.** SWE-bench measures isolated tasks. Production is messier — don't extrapolate scores to readiness.

---

## Session 1 Pitfalls & Discussion

**Common pitfalls:**
- ⚠️ "DevOps is just tools" — without culture, tools nobody trusts
- ⚠️ "Fully autonomous = better" — depends on blast radius & risk tolerance
- ⚠️ "The agent is always right" — LLMs hallucinate; always audit
- ⚠️ Confusing AIOps (*recommends*) with agentic AI (*acts*)

**Discussion:** For each — which autonomy level would you allow?
- Bump a patch dependency on a non-prod branch
- Restart a pod in a dev cluster
- Roll back a **production** deployment
- Delete a 90-day-unused feature flag

---

<!-- _class: lead invert -->

# Session 2: AI/ML & LLM Foundations

---

## ML Categories for DevOps

| Type | DevOps examples |
|---|---|
| **Supervised** | Predict deploy success; classify log line "error vs. noise" |
| **Unsupervised** | Cluster logs into new error categories; anomaly detection |
| **Reinforcement** | Learn autoscaling policy; pick fastest CI test subset |

- LLMs are technically **self-supervised** — predict the next token, text is its own label
- **RLHF** — humans rate responses; the model learns what humans prefer
- **Foundation models** — shift from "one model per task" to "one model, many tasks"

---

## LLM Capabilities that Enable Agents

**Reasoning** — chain-of-thought: "think step by step," show intermediate steps → better *and* auditable.

**Tool / function calling** — chooses a tool; emits structured JSON:
```json
{ "tool": "run_command",
  "parameters": { "command": "kubectl get pods -n production", "timeout": 30 } }
```
The system *actually runs* it and returns the result to the LLM.

**Structured output** — constrained format (JSON/YAML) for downstream systems, no human needed.

---

## Quiz: Why Is a Tool Call Different?

**Q:** Why is a tool call (structured JSON) fundamentally different from an LLM merely *writing out* `kubectl get pods` as text?

<br>

**A:**
- A tool call is a structured request an external system **executes**, then feeds the **real result** back to the LLM
- Text that *describes* a command does nothing — nothing runs; the model only guesses the output
- Tool use is what lets an agent **affect and observe the real world**

---

## DevOps Data Sources as Agent Context

An agent is only as useful as the data it can perceive.

| Source | What it is | Agent use |
|---|---|---|
| **Logs** | Text records of events | Read to understand an incident; LLMs parse unstructured text |
| **Metrics** | Numeric time-series (CPU, latency p50/p95/p99) | Check thresholds, trends, confirm a fix |
| **Traces** | One request's path across services | Find the slow hop in a call chain |
| **Configs** | Desired state (Dockerfile, K8s, Terraform) | Read to understand a deploy; generate/modify |

---

## Reading Logs: Example

```
2025-03-15 14:32:01 ERROR [payment-service] Connection timeout to db-primary:5432
2025-03-15 14:32:01 WARN  [payment-service] Retrying (attempt 3/3)
2025-03-15 14:32:02 ERROR [payment-service] Max retries exceeded. Circuit breaker OPEN.
```

An agent reading this infers:
- The database is unreachable
- The payment service is circuit-broken
- **Next step:** check the database

LLMs read natural-language error messages, stack traces, and exceptions **without a rigid parser.**

---

## RAG for Operational Knowledge

Ops knowledge lives in docs: runbooks, postmortems, ADRs, wikis — and it **changes constantly**.

**RAG steps:**
1. Split docs into chunks → store as vectors in a vector DB
2. On a task, a *retriever* finds the most semantically relevant chunks
3. Inject those chunks into the context window
4. Agent reasons with trained knowledge **+** retrieved docs

**Analogy:** a briefing packet before the meeting — not memorizing the whole wiki.

---

## Quiz: Why RAG Over Retraining?

**Q:** Your runbooks change every week. Why is RAG better than retraining — and what if you relied on built-in knowledge?

<br>

**A:**
- RAG retrieves the *current* docs at query time — updates appear instantly, no retraining
- Built-in (training-time) knowledge can't know your private runbooks at all
- Anything it "knew" goes stale the moment a runbook changes → confident, out-of-date answers

---

## Prompting & Context Engineering

**A prompt** in agent systems = system prompt + user message + tool definitions + context + history → the **context window**.

**Effective prompting:**
1. Be specific — "summarize the last 10 error lines," not "look at the logs"
2. Provide context — system, environment, recent changes
3. Specify format — say "JSON," give an example
4. Define constraints — "do not modify /prod"
5. Ask for reasoning — "explain before suggesting a fix"

**Context engineering:** include the *most relevant* files, summarize long docs, use headings/delimiters/XML tags.

---

## Evaluation Basics

How do you know the agent works? Often no single "correct" answer.

| Approach | How | Good for |
|---|---|---|
| **Human eval** | Humans rate outputs | Subjective quality, complex tasks |
| **LLM-as-judge** | A separate LLM rates | Scale — thousands cheaply |
| **Deterministic checks** | JSON parses? PR passes CI? | Measurable, binary |
| **Task completion rate** | End-to-end without error? | Multi-step, clear success |

> Define your **success criteria before building the agent, not after.**

---

## How Agents Connect to Toolchains

**1. Direct API calls** — GitHub (PRs), Kubernetes (pods/scale), PagerDuty, Datadog

**2. CLI wrappers** — a `run_command(cmd)` tool:
```bash
kubectl get pods -n production --output json
terraform plan -var-file=prod.tfvars
docker build -t myapp:latest .
```

**3. Model Context Protocol (MCP)** — a standardized connector (studied deeply in Week 2)

---

## The Model Context Protocol (MCP)

MCP (open standard, from Anthropic) defines three concepts:
- **Tools** — functions the agent can call
- **Resources** — data the agent can read
- **Prompts** — reusable prompt templates

```
                    ┌─→ MCP server: GitHub   (create PR, read files)
   Agent            ├─→ MCP server: Jenkins  (trigger build, get logs)
 (MCP client) ─MCP──┤
                    ├─→ MCP server: Datadog  (query metrics, alerts)
                    └─→ MCP server: Kubectl  (get pods, scale)
```

**One MCP server per tool → any MCP agent can use it.** Think **USB for AI agents.**

---

## Quiz + Session 2 Pitfalls

**Q:** Why is "USB for AI agents" a fitting analogy for MCP?
**A:** A *standard connector* — build one server per tool, any MCP agent uses it. Removes the combinatorial explosion of bespoke glue per agent × tool.

**Pitfalls:**
- ⚠️ Treating LLM output as ground truth (hallucination)
- ⚠️ Ignoring context-window limits — use RAG + summarization
- ⚠️ Skipping evaluation across diverse scenarios
- ⚠️ **Prompt injection** — untrusted text with adversarial instructions (Week 7)
- ⚠️ **Permission creep** — scope agent credentials to the minimum

---

## Recap: What We Covered

- **DevOps** — cultural + technical practice; CI/CD is its automation backbone
- **DevSecOps → AIOps → Agentic DevOps** — security in every stage; ML on telemetry; autonomous multi-step agents
- **AI agent** — perceive → plan → act → observe, with tools, goals, memory
- **Levels of autonomy** — assistant → fully autonomous; choose by blast radius
- **LLMs** — reason, call tools, produce structured output
- **Data sources** — logs, metrics, traces, configs; **RAG** for org knowledge
- **MCP** — standardizes agent-to-tool connections

**Next — Week 2:** compare real coding agents, go deep on MCP, build an MCP-connected pipeline.

---

<!-- _class: lead invert -->

# Questions?

Complete the Week 1 lab and bring your CI build logs + system metrics — we'll feed them to agent tools in Week 2.
