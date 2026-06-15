# CSE636 — DevOps with AI · Teaching Notes

Classroom-ready lecture notes for **CSE636 DevOps with AI**, a 7-week graduate course at the California Science and Technology University (CSTU). These notes follow the **v2 (agentic) syllabus** — see [`../syllabus/CSE636_Syllabus_v2.md`](../syllabus/CSE636_Syllabus_v2.md).

> **Who these notes are written for.** They assume students have **little prior DevOps or AI background**. Every week starts from plain-language explanations, uses analogies before jargon, and includes short *Foundations* primers (Git, Docker, CI/CD, Kubernetes, observability) woven into the weeks where they're first needed. An instructor can teach directly from these notes; a motivated student can also read them as a study guide.

---

## How the course is structured

- An optional **Week 0** on-ramp ([`week-00/`](week-00/)) gets absolute beginners to a working toolchain *before* Week 1 — install + verify Git, Python, Docker, and an AI agent by running the [starter service](../project/starter/) end to end. It is pre-work, not part of the 13 graded sessions.
- **7 weeks**, **13 sessions** total.
- Weeks 1–6 have **2 sessions** each; Week 7 has **1 session** (Session 13).
- **Session timing** (assumed in the notes; adjust to your schedule):
  - **Session 1 of each week ≈ 2 hours** (the larger meeting).
  - **Session 2 of each week ≈ 1.5 hours.**
  - **Week 7's single session ≈ 2 hours.**
- Each session's agenda is broken into timed blocks that add up to its budget. Trim or expand the *discussion* and *demo* blocks first if you run long or short.

## The course arc (how the weeks build on each other)

The course tells one continuous story: **move from using AI as a passive assistant to designing autonomous AI agents that help run software delivery — safely.**

| Week | Theme | What students can do by the end |
|---|---|---|
| **0** *(optional pre-work)* | Getting Ready — A Beginner's On-Ramp | Have a working toolchain (Git, Python, Docker, an AI agent) and run a tiny app end to end; know the core vocabulary |
| **1** | Foundations of AI-Assisted & Agentic DevOps | Explain DevOps, the CI/CD lifecycle, what an LLM and an AI *agent* are, and the *levels of autonomy* |
| **2** | AI Agent Tooling, Protocols & Platforms | Compare AI coding agents and AIOps tools; connect an agent to a tool with **MCP**; manage agent permissions |
| **3** | Agentic CI/CD Pipelines | Put agents *inside* the pipeline — review code, generate tests, triage/fix failing builds behind approval gates |
| **4** | Predictive Analytics & Capacity Intelligence | Use ML forecasting for deployment risk, autoscaling, and cost (FinOps) |
| **5** | Intelligent Monitoring, Observability & Agent Telemetry | Detect anomalies in logs/metrics/traces, do AI root-cause analysis, and **observe the agents themselves** |
| **6** | Autonomous Incident Response & Agentic SRE | Build self-healing systems and an "agentic SRE" with guardrails and ITSM integration |
| **7** | Agentic IaC, Platform Engineering, Security & Governance | Generate infrastructure-as-code with agents; secure and govern agentic systems; tie it together in a capstone |

**Mental model used throughout:** an AI agent runs a loop — **perceive → plan → act (use a tool) → observe → repeat** — with a human kept *in the loop* (approves each step), *on the loop* (supervises and can intervene), or *out of the loop* (fully autonomous). Choosing the right level of autonomy for a given task, and putting **guardrails** around it, is the recurring theme of the course.

## How each week's files are organized

Each week is split into **two files** so the teaching material and the hands-on work stay separate. They cross-link to each other at the top.

```
weeks/
  README.md
  week-00/   week-00-notes.md   week-00-lab.md   (optional beginner on-ramp)
  week-01/   week-01-notes.md   week-01-lab.md
  week-02/   week-02-notes.md   week-02-lab.md
  …
  week-07/   week-07-notes.md   week-07-lab.md
```

**`week-NN-notes.md` — the lecture notes** (what you teach from):

1. **Week header** — theme, where it sits in the arc, what prior weeks it builds on.
2. **🧱 Foundations primer** *(only in weeks that introduce new base tooling)* — a short, beginner explainer drawn from the course slide decks.
3. **Sessions** — for each session: *learning objectives → timed agenda → concept explanations (with analogies) → worked example / live-demo steps → discussion & case questions → key-terms glossary → common pitfalls.*
4. **Recap & looking ahead** — ties the week to the next.
5. **References** — syllabus links plus relevant materials in this repository.

**`week-NN-lab.md` — the hands-on work** (what students do):

- **🧪 Lab** — the hands-on exercise for the week, with starter steps.
- **Assignment** — the graded out-of-class deliverable.
- *(Week 7 also carries the Capstone overview and Final Exam review here.)*

## Conventions

- **🧱 Foundations** callouts = prerequisite knowledge explained from scratch.
- **🧪 Lab** = hands-on, in-class or take-home exercise.
- **💬 Discussion** = case-study / open questions to run live.
- **⚠️ Pitfall** = a common beginner mistake or a safety concern.
- **🔑 Key terms** = a glossary at the end of each session.
- Code and commands are shown in fenced blocks; they're illustrative starting points, not turnkey solutions.

## Source materials in this repository

These notes reuse and point to existing course content:

- **Slide decks** (converted to Markdown in [`../slides/`](../slides/)): `DevOps.md`, `Git.md`, `Docker_101.md`, `Jenkins.md`, `Kubernetes.md`, `AI_Automation.md`, `n8n_tutorial.md`, and `Session 1_ Introduction to DevOps and AI Convergence.md`.
- **Syllabus**: [`../syllabus/CSE636_Syllabus_v2.md`](../syllabus/CSE636_Syllabus_v2.md).
- **Jenkins teaching setup** (runnable Docker lab): [`../project/Jenkins/`](../project/Jenkins/).

## Grading (from the syllabus)

| Component | Weight |
|---|---|
| Mid-term Exam | 15% |
| Group Project | 20% |
| Case Discussions | 30% |
| Final Exam | 20% |
| Class Participation | 15% |

> **Responsible AI-tool use.** Students are expected to *use* AI coding agents in labs and projects **and to disclose and critically evaluate** that use — verifying correctness, reviewing agent-generated changes, and noting failures. Undisclosed or uncritical reliance on AI output is handled under the Academic Integrity policy.
