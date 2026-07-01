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

# Week 2: AI Agent Tooling, Protocols & Platforms
## Coding agents, AIOps, MCP, orchestration & least-privilege
### CSE636 — DevOps with AI

Qingsong Zhang, Ph. D.

---

## 🎯 At a Glance

From *what* an agent is → *which tools exist* and *how agents connect* to the outside world.

| | |
|---|---|
| **Prerequisites** | Week 1 — agent anatomy, autonomy levels, tool-calling |
| **Time budget** | 2 sessions: ~2 hrs + ~1.5 hrs |
| **By the end** | Compare coding agents & AIOps; explain MCP + least-privilege; pick an orchestration framework |
| **You'll build** | Jenkins pipeline with an AI code-review stage + a working MCP server |

Populate the toolbox → connect an agent to a real tool.

---

<!-- _class: lead invert -->

# Foundations Primer
## Git & Docker — the base for every lab

---

## Why Version Control Exists

A **VCS** records snapshots of files over time, so you can:

- Rewind to any earlier snapshot
- See what changed between two snapshots
- Work in parallel without overwriting teammates
- Keep an authoritative, backed-up copy off your laptop

**Git** — distributed VCS (Torvalds, 2005). Every dev has the full history.
**GitHub** — cloud hosting for Git repos. Git is the engine; GitHub is the garage.

---

## Git: The Three-Area Model

| Area | Where | What it contains |
|---|---|---|
| **Working directory** | Your file system | Files you are editing |
| **Staging area** (index) | `.git/` | Changes selected for next commit |
| **Local repository** | `.git/` | All committed snapshots (full history) |

A **remote** (e.g. GitHub) is a 4th location — the shared copy.

```
Edit file  →  git add  →  git commit  →  git push
(working)     (stage)     (snapshot)      (share)
```

---

## Essential Git Commands

| Command | What it does |
|---|---|
| `git clone <url>` | Download a repo (full history) |
| `git status` | Show modified / staged / untracked |
| `git add <file>` | Stage changes |
| `git commit -m "msg"` | Save staged snapshot locally |
| `git pull origin main` | Fetch + merge from remote |
| `git push origin main` | Upload commits to remote |
| `git branch <name>` / `git checkout <b>` | Create / switch branch |
| `git merge <branch>` | Merge a branch in |

---

## Branches & Common Git Pitfalls

```bash
git branch feature/add-review-step    # create
git checkout feature/add-review-step  # switch
# ... commits ...
git checkout main
git merge feature/add-review-step     # merge back
```

Branch-per-change + merge via PR = foundation of Week 3 CI/CD.

- ⚠️ **Forgetting `git pull`** → stale copy, later conflicts
- ⚠️ **Committing secrets** → treat any leaked secret as compromised
- ⚠️ **Giant commits** → hard to review, impossible to revert cleanly

---

## Containers vs. VMs

Containers kill "it works on my machine" — app *and* dependencies in one portable unit.

| | Virtual Machine | Container |
|---|---|---|
| Isolation | Full OS per VM | Process-level (shared kernel) |
| Start time | Minutes | Seconds |
| Size | Gigabytes | Megabytes |
| Portability | Good | Excellent |
| Use case | Strong isolation, other OS | Microservices, CI/CD |

VMs use a hypervisor; containers use Linux namespaces + cgroups. Often run together.

---

## Docker Vocabulary & Build–Ship–Run

- **Image** — read-only template (recipe / class)
- **Container** — running instance of an image (object)
- **Dockerfile** — script that builds an image
- **Registry / Hub** — cloud store for images
- **Engine** — daemon that builds & runs containers

```
Developer                     Registry              Production
1 BUILD  docker build -t app .
2 SHIP   docker push app  ───────►  Docker Hub  ───► docker pull app
                                                      3 RUN docker run app
```

Same image runs identically everywhere.

---

## Docker Commands & a Minimal Dockerfile

| Command | What it does |
|---|---|
| `docker build -t <name> .` | Build image from Dockerfile |
| `docker run -d -p 8080:80 <img>` | Run detached, map host:container port |
| `docker ps` / `docker images` | List containers / images |
| `docker pull` / `docker push` | Download / upload image |
| `docker exec -it <name> bash` | Shell into a running container |

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]        # ⚠️ no root, no baked secrets, watch size
```

---

<!-- _class: lead invert -->

# Session 3
## AI Coding Agents & Agentic Tooling
### ≈ 2 hrs · Objectives: compare ≥5 agents · name AIOps agentic features · criteria for when *not* to use an agent · sketch a toolchain

---

## What is an AI Coding Agent?

A **chatbot answers**. An **agent acts**: reads/writes files, runs tests, calls the compiler, pushes commits, opens PRs.

- Executes a **multi-step plan** autonomously, with human review at checkpoints
- Like a capable contractor: give a task → it reads code, writes it, verifies, hands you a PR
- This is Week 1's **perceive → plan → act → observe** loop, applied to coding

You review and approve — or reject and redirect.

---

## The Competitive Landscape (2025)

| Agent | Made by | Autonomy |
|---|---|---|
| **Claude Code** | Anthropic | CLI; reads/edits, runs shell, MCP; HITL by default |
| **Cursor** | Anysphere | VS Code fork; agent mode needs approval for destructive |
| **Copilot (agent)** | Microsoft/GitHub | Multi-file changes, runs tests; changes shown as diffs |
| **Devin** | Cognition AI | Cloud "SW engineer"; more autonomous; still errs |
| **OpenAI Codex** | OpenAI | Cloud API + CLI; pure API is headless |

---

## A Closer Look: Claude Code, Cursor, Copilot, Devin

- **Claude Code** — terminal: reads → plans → edits + runs tests → reports the diff. Tunable autonomy; supports MCP.
- **Cursor** — AI *inside* the IDE; tight inline loop, but IDE-bound → weaker for headless CI.
- **GitHub Copilot** — issue → proposes changes → runs tests → opens a PR on GitHub Actions.
- **Devin** — higher autonomy: drives browser + terminal + editor toward a solution.

> ⚠️ **Higher autonomy ≠ higher reliability.** Devin still loops and writes plausible-but-wrong code. Human review remains essential.

---

## 💬 Quiz: Autonomy vs. Reliability

**Q:** "Devin is more autonomous than Claude Code, so it's the better tool for our production refactor." What's the flaw?

<details><summary>💡 Show answer</summary>

It conflates **autonomy with reliability**. More autonomy just means less human checking *by default* — not more correct output. For a high-blast-radius production refactor you want *more* review → favor human-in-the-loop, whichever tool is "more autonomous."

</details>

---

## AIOps Platforms with Agentic Features

**AIOps** = AI/ML applied to *operations*. Reactive (break → alert → human) → **proactive**: detect anomalies early, correlate alerts into one incident, predict capacity. New *agentic* twist: the AI **acts**, not just surfaces insight.

| Platform | Vendor | Agentic highlight |
|---|---|---|
| **Datadog Bits AI** | Datadog | NL query; RCA summaries; remediation steps; draft runbooks |
| **New Relic AI** | New Relic | Conversational; open tickets, trigger rollbacks, page on-call |
| **Dynatrace Davis** | Dynatrace | Causal AI; auto dependency map + RCA; Autopilot remediation |
| **PagerDuty AI** | PagerDuty | Noise reduction; incident summaries; recommended responders |

Capabilities: anomaly detection · prediction · root-cause analysis (↓ MTTR) · optimization.

---

## When NOT to Use an Agent

| Situation | Why risky | Better approach |
|---|---|---|
| Unclear / underspecified | Confidently does wrong thing | Clarify first; well-defined subtask |
| Irreversible changes | Delete / prod / DB, no undo | Human approval; staging; blast limits |
| Security-sensitive | Prompt-injection, leaks | Scope tightly; audit; no prod creds |
| Compliance / audit | May lack documentation | Human sign-off; log every action |
| Correctness critical, unverifiable | LLMs hallucinate | Run tests; human reviews diff |
| Novel / specialized domain | Lacks context | RAG/MCP; treat as first draft |

**Pre-deploy checklist:** blast radius? · reversible? · automated way to verify? · what (sensitive) data? · who approves before prod?

---

## 💬 Quiz: Run the Checklist

**Q:** A dev wants an agent to auto-delete cloud resources tagged "unused" to save money — no human review. Which red flags fire?

<details><summary>💡 Show answer</summary>

At least three: **blast radius** (deleting the wrong resource downs a live service), **reversibility** (deletes are often irreversible), **verifiability** (a stale "unused" tag can be wrong — no automatic test proves it's safe). Fix: human in the loop, dry-run first, limit to a reversible step (*stop* before *delete*).

</details>

---

## Building AI Toolchains

An **AI toolchain** = connected tools where an agent orchestrates work across systems.

```
Developer request
   │
   ▼
AI coding agent (Claude Code / Copilot)
   │  reads codebase (Git) → writes code → runs tests (CI)
   │  → lint/SAST → opens PR (GitHub API)
   ▼
Human reviewer (approval gate)
   ▼
CI/CD deploy → AIOps monitors → rollback agent on anomaly
```

The glue is increasingly **MCP** — one standard, not a connector per pair.

---

## Worked Example: Claude Code on a Repo

```bash
# Setup
npm install -g @anthropic-ai/claude-code
export ANTHROPIC_API_KEY=<your-key>
git clone https://github.com/pallets/flask.git demo-repo && cd demo-repo

# Explain structure
claude "What is the structure of this project? Summarize the main modules."

# Find issues
claude "Look at the error handling. Any exceptions swallowed silently?"

# Add a test — watch it read, write, run, iterate
claude "Add a unit test for url_for in routing. Run it to verify it passes."
```

**Observe:** reads many files first · runs the test itself · every write is a diff you approve. HITL in action.

---

## 🔑 Key Terms & Pitfalls — Session 3

| Term | Definition |
|---|---|
| **AIOps** | AI/ML applied to IT ops — monitor, alert, respond, plan |
| **Anomaly detection** | Deviation from a learned baseline (not static thresholds) |
| **RCA** | Finding the underlying cause, not the symptom |
| **MTTR** | Mean Time To Resolution — key reliability metric |
| **Blast radius** | Scope of damage if an automated action goes wrong |

⚠️ Over-trusting output · too much access too soon · picking tools by hype · ignoring latency/cost · no audit trail.

---

<!-- _class: lead invert -->

# Session 4
## Agent Protocols, Frameworks & Environments
### ≈ 1.5 hrs · Objectives: explain MCP · describe an MCP server · compare frameworks · name cloud agent services · apply least privilege

---

## MCP & the USB-C Analogy

Before MCP, every agent + tool pair needed a **custom integration** (Claude Code ↔ Jira, LangChain ↔ Jira, …) → the **N × M integration problem**. MCP defines a **standard protocol** — any agent speaks MCP to any MCP-wrapped tool, never learning its internal API.

| USB-C | MCP |
|---|---|
| Universal connector standard | Universal agent ↔ tool protocol |
| Any device charges from any adapter | Any MCP agent uses any MCP server |
| One cable spec, not one per pair | One server per tool, not one per agent |

Turns **N × M** into **N + M**: M servers + N clients.

---

## MCP Architecture

Three parties:

- **Host** — the agent app (Claude Code, LangChain app); decides when to call tools
- **Client** — inside the host; manages connections, handshake, auth, routing
- **Server** — lightweight process wrapping one system; declares its tools

```
┌─ MCP Host (agent app) ─────────────┐
│  LLM Core  ──  MCP Client          │
└──────────────────┬─────────────────┘
       JSON-RPC (stdio / HTTP+SSE)
   ┌───────────────┼───────────────┐
 GitHub server  Jenkins server  Postgres server
 (PRs, issues)  (build, logs)   (query rows)
```

---

## MCP's Three Primitives

**1. Tools** — functions the agent can call (name + description + JSON Schema input).

**2. Resources** — read-only data by URI (file, DB row, webpage, build log).

**3. Prompts** — pre-defined templates to use tools correctly (less common).

```json
{
  "name": "get_build_status",
  "description": "Returns status of the latest Jenkins build for a job.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "job_name": {"type": "string", "description": "e.g. 'backend-api'"}
    },
    "required": ["job_name"]
  }
}
```

---

## A Minimal MCP Server (Python)

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

app = Server("demo-jenkins-server")

@app.list_tools()
async def list_tools():
    return [Tool(
        name="get_build_status",
        description="Returns the last build result for a Jenkins job.",
        inputSchema={"type": "object",
            "properties": {"job_name": {"type": "string"}},
            "required": ["job_name"]})]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_build_status":
        job = arguments["job_name"]
        return [TextContent(type="text",
            text=f"Job '{job}': LAST BUILD SUCCESS (build #42)")]
```

Register it in Claude Code config, then "Is backend-api passing?" **calls the tool** instead of hallucinating:

```json
{ "mcpServers": { "demo-jenkins": {
    "command": "python", "args": ["/path/to/minimal_mcp_server.py"] } } }
```

MCP turns an agent into a **system actor** — real metrics, trackers, builds. Real power → permissions matter.

---

## Agent Orchestration Frameworks

One agent call isn't enough for "refactor, update docs, notify Slack, open a PR." Frameworks wire agents into workflows and teams.

- **LangGraph** — workflow as a **directed graph**; nodes = steps, conditional edges (tests pass → PR; fail → debug). Great for loops + HITL checkpoints.
- **CrewAI** — a **crew** of role-playing agents (Coder, Reviewer, Auditor) with goals; agents delegate + share memory.
- **AutoGen** (Microsoft) — **multi-agent conversation**; agents debate in natural language; humans can join.
- **Google ADK** — agents on **Vertex AI**; built-in tools, streaming, eval, multi-agent hierarchies.

---

## LangGraph Flow & Framework Comparison

```
Start → Planner → Code Editor ──► tests pass? ──yes──► Open PR (done)
                       ▲                │
                       └── Debug Agent ◄┘ no  (loop until green)
```

| Framework | Best for | Key concept | HITL |
|---|---|---|---|
| **LangGraph** | Workflows w/ loops & decisions | Directed graph | Pause/resume any node |
| **CrewAI** | Team tasks, specialist agents | Crew of roles | Human agent in crew |
| **AutoGen** | Conversational multi-agent | Agent dialogue | Human joins |
| **Google ADK** | GCP-native deployment | Tool-using on Vertex | Interrupt/approve |

---

## Cloud Agent Services

Managed: you bring task + tools; the cloud runs infra, memory, sessions, scaling.

| Service | Provider | Offers |
|---|---|---|
| **Bedrock Agents** | AWS | Knowledge bases (S3+vector), Lambda tools, Action Groups, IAM |
| **Vertex AI Agent Builder** | Google | RAG (GCS/BigQuery), function calling, ADK, Dialogflow CX |
| **Azure AI Foundry** | Microsoft | Azure OpenAI, AI Search (RAG), Functions, Copilot |

**Managed** = fast to prototype, no infra, built-in compliance.
**Self-hosted** = more control, no lock-in, on-prem / any model.

---

## Least Privilege for Agents

An agent should access only what its **current task** needs — nothing more.

Especially critical for agents because they can be:

1. **Prompt-injected** into unintended actions
2. **Misunderstand** instructions → wrong actions
3. Sending **sensitive data** to the LLM vendor

Practical controls: scoped tokens · short-lived creds · separate identity per agent · env vars (not hardcoded) · sandboxing · audit logging.

```bash
GITHUB_TOKEN = "ghp_abc123"                       # Bad — hardcoded
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]         # Good — from env
```

**Oversight spectrum:** human-in-the-loop (approves every action) → -on-the-loop (monitors, actions reversible) → -out-of-the-loop (autonomous, only bounded/reversible/low-blast). Default to **human-in-the-loop**; raise autonomy with evidence.

---

## 💬 Quiz: Least Privilege Fixes

**Q:** Your code-review agent has an admin token with write to *all* org repos "so it has what it needs." Name two least-privilege fixes.

<details><summary>💡 Show answer</summary>

Any two: **scope the token** to reviewed repos, read-only; **separate identity** per agent so a compromise can't deploy; **short-lived credentials**; pull the secret from **env / secrets manager**. Principle: grant only what *this task* needs — agents can be injected or act wrongly.

</details>

---

## Lab Preview: Connect an MCP Server

**Scenario:** Let Claude Code check the Jenkins build before a code change.

1. Stand up a Jenkins container (or reuse `project/Jenkins/`)
2. Create an MCP server wrapping the Jenkins REST API
3. Register it in Claude Code config (`~/.claude/claude.json` / `.claude/settings.json`)
4. Ask: "Is it safe to merge right now? Check the build status."
5. Observe the `get_build_status` tool call in the output

The agent queries **live** infrastructure — the foundation of agentic DevOps.

---

## 🔑 Key Terms & Pitfalls — Session 4

| Term | Definition |
|---|---|
| **MCP** | Open standard (Anthropic) for agent ↔ tool connection |
| **MCP Server** | Wraps one system; exposes declared tools/resources |
| **MCP Tool / Resource** | Callable function / readable data source |
| **Scoped token** | Credential limited to specific ops or resources |
| **Sandboxing** | Isolated env restricting host + network access |

⚠️ One giant server · long-lived secrets · no audit trail · trusting LLM to judge safety · skipping HITL · secrets in configs in Git.

---

## Recap: This Week's Takeaways

1. **The ecosystem is rich but fragmented** — tool choice follows workflow, not hype
2. **MCP is the connective tissue** — one server per tool; building them is a core skill
3. **Frameworks are for composition** — start simple, add complexity as you learn
4. **Permissions are not an afterthought** — design the permission model first
5. **Human oversight is a feature** — it builds the evidence to safely raise autonomy

**Next — Week 3:** put agents *inside* CI/CD — code review, test gen, self-healing builds behind approval gates.

---

<!-- _class: lead invert -->

# Questions?

Get your Jenkins pipeline + MCP server working before Week 3.
