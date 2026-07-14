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

# Week 3: Agentic CI/CD Pipelines
## Agents inside the pipeline — and the guardrails that keep autonomy safe
### CSE636 — DevOps with AI

Qingsong Zhang, Ph. D.

---

## This Week's Theme

Put AI agents **inside** the pipeline:

- Review code automatically
- Generate and heal tests
- Triage and fix broken builds
- Enforce guardrails so autonomy never outpaces oversight

**The pivot week:** Week 2 gave you the *tools* (MCP, agent frameworks). Now they move off the workbench and into the assembly line.

**By the end you can** wire an agent into every CI/CD stage — *and* make sure it cannot break production without a human saying so.

---

## Foundations Primer: Anatomy of a Pipeline

| Term | Plain-language meaning |
|---|---|
| **Pipeline** | Whole workflow, commit → deployed artifact |
| **Stage** | A named phase (Build, Test, Deploy) |
| **Step** | A single command inside a stage |
| **Job** | Jenkins unit holding one pipeline/script |
| **Runner / Agent** | Machine/container that runs the steps |
| **Controller** | Server that schedules jobs, stores results |
| **Artifact** | Output of a build — binary, image, zip |
| **Trigger** | Event that starts a run — push, PR, timer |

The **controller** is the factory manager; **agents** are the workers.

---

## CI vs. CD

- **CI (Continuous Integration):** every push is checked out, compiled, tested — problems found in minutes, not weeks.
- **CD (Continuous Delivery / Deployment):** if CI passes, package and push toward production — staging first, then users.

> Turns *"it works on my machine"* into *"it works, period — we checked."*

Ten developers, one codebase — the pipeline is the automated traffic cop.

---

## Jenkins — Declarative Pipeline

```groovy
pipeline {
  agent any
  stages {
    stage('Checkout') {
      steps { git 'https://github.com/org/repo' }
    }
    stage('Build') {
      steps { sh 'mvn clean package -DskipTests' }
    }
    stage('Test') {
      steps { sh 'mvn test' }
    }
    stage('Deploy') {
      steps { sh 'kubectl apply -f k8s/' }
    }
  }
}
```

Declarative = structured, readable. Scripted = free-form Groovy, more flexible, harder to read.

---

## GitHub Actions — Same Concepts, YAML

```yaml
name: CI
on: [push, pull_request]
jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: mvn clean package -DskipTests
      - name: Test
        run: mvn test
```

`stages` → **jobs**, steps-in-stage → **steps** in a job. Concepts identical; only syntax differs.

The course ships a runnable `project/Jenkins/` lab (`Dockerfile_Master` + Blue Ocean).

---

<!-- _class: lead invert -->

# Session 5
## AI & Agents in Code Quality and Testing

---

## Session 5 — Learning Objectives

By the end, you can:

1. Explain how an AI review agent differs from a rule-based linter.
2. Describe three approaches to AI test generation and their tradeoffs.
3. Define a *flaky test* and two agent strategies to eliminate flakiness.
4. Define an *eval harness* and why AI-generated code needs one.
5. Name 3+ AI-QA tools and map them to tasks.

---

## Static Analysis: Linter vs. Agent

**Static analysis** = inspecting code *without running it*.

- **Rule-based linters** (`pylint`, `eslint`, `semgrep`): fixed hand-written rules. Many false positives; cannot reason about *intent*.
- **AI agent** adds a reasoning layer — like a senior colleague:

> "This logic is technically correct, but returns the wrong answer when `user_list` is empty — here's a fix."

The agent can:
- Understand *purpose* from comments, names, tests
- Suggest an inline fix, not just a flag
- Learn from the project's own history

---

## How Agents Review a PR

The agent loop on a pull request:

1. **Perceive** — fetch the diff, full file context, tests, prior CI results
2. **Plan** — pick concern categories (correctness, security, style, coverage, perf)
3. **Act** — call tools: read files, look up guidelines, query past-review vector store
4. **Observe** — synthesize findings keyed to line numbers
5. **Report** — post inline comments via GitHub/GitLab API

**Human-in-the-loop:** the agent *proposes*; the human decides.

*ML classifiers (Infer, Pysa, bug predictors) say **where** to look; the LLM says **what** is wrong.*

---

## Worked Example: PR-Review Step

```yaml
# .github/workflows/pr-review.yml
name: AI Code Review
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  ai-review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write        # comment only — not merge
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0            # full history for diff context
      - name: Run AI code review
        uses: anthropics/claude-code-action@v1
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        with:
          prompt: "Review this PR for security, correctness, and test coverage. Post inline comments; do NOT merge."
          claude_args: >-
            --model claude-opus-4-8
            --allowed-tools "mcp__github_inline_comment__create_inline_comment,Bash(gh pr comment:*),Read"
```

Guardrail = `pull-requests: write` only (no merge) **+** branch protection requiring a human review. The agent comments; a person approves.

---

## AI Test Generation — Three Approaches

**1. Generation from code** — reads a function, reasons about edge cases, writes `pytest`/`JUnit` tests. (Copilot, Cursor, CodiumAI)

**2. Generation from specifications** — from a user story or OpenAPI contract, generate tests *before* the code exists. Agentic **TDD**.

**3. Mutation-guided generation** — inject small bugs (*mutations*); if a mutation survives, write a test that would catch it. Measures whether tests *exercise* logic, not just *call* it.

---

## Self-Healing Tests

Tests break two ways:
- **Real regression** — code changed intentionally → update the test
- **Brittle failure** — incidental change (CSS class, record ID, locator) → wastes engineering time

The agent's healing loop:
1. Read the failing test + error message
2. Read the relevant changed code
3. Decide: real regression, or brittle selector/ID?
4. If brittle → propose an update
   `findById("submit-btn-42")` → `findByRole("button", { name: /submit/i })`
5. Open a PR for human approval

*Tools: Applitools, Mabl, Testim, Playwright/Cypress LLM approaches.*

---

## Test Prioritization

Running a 45-min suite on a one-line typo fix is wasteful. Pick the tests *likely to matter*:

| Approach | How |
|---|---|
| **Coverage-based selection** | Run only tests overlapping changed lines (`pytest --co`, `jest --changedSince`, Bazel) |
| **Failure-prediction models** | Train on `(changed_files, failed_tests)`; predict likely failures — MSR: 40–70% time saved |
| **LLM semantic similarity** | Embed change + test names; run only semantically close tests |

---

## A Test Pipeline with Selection + Generation

```yaml
name: AI-Augmented Test Pipeline
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Identify changed files
        run: git diff --name-only origin/main...HEAD > changed_files.txt
      - name: AI test prioritization
        run: |
          python scripts/select_tests.py --changed changed_files.txt \
            --model gpt-4o --output selected_tests.txt
      - name: Run selected tests only
        run: pytest $(cat selected_tests.txt)
      - name: Generate missing tests (on PR)
        if: github.event_name == 'pull_request'
        run: python scripts/generate_tests.py --changed changed_files.txt --output tests/generated/
```

---

## Flaky Tests: Causes

A **flaky test** passes *and* fails on the same code, no source change. It erodes trust: "oh, it probably just flaked."

| Cause | Example |
|---|---|
| **Time dependencies** | `assert result == "2025-01-01"` fails at midnight |
| **Order dependencies** | Test B assumes Test A set up state |
| **External service calls** | Real API occasionally slow/down |
| **Concurrency / races** | Two threads write the same file |
| **Resource exhaustion** | Assumes memory/disk always available |
| **Non-deterministic data** | Unseeded UUID or shuffle |

Google: flaky tests cost thousands of engineering hours per year.

---

## What an Agent Does About Flakiness

1. **Detection** — monitor CI history; flag tests that flip pass/fail on the same SHA >2× in 30 runs. *(Data task, not LLM.)*
2. **Root-cause analysis** — LLM reads test code, flake logs, history; matches a cause category.
3. **Proposed fix** — concrete change: `datetime.now()`, `@pytest.mark.timeout(10)`, `mock.patch` the API. Opens a PR.
4. **Verification** — re-run the test 10× before merging.

> ⚠️ **Pitfall:** Agents tend to *hide* flakiness with retry loops. A retry-wrapped flaky test is still flaky — just harder to notice. Require a root-cause explanation.

---

## Coverage Is Necessary, Not Sufficient

**Code coverage** = % of lines/branches exercised. Useful proxy, not a definition of quality. *80% coverage can coexist with zero tests for the most dangerous paths.*

AI improves coverage two ways:

1. **Gap identification** — read uncovered lines, classify them (error path? edge case? dead code?), generate tests for the highest-risk ones.
2. **Semantic coverage** — check tests *assert meaningful things*. A test that calls a function but asserts nothing is "covered" but useless — flag it.

---

## Eval Harnesses — An Agent Can't Grade Its Own Homework

**Bootstrapping problem:** the agent generates code *and* the tests. If both come from the same agent, "all tests pass" just means "the agent agrees with itself."

An **eval harness** is a *separately maintained* framework — independent reference cases, fuzzing, formal contracts, golden-output comparisons — whose sole job is to verify AI-generated artifacts.

```
code change → Agent A writes tests → Eval Harness (independent):
                                       - contract tests (OpenAPI)
                                       - property fuzzing (Hypothesis)
                                       - golden-output regression
                                       - detects always-pass tests
                                     → eval score → human gate if low
```

It is **not** written by the agent it checks — an external signal the agent can't game.

---

## Quiz — Session 5

**Q1:** What can an AI review agent reason about that a linter fundamentally cannot?

**Q2:** An agent "fixes" a flaky test with `@retry(3)` and the build goes green. Why is that worse than leaving it red?

<details><summary>Discuss, then reveal</summary>

**A1: Intent & context.** A linter applies fixed patterns; an agent infers *purpose* from comments/names/tests — but is a *proposer* a human still judges.

**A2:** It **hides** the flakiness — the race/time/external fragility is still there, now masked, and can paper over a *real* intermittent bug. Name the root cause and prove it by re-running many times.

</details>

---

## Tools for AI-Enhanced QA

| Tool / Framework | Primary Use |
|---|---|
| **GitHub Copilot** | Inline test suggestions, PR review comments |
| **CodiumAI / Qodo** | Automated test generation from code |
| **SonarQube + AI** | Quality, security scans, ML-ranked findings |
| **Semgrep** | Lightweight static analysis; shareable rules |
| **Diffblue Cover** | Java unit-test generation |
| **Mabl / Testim / Applitools** | Self-healing UI/E2E tests |
| **Hypothesis** | Property-based testing (Python) |
| **Pynguin** | Research-grade Python test generation |
| **pytest-randomly + -repeat** | Detect order-dependent / flaky tests |
| **jest --changedSince / Bazel** | Test impact analysis |

---

<!-- _class: lead invert -->

# Session 6
## Self-Optimizing & Self-Healing Pipelines

---

## Session 6 — Learning Objectives

By the end, you can:

1. Describe how an agent triages a failing build, proposes a fix, opens a PR.
2. Explain two ML techniques that cut CI execution time.
3. Define *predictive build-failure detection* and sketch its training.
4. Describe how AI improves cache hit rates and artifact reuse.
5. **Explain the guardrails for autonomous merges — approval gates and blast-radius limits — and why they're non-negotiable.**

---

## The "Fire Alarm" Problem

A build fails. Red in Slack. On-call sees **47 failing steps in 3 pipelines** and sifts thousands of log lines by hand.

> The alarm goes off — but you still have to find the fire yourself.

A **build triage agent** turns "find it yourself" into a reasoned diagnosis in minutes.

```
1 Failure → 2 Collect → 3 Reason → 4 Propose → 5 Open PR → 6 Wait
 (red sig)  (logs,diff, (root      (minimal   (PR-scope   (human
             history)   cause)      fix)        token)      approves)
```

---

## Build Triage Agent — The Six Steps

1. **Receive** the failure signal (webhook or poll)
2. **Collect evidence** — full log, diff since last green, `Dockerfile`/deps changes, similar past failures
3. **Reason** — group errors (compile, test, timeout, missing dep, config), find likely cause
4. **Propose** — minimal code/config change
5. **Open a PR** — branch + commit + structured description
6. **Wait for human approval** — it does not merge. It *cannot* merge.

**Step 6 is the guardrail.**

---

## Build-Fixer Agent (Pseudocode)

```python
def handle_build_failure(build_id, repo):
    client = anthropic.Anthropic()
    log = ci_api.get_build_log(build_id)[-5000:]
    diff = git_api.get_diff_since_last_green(repo)
    history = ci_db.get_similar_failures(log[:500], limit=5)

    message = client.messages.create(
        model="claude-opus-4-8", max_tokens=2048,
        system="""You are a CI triage agent... propose the minimal fix.
        Output JSON: {root_cause, fix_description, files_to_change}.
        Never touch production config or deployment files.""",
        messages=[{"role": "user",
                   "content": f"Log:\n{log}\n\nDiff:\n{diff}\n\nHistory:\n{history}"}])

    fix = parse_json(message.content[0].text)
    gh = github.Github(os.environ["GH_PR_TOKEN"])   # least-privilege token
    branch = f"bot/fix-build-{build_id}"
    create_branch_and_commit(gh.get_repo(repo), branch, fix["files_to_change"])
    pr = gh.get_repo(repo).create_pull(title=..., head=branch, base="main")
```

The token holds `pull_request:write` **only** — cannot push to `main`, delete branches, or deploy. Least privilege at the token level, not "I promise not to."

---

## ML to Reduce Pipeline Time

Why speed matters: DORA shows high performers keep change lead time **under one hour**. A 45-min pipeline is one engineers learn to ignore.

**A. Selective execution** — skip provably irrelevant tests *and* build steps (no `frontend/` change → skip frontend build). ML beats simple path-globs.

**B. Dynamic resource allocation** — a README change and a payment-service change need very different CPU/memory. A model trained on `(changed_files, resource_used, build_time)` provisions the exact runner size.

```
docs/ only → resource-predictor (2 min, 1 vCPU → t3.micro)
           → selective-exec (skip frontend+backend suites, run markdown lint)
```

*GitHub Actions: self-hosted runners. Jenkins: Kubernetes plugin (per-job pods).*

---

## Predictive Build-Failure Detection

Triage is *reactive* — after failure. Prediction is *proactive* — estimates failure probability *when the PR opens*.

High predicted risk → run a broader suite early, warn on the PR, or route to a senior reviewer.

| Feature | Why |
|---|---|
| # changed files | More files → more coupling |
| Files changed (encoded) | `auth.py` riskier than `README.md` |
| Time since last change | Stale files → brittle coverage |
| Author failure rate | Targeted guidance, not penalty |
| Past failures nearby | High bug-density regions |
| Coverage of changed lines | Low coverage → riskier |
| Day / time | Friday-afternoon deploys are a meme |

Output = probability; threshold (e.g. 0.7) triggers the warning.

---

## Caching & Artifact Management with AI

Cache too aggressively → stale artifacts. Too conservatively → recompile every time.

AI improves cache utilization three ways:

1. **Cache key optimization** — analyze which files *actually affect* each stage's output; generate a minimal, precise key → fewer needless misses.
2. **Artifact lifecycle** — delete never-downloaded artifacts; store frequently-reused ones closer to runners.
3. **Dependency change alerts** — on `requirements.txt`/`package.json` change, pre-warm the invalidated cache off-peak, before devs arrive.

---

## Guardrails: The Most Important Section

Everything so far is useful **only if it is safe.** The moment an agent can merge into `main`, blast radius jumps from *"a PR sits in the queue"* to *"production is broken."*

> Autonomy must grow incrementally, and **every new level of autonomy requires a corresponding guardrail.**

Two pillars:
- **Approval gates** — the human checkpoint
- **Blast-radius limits** — restrict what the agent can change

---

## Approval Gates — The Human Checkpoint

```groovy
stage('Human Approval Required') {
  steps {
    input message: 'Agent proposed a fix. Review PR and approve.',
          submitter: 'team-leads',   // only these can approve
          timeout: 60                // times out to ABORT, not auto-approve
  }
}
```

```yaml
  human-review:
    needs: agent-fix
    environment: production          # required reviewers must click Approve
    steps:
      - run: gh pr merge ${{ env.PR_NUMBER }} --squash
```

> ⚠️ **Never auto-approve on timeout.** "If nobody reviews in 30 min, auto-merge" defeats the gate. Leave the PR open and notify louder.

---

## Blast-Radius Limits

| Limit type | Example |
|---|---|
| **File scope** | Only `src/` + `tests/`; never `infra/`, `secrets/`, `Dockerfile` |
| **Size limit** | ≤ 50 lines per PR; larger needs human authorship |
| **Deployment scope** | Auto to `staging`; extra approval for `production` |
| **Rate limit** | ≤ 3 PRs/hour — prevents runaway loops |
| **Rollback-only** | In freeze/holiday, may only *roll back*, never forward |

Enforced at multiple layers: system prompt, CI config (branch protection, CODEOWNERS), and token scope (no `admin`).

---

## The Layered Guardrail Model

Concentric fences, not a single gate:

```
┌───────────────────────────────────────────────┐
│ ① Token permissions (cannot push to main)     │
│  ┌──────────────────────────────────────────┐ │
│  │ ② CODEOWNERS + branch-protection rules   │ │
│  │  ┌─────────────────────────────────────┐ │ │
│  │  │ ③ Agent system-prompt scope limit   │ │ │
│  │  │  ┌────────────────────────────────┐ │ │ │
│  │  │  │ ④ Human approval gate          │ │ │ │
│  │  │  │      [ AGENT ACTION ]          │ │ │ │
│  │  │  └────────────────────────────────┘ │ │ │
│  │  └─────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────┘ │
└───────────────────────────────────────────────┘
```

Outer fences catch mistakes even if inner ones fail. No single layer is trusted alone.

---

## Continuous Feedback Loops

A self-optimizing pipeline *learns* over time:

- **Failure-pattern database** — store every triage outcome (accepted/rejected); prompt/fine-tune future triage on it.
- **Coverage trend tracking** — if AI tests cut defect-escape rates, trust the generator more; if not, tune it.
- **DORA metrics dashboard** — Deployment Frequency, Lead Time, Change Failure Rate, MTTR — annotate when each agentic change landed. Makes ROI visible.

---

## Quiz — Session 6

**Q:** A team relies *only* on the agent's system prompt ("never modify infra files") to stay safe. Why is that fragile? What layers would you add?

<details><summary>Discuss, then reveal</summary>

A system prompt is a single **soft** layer — confusable, ignorable, and overridable by **prompt injection**; nothing outside the LLM enforces it. Add hard, external layers:

- **Scoped token** (no write to infra/main)
- **Branch protection + CODEOWNERS**
- **Human approval gate** before merge

Then a failure of any one fence is caught by the others.

</details>

---

## Common Pitfalls — Session 6

- **Auto-approve on timeout** — defeats the gate.
- **Single-layer guardrails** — system prompts can be bypassed (prompt injection); add token- and platform-level enforcement.
- **Feedback loop corruption** — rubber-stamp approvals poison the data; require a lightweight review checklist.
- **Runaway PR loops** — fix → CI fails → fix → PR → ... Rate-limit and add loop detection.
- **Ignoring DORA regressions** — if Deployment Frequency drops or Change Failure Rate rises after the agent, investigate now.
- **Scope creep via prompting** — "fix the build" ≠ "refactor the module." Narrow prompts + file-scope limits.

---

## Recap — Week 3

- **Code review agents** give contextual feedback linters can't — humans still make the final call.
- **AI test generation** cuts cost — but eval harnesses & independent verification are required to trust it.
- **Flaky detection & healing** saves hours — fix root causes, don't paper over with retries.
- **Build triage agents** automate "find the fire" — PR privilege strictly scoped, merge capability zero.
- **Predictive failure detection** shifts the pipeline reactive → proactive.
- **Guardrails** are not optional. Every level of autonomy needs a matching guardrail.

---

## Looking Ahead — Week 4

**Predictive Analytics & Capacity Intelligence.** This week's agents produce the telemetry and build history Week 4's models train on.

Week 4 forecasts *deployment failures* before they happen, predicts *capacity needs* hours/days ahead, and drives autoscaling + FinOps.

Think about before Week 4:
- What historical data does your CI pipeline produce for a deployment-risk model?
- At 50 builds/day, how many builds before a failure model is useful?
- How do you handle the cold-start problem for a brand-new project?

---

<!-- _class: lead invert -->

# Questions?

Try the build-fixer lab — detect a failure, propose a fix, open a PR behind a human-approval gate.
