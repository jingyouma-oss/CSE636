# Week 3 Class Demo — Claude Code as the CI/CD Agent in the Loop

**Date:** 2026-07-16
**Course:** CSE636 DevOps with AI — Week 3 (CI/CD)
**Status:** Approved design; ready for implementation planning

---

## 1. Summary

A class demo in which **Claude Code** is both the *orchestrator* and the *AI agent in the loop* of a CI/CD pipeline running on **local Jenkins** (`cstu-jenkins`, from Week 2).

An instructor hands Claude Code a requirements document (`REQUIREMENTS.md`). Claude Code reads it and autonomously:

1. Generates a Jenkins pipeline (inline `Jenkinsfile`) and **creates the job** via an MCP tool.
2. **Triggers** build #1 and polls status → **red** (a planted bug).
3. Pulls the **console log**, diagnoses the failing test and root cause.
4. Presents the minimal fix as a diff and **pauses for the instructor to approve** (human-in-the-loop gate).
5. On approval, applies the fix, **commits + pushes to `main`**, triggers build #2 → **green**.
6. Writes a **summary report** to `reports/run-NN.md`.

All Jenkins interaction happens **only through MCP tools** — no raw REST in the transcript, no GitHub REST contents API. Checkout is a normal `git` clone of the class repo; the fix is delivered by `git push`.

**Teaching point:** the AI agent operates the CI/CD system through a tool interface the way a human engineer would, but the human keeps control at the one decision that matters — approving the change. This is the difference between "AI that writes code" and "AI that operates infrastructure with guardrails."

## 2. Goals / Non-goals

**Goals**
- Show a *closed* CI/CD loop driven end-to-end by an agent: create pipeline → build → detect failure → diagnose → (gated) fix → verify green → report.
- Keep Jenkins access behind a small, typed **MCP tool surface** (extends Week 2's `jenkins_status.py`).
- Keep a **mandatory human approval gate** before any change is applied or pushed.
- Be **repeatable** in a classroom with a one-line reset.
- Be **mount-free**: no changes to how `cstu-jenkins` is run; no Docker volume/bind-mount edits.

**Non-goals**
- Not a replacement for the existing `project/build-fixer/` lab (SDK-script + Jenkins `input` gate). This is a parallel, Claude-Code-native demo.
- No autonomous merge/deploy; no production targets.
- No multi-service or matrix pipelines; one job, two stages.
- Not driving Jenkins via raw REST from Bash (explicitly routed through MCP).

## 3. Design decisions (settled during brainstorming)

| Decision | Choice | Why |
|---|---|---|
| Role of Claude Code | Orchestrator **and** in-loop agent, driven by a requirements doc | The ask: agent reads spec, builds pipeline, runs the fix loop |
| Jenkins interface | **Extend the MCP server** (`jenkins_status.py`, in place) | Reuses Week 2 work; clean, typed, teachable; keeps one canonical server |
| App under test | **Fresh minimal app** with a planted bug | No coupling to build-fixer's calculator |
| Autonomy | **Human approval gate** (in-conversation) | Keeps Week 3's guardrail/blast-radius teaching point |
| Source delivery | **GitHub SCM checkout of `main`**, mount-free | User has the project on the class GitHub repo; simplest setup |
| Fix delivery | Claude Code `git push` to `main` | Git works through the proxy; REST contents API is not used |
| Repeatability | Reset demo app to buggy state (revert fix commit) | Doubles as the "prove it's real" sanity check |

## 4. Architecture & components

### 4.1 Extended MCP server — `project/build-fixer/mcp_servers/jenkins_status.py`

Grow the existing server (currently `list_jobs`, `get_build_status`) with three tools:

| Tool | Verb | Endpoint | Notes |
|---|---|---|---|
| `create_job(name, pipeline_script)` | POST | `createItem?name={name}` | Body is a `flow-definition` `config.xml` wrapping an **inline** `CpsFlowDefinition` (the pipeline text Claude Code authors). Requires a **CSRF crumb**. |
| `trigger_build(job_name)` | POST | `/job/{name}/build` | Requires crumb. Returns queued/OK; caller polls `get_build_status`. |
| `get_build_log(job_name)` | GET | `/job/{name}/lastBuild/consoleText` | Plain-text console log for diagnosis. |

Cross-cutting requirements for the new tools:
- **CSRF crumb**: fetch `/crumbIssuer/api/json` and attach the crumb header to every POST. This is called out as a teachable detail.
- **Idempotent `create_job`**: if the job exists, either no-op with a clear message or update its config (decide in plan; default: report "already exists, updated config" via `POST /job/{name}/config.xml`).
- Consistent error strings matching the existing style (`Jenkins API error {code}.`).
- Same env/auth (`JENKINS_URL`/`JENKINS_USER`/`JENKINS_TOKEN`, `_auth()` helper).

The companion `test_jenkins_status.py` client is extended to exercise the new tools against a throwaway job so the whole surface stays verifiable without `claude.json`.

### 4.2 Fresh minimal app — `project/ci-agent-demo/app/`

- A tiny self-contained Python module + `pytest` with exactly **one planted bug** that fails exactly one test (a second test passes, so the report can show "1 failed, 1 passed" → "2 passed").
- Pure standard library; no heavy deps. `pytest` is already pre-installed in `cstu-jenkins`'s venv (per Week 2 image), so the pipeline needs no `pip install`.
- The bug is small and unambiguous (one wrong operator / off-by-one) so the diagnosis is crisp and the minimal-fix guardrail is easy to honor.

### 4.3 The pipeline (authored by Claude Code, created via `create_job`)

Inline declarative pipeline, two stages:
1. **Checkout** — `git url: <class repo https>, branch: 'main'` (credentials only if the repo is private).
2. **Test (expect red)** — `cd project/ci-agent-demo/app && pytest`; the stage surfaces a non-zero exit as a red build.

`agent any` (single-container `cstu-jenkins`). The exact Jenkinsfile text is a template in the plan; Claude Code may regenerate it from `REQUIREMENTS.md` at demo time.

### 4.4 The agent loop (Claude Code, per `REQUIREMENTS.md`)

```
read REQUIREMENTS.md
 -> author Jenkinsfile
 -> create_job (MCP)
 -> trigger_build (MCP); poll get_build_status until complete
 -> if RED: get_build_log (MCP); diagnose failing test + root cause
 -> PROPOSE minimal fix as a diff; WAIT for instructor approval   # gate
 -> on approval: edit source, commit, git push origin main
 -> trigger_build (MCP); poll until GREEN
 -> write reports/run-NN.md
 -> STOP after 2 failed fix attempts (guardrail)
```

### 4.5 Summary report — `project/ci-agent-demo/reports/run-NN.md`

Fixed structure: run metadata (timestamps, job name, build numbers), the failure (test name, assertion, root cause), the approved fix (diff + one-line rationale), verification (build #2 result), the MCP calls made (as an audit trail), and a short "what the human approved" line.

## 5. Deliverables

### 5.1 `project/ci-agent-demo/REQUIREMENTS.md` (the agent's input)

Written as a spec *to an agent*. Sections:
- **Objective & success criteria** — pipeline exists in Jenkins; a red build is produced and then driven to green; a report is written.
- **Constraints** — local Jenkins only; Jenkins touched **only via MCP tools**; the human approval gate is **mandatory**; minimal-fix-only.
- **Pipeline contract** — stages, must surface a red build, `main` checkout.
- **Agent-loop contract** — detect → diagnose → **propose & wait** → apply+commit+push → verify → report.
- **Report format** — the §4.5 structure.
- **Guardrails** — minimal change only; never force-push; never disable/delete tests to make it pass; stop after 2 failed attempts and hand back to the human.

### 5.2 `weeks/week-03/week-03-demo.md` (instructor runbook)

Follows the `weeks/` conventions (learning-path strip, 🎯 at-a-glance, `<details>` check-your-understanding, recap; a linked `.svg` in `weeks/week-03/images/` if a diagram helps). Two parts:
- **Setup (one-time, before class):** Jenkins up; API token in `.env`; register the extended MCP server in `claude.json`; confirm the demo project + planted bug are on `main`; local git push credentials configured; smoke-test the MCP tools with `test_jenkins_status.py`.
- **Run (live in class):** the single kickoff prompt to Claude Code; what to narrate at each step; where/how to approve the fix; the expected report; and the reset/"prove it's real" step (revert the fix → red again).

### 5.3 `project/ci-agent-demo/README.md`

Short orientation: what the demo is, the file layout, the **reset command** to restore the buggy state, and pointers to `REQUIREMENTS.md` and the runbook.

## 6. File layout

```
project/ci-agent-demo/                 # on main, with the rest of the course
├── REQUIREMENTS.md                    # deliverable A — Claude Code reads this
├── README.md                          # orientation + reset instructions
├── app/                               # fresh minimal app + pytest (planted bug)
│   ├── <module>.py
│   └── test_<module>.py
└── reports/                           # Claude Code writes run-NN.md here (gitkeep)
weeks/week-03/week-03-demo.md          # deliverable B — instructor runbook
weeks/week-03/images/                  # optional linked .svg for the runbook
project/build-fixer/mcp_servers/jenkins_status.py       # extended in place (+3 tools)
project/build-fixer/mcp_servers/test_jenkins_status.py  # extended to cover new tools
```

## 7. Prerequisites / environment

- `cstu-jenkins` running on `http://localhost:8080` (Week 2 image; venv has `pytest`).
- A Jenkins **user + API token**; stored in `project/build-fixer/.env` as `JENKINS_URL`/`JENKINS_USER`/`JENKINS_TOKEN` (gitignored).
- The extended MCP server registered in `~/.claude/claude.json` (per Week 2 Part 2).
- Local **git push** credentials (a GitHub PAT via git credential helper) so Claude Code can push the fix. Git works through the corporate proxy; the GitHub REST contents API does not — the design avoids it.
- Class GitHub repo reachable from the Jenkins container (CA already baked into the image). Public repo → no checkout credential; private → a `github-https` credential.

## 8. Risks & mitigations

| Risk | Mitigation |
|---|---|
| CSRF crumb handling breaks POSTs | `create_job`/`trigger_build` fetch and attach the crumb; covered by the test client |
| `git push` to `main` blocked by proxy or perms | Git (not REST) is used; verified in Week 2 that git push works. Fallback documented: per-run `agent/fix-N` branch |
| Repeatability: `main` ends fixed | Documented one-line reset (revert the fix commit / restore the file); doubles as the sanity check |
| Job already exists on re-run | `create_job` is idempotent (updates config) |
| Private-repo checkout needs creds | Runbook documents the `github-https` fallback |
| Build polling races (queued vs building vs done) | Poll `get_build_status`; treat null result as `IN_PROGRESS` (already handled) |

## 9. Success criteria (demo is "working")

- From a single instructor prompt, Claude Code creates the job, produces a red build, diagnoses it correctly, pauses for approval, and — only after approval — pushes a minimal fix that yields a green build, then writes a coherent report.
- No Jenkins access outside MCP tools.
- The demo can be reset and re-run in under a minute.

## 10. Out of scope / future

- Auto-merge, deployment, multi-branch, or matrix builds.
- Replacing the existing build-fixer lab.
- A fully autonomous (no-gate) variant — could be a follow-up contrast demo.
