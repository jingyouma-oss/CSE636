# Week 3: Agentic CI/CD Pipelines

![Course learning path with Week 3 (CI/CD) highlighted: 0 Setup, 1 Basics, 2 Tooling, 3 CI/CD, 4 Predict, 5 Observe, 6 Respond, 7 Govern.](learning-path.svg)

> 📝 **Lecture notes.** The hands-on lab and assignment for this week live in **[week-03-lab.md](week-03-lab.md)**.


**Theme:** Put AI agents *inside* the pipeline — review code automatically, generate and heal tests, triage and fix broken builds, and enforce guardrails so autonomy never outpaces oversight.

**Arc placement:** This is the pivot week. [Week 2](../week-02/week-02-notes.md) gave you the *tools* — MCP servers, agent frameworks, coding agents. Now those tools move off the workbench and into the assembly line. By the end of today you will understand how to wire an agent into every stage of a CI/CD pipeline *and* how to make sure it cannot break production without a human saying so. [Week 4](../week-04/week-04-notes.md) will build on this by adding predictive analytics: instead of reacting to failures after they occur, the pipeline will start forecasting them.

**Builds on:** [Week 2](../week-02/week-02-notes.md) — MCP protocol, agent tooling, permission management.

> 🎯 **At a glance**
>
> | | |
> |---|---|
> | **Prerequisites** | [Week 2](../week-02/week-02-notes.md) (MCP, agent tooling, least-privilege) |
> | **Time budget** | 2 sessions: ~2 hrs + ~1.5 hrs |
> | **By the end you can** | Put agents inside CI/CD — review code, generate/heal tests, triage builds — and design the **guardrails** (approval gates, blast-radius limits) that keep autonomy safe |
> | **What you'll build** | A build-fixer agent that detects a failure, proposes a fix, and opens a PR behind a human-approval gate (see the [lab](week-03-lab.md)) |

---

## 🧱 Foundations Primer: CI/CD Pipelines and Jenkins

*New to CI/CD? Start here. If you already know what a pipeline, stage, and runner are, you can skim this section.*

### What problem does a CI/CD pipeline solve?

Imagine ten developers each working on a different part of the same codebase. Without any coordination, the first moment they all merge their changes is the moment the application might stop working — and nobody knows whose change caused the breakage. A **CI/CD pipeline** is the automated traffic cop that catches problems early, systematically, and consistently.

- **CI (Continuous Integration):** Every time a developer pushes a commit, an automated system checks out that code, compiles it, and runs the tests. Problems are found within minutes of being introduced, not weeks later at release time.
- **CD (Continuous Delivery / Continuous Deployment):** If the CI checks pass, the same system automatically packages the software and pushes it toward production — first to a staging environment, then (in full CD) all the way to users.

The pipeline turns "it works on my machine" into "it works, period — we checked."

### Anatomy of a pipeline

| Term | Plain-language meaning |
|---|---|
| **Pipeline** | The whole automated workflow, from code commit to deployed artifact |
| **Stage** | A named phase inside the pipeline (e.g., *Build*, *Test*, *Deploy*) |
| **Step** | A single command or action inside a stage |
| **Job** | In Jenkins, the configurable unit that contains one pipeline or one freestyle script |
| **Runner / Agent** | The machine (or container) that actually executes the steps |
| **Controller** | The Jenkins server that schedules jobs, stores results, and talks to agents |
| **Artifact** | The output of a build stage — a compiled binary, a container image, a zip file |
| **Trigger** | The event that starts a pipeline run — a git push, a pull-request open, a timer |

A simple mental model: the **controller** is the factory manager who reads the assembly instructions (the `Jenkinsfile` or workflow YAML) and dispatches tasks to **agents** (the factory workers) who actually do the compiling, testing, and deploying.

### Jenkins in one page

Jenkins is one of the oldest and most widely deployed open-source CI/CD servers. You configure a pipeline by writing a **Jenkinsfile** — a text file that lives in your repository alongside your code. There are two styles:

**Declarative** (recommended for beginners): structured, readable, visual.

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

**Scripted** (for complex logic): free-form Groovy code with `node { stage('...') { ... } }` blocks. More flexible, harder to read.

### GitHub Actions in one page

GitHub Actions uses YAML files stored in `.github/workflows/`. Instead of "stages," it has **jobs**, and instead of "steps" inside a stage it has **steps** inside a job. The concepts are identical; only the syntax differs.

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

### The course's runnable Jenkins lab

The `project/Jenkins/` directory in this repository is a self-contained teaching setup. `Dockerfile_Master` builds an official Jenkins image with Docker CLI and the Blue Ocean plugin pre-installed. You can spin it up with:

```bash
cd /path/to/CSE636/project/Jenkins

# Build once
docker build -t cstu-jenkins -f Dockerfile_Master .

# Run with Docker Compose
docker compose up -d

# Get the initial admin password
docker exec cstu-jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Alternatively, `automate.py` does the same thing programmatically via the Docker Python SDK (`pip install docker`). This lab environment is optional for Weeks 2–4 — if you prefer GitHub Actions you can run the same pipeline concepts there for free. See the [Jenkins project README](../../project/Jenkins/) and the [Jenkins slide deck](../../slides/Jenkins.md) for further detail.

---

## Session 5: AI & Agents in Code Quality and Testing

**Session budget: ≈ 2 hours**

### Learning Objectives

By the end of Session 5, students will be able to:

1. Explain how an AI agent performs code review and ML-assisted static analysis differently from a rule-based linter.
2. Describe three distinct approaches to AI-driven test generation and articulate their tradeoffs.
3. Explain what a *flaky test* is, why it is costly, and describe two agent-based strategies to detect and eliminate flakiness.
4. Define an *eval harness* and explain why it is needed when testing AI-generated code.
5. Name at least three tools or frameworks used in AI-enhanced QA and map them to specific tasks.

### Timed Agenda

| Time | Activity |
|---|---|
| 0:00–0:10 | Welcome, recap of Week 2, and session overview |
| 0:10–0:35 | Concept: Agentic code review and ML-assisted static analysis |
| 0:35–1:00 | Concept: AI-driven test generation, self-healing tests, and test prioritization |
| 1:00–1:20 | Concept: Flaky tests — causes, costs, and agent remedies |
| 1:20–1:35 | Concept: Coverage measurement and eval harnesses for AI-generated code |
| 1:35–1:50 | Tools survey and live-demo walkthrough |
| 1:50–2:00 | Discussion questions |

---

### 5.1 Agentic Code Review and ML-Assisted Static Analysis

#### What is static analysis, and why should agents do it?

**Static analysis** means inspecting source code *without running it* — the way a copy editor reads a manuscript without performing the experiment described in it. Traditional static analysis tools (linters like `pylint`, `eslint`, `checkstyle`, or security scanners like `semgrep`) apply hand-written *rules*: "flag any SQL string constructed by concatenating user input." These rules are valuable but have two limitations: they generate many false positives (things flagged that are actually fine), and they cannot reason about *intent* — they cannot tell the difference between code that happens to look dangerous and code that is genuinely risky in context.

An AI agent adds a reasoning layer on top. Think of it as the difference between a spell-checker (rule-based) and a senior colleague who reads your code and says, "This logic is technically correct, but it will produce the wrong answer when `user_list` is empty — here is a fix." The agent can:

- Understand the *purpose* of the code from surrounding comments, variable names, and test files.
- Produce a suggested fix inline, not just a flag.
- Learn from the project's own history: if the team consistently writes helper functions for repeated patterns, the agent notices and suggests doing the same.

#### How agents perform code review in practice

When a developer opens a pull request (PR), the CI pipeline can trigger an AI agent review step. The agent typically follows this loop:

1. **Perceive:** Fetch the diff (the changed lines), the full file context, the test files, and any CI results from prior runs on this branch.
2. **Plan:** Identify the categories of concerns to check (correctness, security, style, test coverage, performance).
3. **Act:** For each concern, call tools — read related files, look up the project's coding guidelines, query a vector store of past code-review comments.
4. **Observe:** Synthesize findings into structured comments keyed to specific line numbers.
5. **Report:** Post inline comments on the PR via the GitHub/GitLab API.

This is a **human-in-the-loop** arrangement: the agent *proposes* comments; the human author reviews them and decides what to address before the PR is approved.

#### ML-assisted static analysis: a note on what "ML" adds

Some tools go beyond language models and train *task-specific classifiers* on historical bug data. Facebook's **Infer** (pointer-safety analysis) and **Pysa** (taint tracking) use interprocedural analysis trained on millions of real bugs. Google's internal "bug predictor" models which files are likely to contain bugs based on features like churn rate and past bug density — and assigns higher-priority code review to those files. These models complement LLM-based review: the ML classifier says *where to look*; the LLM agent says *what is wrong and how to fix it*.

#### Worked example: adding a GitHub Copilot agent review step

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
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0            # need full history for diff context

      - name: Run AI code review
        uses: anthropics/claude-code-action@v1   # illustrative
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          review_scope: "security,correctness,test-coverage"
          post_comments: true
          require_human_approval: true   # agent suggests; human approves
```

The `require_human_approval: true` flag is the **guardrail**: the agent cannot merge or close the PR. It can only write comments. A human reviewer must still click "Approve."

#### ✅ Check your understanding

**Q:** What can an AI review agent reason about that a rule-based linter (like `pylint`) fundamentally cannot?

<details><summary>💡 Show answer</summary>

**Intent and context.** A linter applies fixed pattern rules and can't tell genuinely risky code from code that merely *looks* risky. An agent reads surrounding comments, variable names, and tests to infer *purpose* — so it can say "this is correct but returns the wrong answer when `user_list` is empty, here's the fix" rather than just flagging a pattern. The trade-off: the linter is deterministic; the agent must be treated as a *proposer* whose comments a human still judges.

</details>

---

### 5.2 AI-Driven Test Generation, Self-Healing Tests, and Test Prioritization

#### Why testing is still hard (and why AI helps)

Writing good tests is tedious. A developer who spends four hours implementing a feature may face two more hours writing unit tests that cover all the edge cases. The result is often that test coverage is incomplete — not from laziness, but from time pressure and the difficulty of imagining all the ways code can fail.

AI agents attack this problem in three distinct ways:

**1. Generation from code.** Given a function, the agent writes test cases that cover the function's inputs, boundary conditions, and documented exceptions. Tools like GitHub Copilot, Cursor, and CodiumAI do this today. The agent reads the function signature and body, reasons about edge cases, and produces `pytest` or `JUnit` tests.

**2. Generation from specifications.** Given a user story or API contract (e.g., an OpenAPI YAML), the agent generates tests that verify the specification is met — even before the implementation exists. This is the agentic version of **Test-Driven Development (TDD)**.

**3. Mutation-guided generation.** The agent introduces deliberate small bugs (*mutations*) into the code and checks whether existing tests catch them. If a mutation survives undetected, the agent writes a new test that would have caught it. This is called **mutation testing**, and it measures whether your tests actually *exercise* the logic, not just *call* the function.

#### Self-healing tests

Tests break in two ways: the *code under test* changed intentionally (the right kind of breakage — update the test), or something *incidental* changed — a CSS class name, a test-data record ID, an element locator in a UI test. The second kind is called a **brittle test failure**, and it wastes enormous engineering time fixing tests that are nominally correct.

An AI agent can perform **test healing**: when a test fails because of an incidental change, the agent:
1. Reads the failing test and the error message.
2. Reads the relevant changed code.
3. Determines whether the failure indicates a real regression (a bug) or a brittle selector/ID.
4. If brittle: proposes an updated test (for example, changing `findById("submit-btn-42")` to `findByRole("button", { name: /submit/i })`).
5. Opens a PR with the updated test for human approval.

Tools in this space: **Applitools** (visual regression healing), **Mabl**, **Testim**, and emerging LLM-based approaches in frameworks like **Playwright** and **Cypress**.

#### Test prioritization

Not all tests need to run on every commit. Running a 45-minute test suite on a one-line typo fix is wasteful. **Test prioritization** (also called *test selection* or *test impact analysis*) uses ML to answer: "Given this specific code change, which tests are most likely to be relevant?"

Approaches:
- **Code-coverage-based selection:** only run tests whose coverage overlaps the changed lines (tools: `pytest --co`, `jest --changedSince`, `Bazel` with incremental builds).
- **Failure-prediction models:** train a model on historical `(changed_files, failed_tests)` pairs. Given new changed files, predict which tests are likely to fail. Microsoft Research showed this can reduce test execution time by 40–70% on large codebases.
- **LLM semantic similarity:** embed changed function names and test names; only run tests whose embedding is semantically close to the change.

#### A concrete pipeline with test generation and prioritization

```yaml
# GitHub Actions example — illustrative
name: AI-Augmented Test Pipeline
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Identify changed files
        id: changes
        run: |
          git diff --name-only origin/main...HEAD > changed_files.txt
          cat changed_files.txt

      - name: AI test prioritization
        run: |
          python scripts/select_tests.py \
            --changed changed_files.txt \
            --model gpt-4o \
            --output selected_tests.txt

      - name: Run selected tests only
        run: pytest $(cat selected_tests.txt)

      - name: Generate missing tests (on PR)
        if: github.event_name == 'pull_request'
        run: |
          python scripts/generate_tests.py \
            --changed changed_files.txt \
            --output tests/generated/
```

---

### 5.3 Reducing Flaky Tests: Agents That Diagnose and Fix Failures

#### What is a flaky test?

A **flaky test** is a test that sometimes passes and sometimes fails on the same code, without any change to the source. This is one of the most corrosive problems in a CI/CD pipeline:

- Engineers learn to ignore "transient" failures — and eventually ignore *real* failures too.
- CI must re-run failed jobs, wasting compute and time.
- Trust in the pipeline erodes: "oh, it probably just flaked" becomes the default response to red builds.

Google has publicly stated that flaky tests cost thousands of engineering hours per year and are one of the top reasons developers lose confidence in automated testing.

#### Common causes of flakiness

| Cause | Example |
|---|---|
| **Time dependencies** | `assert result == "2025-01-01"` — fails at midnight on Dec 31 |
| **Order dependencies** | Test B assumes Test A ran first and set up shared state |
| **External service calls** | Test calls a real API that is occasionally slow or unavailable |
| **Concurrency / race conditions** | Two threads write to the same file simultaneously |
| **Resource exhaustion** | Test assumes there is always enough memory/disk |
| **Non-deterministic data** | UUID generation or random shuffling not seeded consistently |

#### What an agent does about it

1. **Detection:** Monitor CI history. Flag any test that has flipped between pass and fail on the same commit SHA more than twice in the last 30 runs. This is a data pipeline task, not an LLM task — but the result feeds the agent.

2. **Root-cause analysis:** For flagged tests, the agent reads: the test code, the failure logs from each flake, and the test's history. It uses the LLM to reason about which of the common cause categories best matches the evidence.

3. **Proposed fix:** The agent suggests a concrete change — for example, replacing a fixed timestamp with `datetime.now()`, adding `@pytest.mark.timeout(10)`, or inserting a `mock.patch` for the external API call. It opens a PR with the change.

4. **Verification:** The pipeline re-runs the previously flaky test 10 times to verify flakiness is gone before merging.

⚠️ **Pitfall:** Agents tend to *hide* flakiness by wrapping tests in retry loops rather than fixing the underlying cause. A retry-wrapped flaky test is still a flaky test — it is just harder to notice. Require the agent's fix to explain the root cause, not just suppress the symptom.

#### ✅ Check your understanding

**Q:** An agent "fixes" a flaky test by wrapping it in `@retry(3)` and the build goes green. Why is this worse than leaving it red?

<details><summary>💡 Show answer</summary>

It **hides** the flakiness instead of fixing it — the underlying race condition, time dependency, or external-call fragility is still there, now masked. Worse, a retry that occasionally passes can also paper over a *real* intermittent bug. The fix should name the root cause (e.g. replace a hardcoded timestamp, mock the external API) and then prove it by re-running the test many times — not suppress the symptom.

</details>

---

### 5.4 Measuring Coverage and Quality with AI; Eval Harnesses for AI-Generated Code

#### Coverage is necessary but not sufficient

**Code coverage** measures what percentage of lines, branches, or conditions are exercised by tests. It is a useful proxy for quality but not a definition of it. 80% line coverage can coexist with zero tests for the most dangerous code paths.

AI agents improve coverage measurement in two ways:

1. **Gap identification:** After running the coverage report, the agent reads the uncovered lines and classifies them — are they error-handling paths? Edge cases? Dead code? It prioritizes which uncovered paths are worth testing and generates tests for the highest-risk ones.

2. **Semantic coverage:** Beyond line coverage, the agent checks whether tests *assert meaningful things* or just exercise lines without verifying outcomes. A test that calls a function and doesn't assert anything is "covered" but useless. The agent flags these.

#### Eval harnesses for AI-generated code — a critical concept

Here is the bootstrapping problem: an AI agent generates code; you need to test that code; but who tests the tests? And if the agent also generates the tests, how do you know the tests are correct?

This is why **eval harnesses** (short for *evaluation harnesses*) have become an essential part of agentic DevOps:

An **eval harness** is a separate test framework — with independently written reference cases, fuzzing, formal contracts, or golden-output comparisons — whose sole job is to verify AI-generated artifacts. It is *not* written by the same agent that produced the code being evaluated.

![A top-to-bottom flow showing why an agent can't grade its own homework. A developer commits a code change, which triggers Agent A (the test-generation agent) that reads the changed functions and writes tests/generated/test_payment.py. Those generated tests feed into an independently-maintained Eval Harness that runs contract tests (OpenAPI assertions), property-based fuzzing (Hypothesis), and golden-output regression tests, and detects trivially-true / always-pass tests. The eval score then feeds a human approval gate, required if the score is below threshold. The harness is not written by the agent it checks.](eval-harness.svg)

The key insight: **an AI agent cannot grade its own homework.** Eval harnesses provide an independent signal.

#### ✅ Check your understanding

**Q:** If the same agent writes both the code *and* the tests, why isn't "all tests pass" enough to trust the change? What makes an eval harness different?

<details><summary>💡 Show answer</summary>

An agent can write tests that pass *by construction* — trivially-true assertions, or tests that only exercise the happy path it already coded for. "Tests pass" then just means "the agent agrees with itself." An **eval harness is maintained independently** of the code-generating agent (separate reference cases, fuzzing, golden outputs), so it provides an *external* signal the agent can't game — and it specifically hunts for always-pass tests.

</details>

---

### 5.5 Tools and Frameworks for AI-Enhanced QA

| Tool / Framework | Primary Use |
|---|---|
| **GitHub Copilot (code review / chat)** | Inline test suggestions and PR review comments |
| **CodiumAI / Qodo** | Automated test generation from code, specialised for testing |
| **SonarQube + AI extensions** | Code quality, security scanning, ML-ranked findings |
| **Semgrep** | Lightweight static analysis; rules shareable across teams |
| **Diffblue Cover** | Java-focused automated unit test generation |
| **Mabl / Testim / Applitools** | Self-healing UI and end-to-end test platforms |
| **Hypothesis** | Property-based testing (Python) — pairs well with AI-identified edge cases |
| **Pynguin** | Research-grade automated test generation for Python |
| **pytest-randomly + pytest-repeat** | Detect order-dependent / flaky tests |
| **jest --changedSince / Bazel** | Test impact analysis / selective test execution |

---

### 💬 Discussion & Case Questions — Session 5

1. **Trust and verification.** A teammate says: "The agent generates the tests so we don't have to write them — that saves 30% of our time." What is the danger in this framing? What assurance would you require before trusting AI-generated tests?

2. **False sense of coverage.** Your pipeline shows 85% code coverage after adding an AI test-generation step. A security incident later reveals the uncovered 15% contained the vulnerability. What process would you add to prevent this?

3. **Self-healing tests and intent.** When an agent "heals" a failing test, it might update the test to match *changed* (but wrong) behavior. How do you distinguish "the test is brittle and needs updating" from "the test caught a real regression that needs a code fix"?

4. **Organizational adoption.** You are proposing to a CTO that the team adopt AI-generated tests. What metrics would you track to demonstrate the program is working? What would signal it is making things worse?

---

### 🔑 Key Terms — Session 5

| Term | Definition |
|---|---|
| **Static analysis** | Inspecting source code without executing it to find bugs, security issues, or style violations |
| **AI code review agent** | An agent that reads pull-request diffs and posts structured review comments |
| **Test generation** | Automatically producing test cases — from code, from specs, or from mutation testing |
| **Self-healing test** | A test that an agent automatically updates when it fails due to incidental environmental change rather than a real regression |
| **Flaky test** | A test that produces inconsistent pass/fail results without code changes |
| **Test prioritization** | Selecting a subset of tests most likely to be relevant to a given change, to reduce execution time |
| **Code coverage** | A metric measuring the percentage of code paths exercised by the test suite |
| **Eval harness** | An independently-maintained evaluation framework that verifies the correctness of AI-generated code or tests |
| **Mutation testing** | Introducing deliberate small bugs to check whether tests detect them |
| **TDD (Test-Driven Development)** | Writing tests before writing the implementation |

### ⚠️ Common Pitfalls — Session 5

- **Trusting AI-generated tests without reading them.** An agent can produce tests that always pass (trivially true assertions) or that test only the happy path. Read the generated tests.
- **Mistaking coverage for quality.** 100% line coverage with weak assertions is worse than 60% coverage with rigorous assertions, because it creates false confidence.
- **Retry loops that mask flakiness.** Wrapping tests in `@retry(3)` hides the problem. Require root-cause fixes.
- **Eval harness drift.** If the eval harness is not maintained as the codebase evolves, its golden outputs become stale and it stops catching regressions.
- **Agent scope creep.** An agent asked to "fix failing tests" may begin modifying production code to make tests pass. Scope the agent's write permissions to the test directory only.

---

## Session 6: Self-Optimizing & Self-Healing Pipelines

**Session budget: ≈ 1.5 hours**

### Learning Objectives

By the end of Session 6, students will be able to:

1. Describe how an AI agent triages a failing build, proposes a fix, and opens a PR.
2. Explain two ML techniques that reduce CI pipeline execution time.
3. Define *predictive build-failure detection* and sketch how a model is trained for it.
4. Describe how AI improves cache hit rates and artifact reuse.
5. **Explain the guardrails required for autonomous merges — approval gates and blast-radius limits — and articulate why these are non-negotiable.**

### Timed Agenda

| Time | Activity |
|---|---|
| 0:00–0:10 | Recap of Session 5; introduce self-optimizing pipelines |
| 0:10–0:30 | Concept: Agents that triage and fix failing builds |
| 0:30–0:50 | Concept: ML for pipeline speed — selective execution, resource allocation |
| 0:50–1:05 | Concept: Predictive failure detection; caching with AI insights |
| 1:05–1:25 | CRITICAL: Guardrails — approval gates and blast-radius limits |
| 1:25–1:30 | Discussion questions and session wrap |

---

### 6.1 Agents That Triage and Fix Failing Builds and Open Pull Requests

#### The "fire alarm" problem

A CI pipeline fails. A red notification appears in Slack. The on-call engineer opens the dashboard, sees 47 failing steps in 3 pipelines, and has to manually sift through thousands of lines of logs to find the root cause. This is the "fire alarm" problem: the alarm goes off, but you still have to find the fire yourself.

A **build triage agent** automates this investigation:

1. **Receive the failure signal:** The pipeline posts a webhook event to the agent (or the agent polls the CI API).
2. **Collect evidence:** The agent fetches the full build log, the git diff since the last green build, recent changes to the `Dockerfile` or dependency files, and any similar past failures from the CI history database.
3. **Reason about the cause:** The agent groups the log errors into categories (compile error, test failure, network timeout, missing dependency, configuration error) and identifies the most likely root cause.
4. **Propose a fix:** The agent constructs a minimal code or configuration change that addresses the identified cause.
5. **Open a PR:** Using the GitHub/GitLab API (or an MCP tool), the agent creates a branch, commits the fix, and opens a PR with a structured description: *"This build failed because X. I changed Y. Please review before merging."*
6. **Wait for human approval.** It does not merge. It cannot merge. This is the guardrail.

![A six-step build-triage agent flow. 1 Failure (red build signal) → 2 Collect (logs, diff, history) → 3 Reason (find root cause) → 4 Propose (minimal fix) → 5 Open PR (with a PR-scope token) → 6 Wait (human approves). A callout notes the token has pull_request:write only — it cannot push to main, delete branches, or deploy. Steps 1–4 turn "47 failing steps, find it yourself" into a reasoned diagnosis in minutes.](build-triage.svg)

#### Worked example: a build-fixer agent in pseudocode

```python
# Illustrative — not production code
import anthropic
import github

def handle_build_failure(build_id: str, repo: str):
    client = anthropic.Anthropic()

    # 1. Collect context
    log = ci_api.get_build_log(build_id)[-5000:]   # last 5k chars
    diff = git_api.get_diff_since_last_green(repo)
    history = ci_db.get_similar_failures(log[:500], limit=5)

    # 2. Ask the agent to reason and propose a fix
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        system="""You are a CI triage agent. Analyze the failing build,
        identify the root cause, and propose the minimal fix.
        Output JSON: { "root_cause": "...", "fix_description": "...",
                       "files_to_change": [{"path": "...", "new_content": "..."}] }
        Never propose changes that touch production config or deployment files.""",
        messages=[{
            "role": "user",
            "content": f"Build log:\n{log}\n\nDiff:\n{diff}\n\nSimilar past failures:\n{history}"
        }]
    )

    fix = parse_json(message.content[0].text)

    # 3. Create branch and PR (requires PR scope token — not merge scope)
    gh = github.Github(os.environ["GH_PR_TOKEN"])  # least-privilege token
    repo_obj = gh.get_repo(repo)
    branch = f"bot/fix-build-{build_id}"
    create_branch_and_commit(repo_obj, branch, fix["files_to_change"])

    pr = repo_obj.create_pull(
        title=f"[Bot] Fix build {build_id}: {fix['root_cause'][:60]}",
        body=f"**Root cause:** {fix['root_cause']}\n\n"
             f"**Proposed fix:** {fix['fix_description']}\n\n"
             f"*This PR was opened by the build-fixer agent. A human must review and approve before merging.*",
        head=branch,
        base="main"
    )
    notify_slack(f"Build fixer opened PR #{pr.number}: {pr.html_url}")
```

Notice what the agent's token *cannot do*: it holds a token with `pull_request:write` scope only — it cannot push to `main` directly, cannot delete branches, and cannot trigger deployments. Least privilege is enforced at the token level, not just at the "I promise not to" level.

---

### 6.2 Using ML to Reduce Pipeline Execution Time; Dynamic Build-Resource Allocation

#### Why pipeline speed matters

A CI pipeline that takes 45 minutes is a pipeline that engineers learn to ignore. They push a commit, go do other work, come back — and by then, the context is cold and fixing the problem is slower. DORA research (see [dora.dev](https://dora.dev)) consistently shows that high-performing engineering teams have mean change lead times under one hour, and that fast feedback loops are a primary predictor of software delivery performance.

ML helps in two main ways:

**A. Selective test and build execution (covered in Session 5)**

As discussed, test-impact analysis skips tests that are provably irrelevant to a change. The same principle applies to build steps: if no file in the `frontend/` directory changed, skip the frontend build entirely. ML models can make this decision more accurately than simple path-glob rules by learning historical patterns of "which changes actually affected which outputs."

**B. Dynamic build-resource allocation**

Not every build needs the same resources. A change to a README file versus a change to the core payment service requires very different amounts of CPU and memory to build and test. Allocating a 32-vCPU build machine for a documentation change is wasteful; allocating a 2-vCPU machine for a full integration test run is slow.

An ML model trained on historical build metadata (`(changed_files, resource_used, build_time)`) can predict, at the moment a pipeline is triggered, how much CPU and memory this particular run will need. The CI system then provisions that exact size of runner — no more, no less.

![Two stacked ML models size a build to the change. A new commit that only touches docs/ flows into a resource-predictor model (predicted build time 2 min, CPU need 1 vCPU, provision a t3.micro runner instead of a 32-vCPU box), then into a selective-execution model that skips the frontend and backend test suites and runs only the markdown lint.](pipeline-speed.svg)

**GitHub Actions** supports this natively with self-hosted runners; **Jenkins** supports it via the Kubernetes plugin (which can provision appropriately sized pods per job). Cloud CI services (CircleCI, Buildkite) are increasingly adding ML-driven resource recommendations.

---

### 6.3 Predictive Build-Failure Detection

#### Reacting versus predicting

The build-triage agent in Section 6.1 is *reactive* — it responds after a failure occurs. **Predictive build-failure detection** is proactive: it estimates, at the moment a developer opens a PR or pushes a commit, the probability that this change will cause the build to fail.

If the model predicts a high failure probability, the pipeline can:
- Automatically run a broader test suite before the developer even asks.
- Post a warning comment on the PR: "High build-failure risk — consider running locally first."
- Route the PR to a senior reviewer who can sanity-check before CI resources are consumed.

#### Building the model (conceptually)

The features fed to the model typically include:

| Feature | Description |
|---|---|
| Number of changed files | More files → higher coupling, more likely to break something |
| Files changed (encoded) | The identity of files matters — changing `auth.py` is riskier than `README.md` |
| Time since last change to those files | Files not touched in 2 years tend to have brittle test coverage |
| Author's historical failure rate | Not to penalize — to offer targeted guidance to newer contributors |
| Past failures on nearby lines | Code regions with high historical bug density |
| Test coverage of changed lines | Low-coverage lines are harder to safely change |
| Day and time | Friday afternoon deploys are a meme for a reason |

The output is a probability score. A threshold (e.g., 0.7) triggers the warning. Microsoft, Google, and Meta have each published research on variations of this approach.

---

### 6.4 Caching and Artifact Management with AI Insights

Build caches store the outputs of expensive steps (compiling, dependency resolution, container-layer building) so that subsequent runs can reuse them. Cache strategy is surprisingly nuanced: cache too aggressively and you get stale artifacts; cache too conservatively and you recompile from scratch every time.

AI agents can improve cache utilization in three ways:

1. **Cache key optimization:** Instead of using a simple file hash as the cache key, the agent analyzes which files *actually affect* the output of each stage and generates a minimal, precise cache key — avoiding unnecessary cache misses.

2. **Artifact lifecycle management:** The agent monitors artifact storage usage and identifies artifacts that have never been downloaded (and can be deleted) versus artifacts that are frequently reused (and should be stored closer to runners).

3. **Dependency change alerts:** When a new commit changes `requirements.txt` or `package.json`, the agent notes that the dependency cache will be invalidated and pre-warms it (kicks off a cache rebuild) during off-peak hours before the developers arrive in the morning.

---

### 6.5 Continuous Feedback Loops and Guardrails on Autonomous Merges

#### This is the most important section of the week.

Everything discussed so far — automated test generation, build triage agents, PR-opening bots — is useful only if it is safe. The moment an agent gains the ability to merge its own changes into `main`, you have crossed from *agentic assistance* to *autonomous delivery*, and the blast radius of a mistake changes from "a PR sits in the queue" to "production is broken."

**This course has one recurring safety message: autonomy must grow incrementally, and every new level of autonomy requires a corresponding guardrail.**

#### Approval gates: the human checkpoint

An **approval gate** (also called a *human-in-the-loop gate* or *manual approval step*) is a required human action that the pipeline cannot bypass. In Jenkins:

```groovy
stage('Human Approval Required') {
  steps {
    input message: 'Agent has proposed a fix. Review PR #${PR_NUMBER} and approve to proceed.',
          submitter: 'team-leads',     // only these users can approve
          timeout: 60                  // minutes; times out to ABORT, not to auto-approve
  }
}
```

In GitHub Actions:

```yaml
jobs:
  agent-fix:
    runs-on: ubuntu-latest
    steps:
      - name: Agent proposes fix and opens PR
        run: python scripts/build_fixer.py

  human-review:
    needs: agent-fix
    runs-on: ubuntu-latest
    environment: production           # environments have required reviewers
    steps:
      - name: Merge approved fix
        run: gh pr merge ${{ env.PR_NUMBER }} --squash
```

The `environment: production` setting triggers GitHub's **required reviewers** feature — one or more designated humans must click "Approve" in the GitHub UI before the `human-review` job is allowed to run. The agent cannot approve its own environment deployment.

⚠️ **Critical pitfall:** Do not set approval gates to auto-approve after a timeout. This is a common mistake: "if nobody reviews in 30 minutes, auto-merge." This behavior defeats the purpose of the gate. If nobody reviewed, the correct behavior is to leave the PR open and notify more loudly — not to proceed autonomously.

#### Blast-radius limits: restricting what the agent can change

Even with approval gates, you want to limit *how much damage* the agent can cause if a human approves something they should not have. **Blast-radius limits** are constraints on the scope of agent-authored changes:

| Limit type | Example |
|---|---|
| **File scope** | Agent may only modify files in `src/` and `tests/`. Cannot touch `infra/`, `secrets/`, or `Dockerfile`. |
| **Size limit** | Agent's PR may not change more than 50 lines total. Larger changes require human authorship. |
| **Deployment scope** | Agent-authored changes may deploy to `staging` automatically but require an additional approval for `production`. |
| **Rate limit** | Agent may open at most 3 PRs per hour. Prevents a runaway loop. |
| **Rollback-only mode** | In high-risk periods (release freeze, holiday), the agent may only *roll back* — never *roll forward*. |

These limits are implemented at multiple layers: the agent's system prompt ("you are prohibited from modifying infrastructure files"), the CI pipeline configuration (branch protection rules, CODEOWNERS), and token permissions (the agent's GitHub token has no `admin` scope).

#### The layered guardrail model

Think of guardrails as concentric fences, not a single gate:

![Four concentric fences around an agent action. From outside in: ① token permissions (agent cannot push to main); ② CODEOWNERS plus branch-protection rules; ③ agent system-prompt scope restriction; ④ a human approval gate. At the very center sits the agent action (e.g. merge a proposed fix), which a human reviews before it runs. Outer fences catch mistakes even if an inner one fails — no single layer is trusted alone.](guardrail-layers.svg)

The outer fences catch mistakes even if the inner ones fail. No single layer is trusted alone.

#### ✅ Check your understanding

**Q:** A team relies *only* on the agent's system prompt ("never modify infra files") to keep it safe. Why is that fragile, and what layers would you add?

<details><summary>💡 Show answer</summary>

A system prompt is a single, *soft* layer — it can be confused, ignored, or overridden by **prompt injection**, and it isn't enforced by anything outside the LLM. Add hard, external layers: a **scoped token** with no write access to infra/main, **branch-protection + CODEOWNERS**, and a **human approval gate** before merge. Then a failure of any one fence is caught by the others.

</details>

#### Continuous feedback loops

A self-optimizing pipeline is not just about fixing individual failures — it learns over time:

- **Failure-pattern database:** Every triage decision (human accepted or rejected the agent's proposed fix) is stored. The agent is fine-tuned or prompted with these examples to improve future triage accuracy.
- **Coverage trend tracking:** If AI-generated tests are reducing real defect escape rates, that is a signal to trust the generator more. If they are not, the generator needs to be tuned.
- **DORA metrics dashboard:** Track the four key DORA metrics — Deployment Frequency, Lead Time for Changes, Change Failure Rate, Mean Time to Restore — and annotate each metric with when the agentic pipeline change was introduced. This makes the ROI of the agentic improvements visible.

---

### 💬 Discussion & Case Questions — Session 6

1. **The auto-approve temptation.** Your team's build-fixer agent is so reliable that it fixes 90% of failures correctly on the first try. A manager suggests: "Given its track record, let's just auto-approve agent PRs for the test directory — it will save time." How do you respond? What could go wrong?

2. **Blast-radius calibration.** If you set the blast-radius limit to "agent may only change files under 10 lines," many legitimate fixes would be blocked. If you set it to "no limit," a runaway agent could rewrite the whole codebase. How would you empirically determine the right limit for your team?

3. **Feedback loop quality.** If the human approver always clicks "Approve" without reading the agent's PR, the feedback loop data (accepted/rejected) becomes meaningless. What process changes would you make to ensure approvals are genuine?

4. **Predictive failure detection fairness.** The model uses "author's historical failure rate" as a feature. Why might this be problematic from an equity standpoint? How would you mitigate this?

---

### 🔑 Key Terms — Session 6

| Term | Definition |
|---|---|
| **Build triage agent** | An AI agent that collects CI failure evidence, identifies root causes, and proposes fixes |
| **Approval gate** | A required human action in a pipeline — the pipeline pauses until a designated human approves |
| **Blast-radius limit** | A constraint on the scope of changes an agent is permitted to make, limiting damage if something goes wrong |
| **Predictive build-failure detection** | ML-based prediction of build failure probability at the time a change is submitted |
| **Test-impact analysis** | Selecting only the tests relevant to a specific code change, reducing CI execution time |
| **Dynamic resource allocation** | Provisioning CI runner resources proportional to the predicted needs of each specific build |
| **Cache key optimization** | Computing minimal, precise cache keys to maximize reuse without introducing staleness |
| **DORA metrics** | The four key DevOps metrics: Deployment Frequency, Lead Time for Changes, Change Failure Rate, Mean Time to Restore |
| **Least privilege** | The principle that an agent (or user) should have only the minimum permissions needed for their task |
| **Human-in-the-loop** | An autonomy model where a human must actively approve each significant agent action before it executes |

### ⚠️ Common Pitfalls — Session 6

- **Auto-approve on timeout.** Never configure an approval gate to approve automatically if no one responds. This defeats the purpose.
- **Single-layer guardrails.** Relying on only the agent's own system prompt to prevent dangerous actions. System prompts can be confused or bypassed (prompt injection). Always add token-level and platform-level enforcement.
- **Feedback loop corruption.** Rubber-stamp approvals poison the feedback loop. Institute a lightweight but mandatory review checklist.
- **Runaway PR loops.** An agent whose fix opens a PR that triggers another CI failure which triggers another fix which opens another PR. Rate-limit agent PR creation and add loop-detection logic.
- **Ignoring DORA regressions.** Agents are supposed to improve the metrics. If Deployment Frequency drops or Change Failure Rate rises after introducing the agent, investigate immediately.
- **Scope creep through clever prompting.** An agent instructed to "fix the build" may interpret that as license to refactor the entire module. Use explicit, narrow system-prompt instructions and file-scope restrictions.

---

## Recap & Looking Ahead

### What we covered this week

Week 3 moved agents from the workbench into the assembly line. The key ideas:

- **Code review agents** provide contextual feedback that rule-based linters cannot — but humans must still make the final call.
- **AI test generation** reduces the cost of writing tests, but eval harnesses and independent verification are required to trust generated tests.
- **Flaky test detection and healing** saves hours of engineering time per week at scale — but agents must fix root causes, not paper over them with retries.
- **Build triage agents** automate the tedious "find the fire" step — but their PR-creation privilege must be strictly scoped and their merge capability must be zero.
- **Predictive failure detection** shifts the pipeline from reactive to proactive.
- **Guardrails** — approval gates and blast-radius limits — are not optional features to add later. They are the difference between a useful agent and a liability. Every level of increased agent autonomy requires a corresponding level of increased guardrail.

### The feedback loop closes

The pipeline is now a learning system: every failure, every fix, every human approval or rejection feeds data back into models that improve future decisions. This is the foundation for Week 4.

### Looking ahead: Week 4 — Predictive Analytics & Capacity Intelligence

[Week 4](../week-04/week-04-notes.md) takes the data generated by agentic pipelines and applies it to harder forecasting problems: predicting *deployment failures* before they happen, forecasting *infrastructure capacity needs* hours or days in advance, and using ML to drive autoscaling and cost optimization (FinOps). The agents we built this week produce the telemetry and build history that Week 4's models will train on.

Questions to think about before Week 4:
- What historical data does your CI pipeline produce that could be used to train a deployment-risk model?
- If your pipeline runs 50 builds per day, what is the minimum number of historical builds you would need before a failure-prediction model has enough data to be useful?
- How would you handle the cold-start problem for a new project with no history?

---

## References

### Course Materials

- [CSE636 Syllabus v2](../../syllabus/CSE636_Syllabus_v2.md) — Week 3 specification
- [Jenkins slide deck](../../slides/Jenkins.md) — Pipeline concepts, declarative vs. scripted syntax, core Jenkins concepts
- [Jenkins project (runnable lab)](../../project/Jenkins/) — Docker-based Jenkins setup for hands-on experimentation
- [Week 2: AI Agent Tooling, Protocols & Platforms](../week-02/week-02-notes.md) — MCP, agent frameworks, permission management (prerequisite)
- [Week 4: Predictive Analytics & Capacity Intelligence](../week-04/week-04-notes.md) — What this week's data feeds into

### External References

- **DORA — Accelerate State of DevOps / DevOps metrics:** https://dora.dev
- **GitHub Copilot documentation (code review and agent features):** https://docs.github.com/en/copilot
- **GitHub Actions documentation:** https://docs.github.com/en/actions
- **Anthropic — Building Effective Agents:** https://www.anthropic.com/engineering/building-effective-agents
- **Anthropic Claude API documentation:** https://docs.anthropic.com
- **CodiumAI / Qodo (AI test generation):** https://www.qodo.ai
- **Semgrep (static analysis):** https://semgrep.dev
- **SonarQube:** https://www.sonarqube.org
- **Hypothesis (property-based testing for Python):** https://hypothesis.readthedocs.io
- **Mabl (self-healing test automation):** https://www.mabl.com
- **Applitools (visual AI testing):** https://applitools.com
- **Microsoft Research — Test case prioritization / predictive failure detection:** https://www.microsoft.com/en-us/research/
- **Open Policy Agent (policy-as-code for guardrails):** https://www.openpolicyagent.org
