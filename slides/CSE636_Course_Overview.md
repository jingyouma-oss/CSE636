# CSE 636 — DevOps with AI

### 1.5 Units · Fall 2025

**Lecturer:** Qingsong Zhang · qingsong.zhang@cstu.edu

California Science and Technology University

> Revised for the era of Agentic AI.

---

## From AI-Assisted to AI-Agentic DevOps

Students move beyond using AI as a passive assistant to designing agentic systems that perceive, plan, use tools, and act across the software delivery lifecycle — with guardrails and human oversight.

> **DevOps → DevSecOps → AIOps → Agentic DevOps**

---

## Course Description

This course explores how AI, ML, and autonomous AI agents are integrated into DevOps to automate, optimize, and enhance software development and operations.

**Hands-on experience with:**

- AI-assisted & agentic CI/CD pipelines
- AI coding agents and the Model Context Protocol (MCP)
- Predictive analytics & forecasting
- Intelligent monitoring & observability
- Autonomous incident response (agentic SRE)
- AI security and governance

---

## Learning Objectives

By the end of the course, students will be able to:

1. **Explain** how AI agents & ML augment DevOps across levels of autonomy (assistant → human-in-loop → human-on-loop → autonomous).
2. **Design & integrate** agentic automation into CI/CD pipelines, including MCP-connected tools.
3. **Use** predictive analytics & forecasting for reliability, performance, and cost (FinOps).
4. **Build** AI-/agent-driven monitoring, RCA, and autonomous incident response.
5. **Evaluate** AI agents, frameworks & protocols at scale — with security & governance guardrails.

---

## Course & Faculty Information

| Field | Details |
| ----- | ------- |
| **Lecturer** | Qingsong Zhang |
| **E-mail** | qingsong.zhang@cstu.edu |
| **Time** | Wed 7:30–9:00pm (Online) · Sat 9:00–10:30am (Onsite) |
| **Contact / Credit** | 23 Hours · 1.5 Units |
| **Office hours** | By Appointment |
| **Prerequisite** | Python; basic computing; Git & Docker recommended. No prior ML/LLM experience required. |

---

## Student Learning Outcomes

Assessed and reinforced in this course (not limited to):

- Communication
- Critical Thinking
- Information Literacy
- ML, AI, and AI-agent / agentic-systems fundamentals

> **Responsible AI-tool use:** students are expected to use AI agents in labs — and to disclose and critically evaluate their use.

---

## Textbook & References

**Supplementary text:** *Mastering ChatGPT and Prompt Engineering*

**Current references reflecting agentic DevOps:**

- Anthropic — Building Effective Agents · Claude Code docs
- Model Context Protocol (MCP) spec & SDKs
- OpenAI Platform docs · Google Agent Development Kit (ADK)
- OpenTelemetry GenAI semantic conventions
- DORA metrics · Platform Engineering (Backstage) · Open Policy Agent

---

## Evaluation & Grading

| Component | Weight |
| --------- | ------ |
| Case Discussions | 30% |
| Group Project | 20% |
| Final Exam | 20% |
| Mid-term Exam | 15% |
| Class Participation | 15% |
| **Total** | **100%** |

**Grade scale:**

> A+ 98–100% · A 93–97% · A- 90–92% · B+ 88–89% · B 83–87% · B- 80–82% · C+ 78–79% · C 73–77% · C- 70–72% · D+ 68–69% · D 63–67% · D- 60–62% · F < 60%

---

## The 7-Week Journey

> Foundations → Tooling → Pipelines → Prediction → Observability → Incident Response → Platform & Governance

13 sessions · weekly labs · weekly assignments · capstone project.

---

## Week 1 — Foundations of AI-Assisted & Agentic DevOps

**S1 · From DevOps to Agentic DevOps**

- Evolution & why agents matter now; assistants vs. agents vs. autonomous
- Anatomy of an agent: perception, planning, tools, memory, act–observe loop
- Case studies: Claude Code, Copilot agent mode, Cursor, Devin

**S2 · AI/ML & LLM Foundations**

- LLM capabilities: reasoning, tool/function calling, structured output
- DevOps data as agent context; RAG; context engineering; connecting via MCP

> **Lab:** cloud DevOps lab + run a coding agent on a sample repo · **Assignment:** report on 3 agentic-DevOps deployments

---

## Week 2 — AI Agent Tooling, Protocols & Platforms

**S3 · AI Coding Agents & Agentic Tooling**

- Claude Code, Cursor, Copilot, Devin, Codex; AIOps platforms (Datadog, New Relic, Dynatrace, PagerDuty)
- Capabilities, weaknesses, and when not to use an agent

**S4 · Agent Protocols, Frameworks & Environments**

- MCP servers/tools/resources; LangGraph, CrewAI, AutoGen, ADK
- Cloud agent services; agent permissions (least privilege, sandboxing)

> **Lab:** pipeline that invokes an agent + connect an MCP server · **Assignment:** compare frameworks + governance plan

---

## Week 3 — Agentic CI/CD Pipelines

**S5 · AI & Agents in Code Quality and Testing**

- Agentic code review & static analysis; AI test generation, self-healing tests
- Eval harnesses for AI-generated code

**S6 · Self-Optimizing & Self-Healing Pipelines**

- Agents that fix failing builds & open PRs; predictive build-failure detection
- Guardrails on autonomous merges: approval gates, blast-radius limits

> **Lab:** agent detects a failing build → proposes fix → opens PR (gated) · **Assignment:** CI pipeline that auto-remediates a failure class

---

## Week 4 — Predictive Analytics & Capacity Intelligence

**S7 · Risk Prediction & Deployment Intelligence**

- Predicting failed deployments; canary/blue-green with AI gating
- Agentic rollback decisions; deployment success scoring

**S8 · Capacity & Performance Forecasting**

- Forecasting infra usage; FinOps & cost optimization
- ML-driven autoscaling (predictive HPA, KEDA); time-series forecasting

> **Lab:** train a time-series model for CPU/memory → autoscaling decision · **Assignment:** AI forecasting for K8s autoscaling + cost

---

## Week 5 — Intelligent Monitoring, Observability & Agent Telemetry

**S9 · AI-Driven Anomaly Detection**

- ML on logs/metrics/traces; isolation forests + LLM-based detection
- Observability for agents: OpenTelemetry GenAI conventions — tokens, cost, latency

**S10 · Root Cause Analysis with AI Agents**

- Dependency mapping; log/trace correlation with LLMs; alert grouping
- Agentic RCA: investigate-and-report agents

> **Lab:** anomaly detector + instrument an agent with OTel GenAI · **Assignment:** anomaly detection → AI root-cause summary

---

## Week 6 — Autonomous Incident Response & Agentic SRE

**S11 · Self-Healing Systems & Agentic SRE**

- AI as a "virtual SRE"; autonomous rollback/failover with guardrails
- Agent reasoning loops (ReAct, reflection); blast-radius control

**S12 · Alert Triage, Runbooks & ITSM Integration**

- Intelligent suppression & correlation; agentic runbooks
- PagerDuty / ServiceNow / Opsgenie; AI-assisted postmortems

> **Lab:** Python agent (MCP tools) triages a simulated incident → gated remediation · **Assignment:** self-healing microservice with approval step

---

## Week 7 — Agentic IaC, Platform Engineering, Security & Governance

**S13 · Agentic IaC, Platform Engineering & AI Governance**

- Agents for Terraform/OpenTofu/CloudFormation; Policy-as-Code (OPA)
- Internal Developer Platforms (Backstage) & golden paths
- Agent security: prompt injection, permission scoping, sandboxing, secrets
- Supply-chain security (SLSA), audit trails, responsible-AI governance

> **Capstone:** agent-augmented IaC + end-to-end agentic DevOps project (pipeline → deploy → observe → auto-remediate, with guardrails)

---

## Academic Integrity & AI Tools

- All submitted work must be original or properly cited.
- AI coding agents/assistants are permitted and expected in designated labs — but must be disclosed.
- Students remain fully responsible for correctness, security, and originality of all submitted work, including AI-generated content.
- Using AI where prohibited (e.g., exams) is a policy violation.

---

## Welcome to CSE636

Let's build the agentic future of DevOps.

> Questions? Office hours by appointment · qingsong.zhang@cstu.edu
