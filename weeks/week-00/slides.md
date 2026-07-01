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

# Week 0: Getting Ready — A Beginner's On-Ramp
## Toolchain setup + core vocabulary before the course begins
### CSE636 — DevOps with AI

Qingsong Zhang, Ph. D.

---

## 🎯 At a Glance

| | |
|---|---|
| **Prerequisites** | None — this is the on-ramp |
| **Time budget** | ~2 hours (the lab); reading ~20 min |
| **By the end you can** | Use the five core words in plain language, run a tiny app end to end |
| **What you'll build** | Nothing new — you run the starter service through the whole DevOps loop |

> Optional-but-strongly-recommended pre-work. Do the lab *before* Week 1's first class.

---

## Why This Week Exists

- Labs move fast — by Week 4 you wire a forecasting model into an autoscaler
- Struggling with setup means falling behind on the **ideas** (the point)

**Two goals:**
1. **Install and verify the five tools** by running one tiny project end to end
2. **Meet the core words** — repo, commit, container, pipeline, agent

> You don't need deep understanding yet. Green checkmarks in the lab = ready for Week 1.

---

<!-- _class: lead invert -->

# 🧱 Foundations Primer

One paragraph, one analogy each. Week 1 expands all of them.

---

## Git & GitHub

- **Git** — tracks the history of your files (who, what, when)
- **Repository** — a folder tracked by Git
- **Commit** — a saved snapshot + a message describing the change
- **Branch** — a parallel line of work you can merge back
- **GitHub** — website that hosts repos so teams can share
- **Pull request (PR)** — a proposal to merge; where review + AI agents work

> **Analogy:** Git is "track changes" for a whole project. GitHub is the shared drive.

---

## Containers (Docker)

- **Container** — packages your app + everything it needs (language, libs, settings)
- Runs *identically* on your laptop, a teammate's, and production
- Kills *"but it works on my machine"*
- **Docker** — the common tool to build/run containers
- **Dockerfile** — the recipe to build one

> **Analogy:** A shipping container — a standardized box that fits every ship, truck, and crane.

---

## Pipelines & CI/CD

- **Pipeline** — an automated assembly line: build → test → deploy
- **CI** (Continuous Integration) — auto-test every change as it comes in
- **CD** (Continuous Delivery/Deployment) — auto-ready or auto-ship passing changes
- In this course: **GitHub Actions** — push code, watch a checkmark go green (or a red X)

> **Analogy:** A factory quality-control line — only changes that pass every check make it out the door.

---

## LLMs & AI Agents

- **LLM** — AI trained on huge text; reads, writes, summarizes, reasons about code
- **AI assistant** — answers your question, then **stops**; you act
- **AI agent** — takes **actions in a loop**: run commands, edit files, open PRs — observing each result

> **Analogy:** An assistant is a GPS showing the route. An agent is a self-driving car that takes you there.

**The spine of the course:** *assistant answers, agent acts.*

---

## ✅ Check Your Understanding

**Q:** An AI tool fixes a failing test — it edits the file, re-runs the tests, sees them pass, and reports done. Assistant or agent? What's the giveaway?

<br>

**A:** An **agent**. The giveaway: it *took actions in a loop* — edited, ran the tests, observed, decided it was finished. An assistant would only *tell you* what to change and stop.

---

## How the Five Tools Fit Together

```
   Your laptop                             GitHub (cloud)
 ┌──────────────────────────┐           ┌────────────────────┐
 │  Edit code in Git repo   │           │  GitHub Actions    │
 │        │                 │  git push │  (CI)              │
 │        ▼                 │ ────────► │   runs same tests  │
 │  Python: run tests/app   │           │        │           │
 │  Docker: build container │           │        ▼           │
 └──────────────────────────┘           │  ✅ green check     │
                                         └────────────────────┘
```

You do exactly this with the **starter service** in `project/starter/`.

---

## The Five Tools (and Why)

| Tool | What it is | Why the course needs it |
|---|---|---|
| **Git + GitHub account** | Version control + repo hosting | Labs are code in repos; agents work via PRs |
| **Python 3.12+** | The course language | Labs, starter app, forecasting/agent code |
| **Docker Desktop** | Builds/runs containers | Docker foundations; later labs run in containers |
| **AI coding agent** | LLM that acts on your repo | The whole point — you direct and audit it |
| **A place to run things** | Compute environment | Somewhere to run the labs |

> **Lowest-friction path:** GitHub Codespaces — Python + Docker pre-installed in the browser.

---

## "Am I Ready for Week 1?" Self-Check

- [ ] **GitHub account** + Git works (`git --version`)
- [ ] **Python 3.12+** installed (`python3 --version`)
- [ ] **Docker** runs (`docker --version`) — *or* using Codespaces
- [ ] Ran the starter: `make setup`, `make test` (pass), `make run` → `{"status":"ok"}` at `/health`
- [ ] Pushed starter to **my own repo**, saw the **CI check go green**
- [ ] Installed an **AI coding agent** and gave it one task
- [ ] Can explain in one sentence each: *repo, commit, container, pipeline, agent*

---

## 🔑 Key Terms

| Term | Plain-language definition |
|---|---|
| **Repository** | A folder whose change history is tracked by Git |
| **Commit** | A saved snapshot of files, with a message |
| **Branch** | A parallel line of work you merge back |
| **Pull request** | A proposal to merge; where review + agents operate |
| **Container** | A portable package of an app + all it needs |
| **Pipeline** | An automated build → test → deploy line |
| **AI assistant** | Answers your question, then stops |
| **AI agent** | Takes actions in a loop to reach a goal |

---

## ⚠️ Common Pitfalls

- **Skipping Week 0** — setup problems are the #1 reason students fall behind
- **Trying to understand everything now** — this is first exposure, not mastery
- **Installing but never verifying** — "installed" is not "working"; prove it end to end
- **Committing secrets** — never commit API keys/passwords; keep them in `.env` (git-ignored)

---

## Recap & Looking Ahead

**What this week gave you:**
- A **working toolchain** (Git, Python, Docker, an AI agent) proven end to end
- Five plain-language words: **repo, commit, container, pipeline, agent**
- The distinction the whole course turns on: **an assistant answers; an agent acts**

**Next — Week 1: Foundations of AI-Assisted & Agentic DevOps**
Full DevOps lifecycle, how LLMs work, the five parts of an agent, levels of autonomy.

---

<!-- _class: lead invert -->

# Questions?

Finish the lab and tick every self-check box before Week 1.
