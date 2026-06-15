# Week 3 — Lab & Assignment

> 🧪 **Hands-on work for Week 3.** For the lecture notes, foundations primer, discussion questions, and references, see **[week-03-notes.md](week-03-notes.md)**.

---

## 🧪 Lab: Build-Fixer Agent with Human Approval Gate

**Duration:** In-class or take-home (1–2 hours)
**Goal:** Implement a minimal pipeline where an AI agent detects a failing CI build, proposes a fix, and opens a PR that requires human approval before merging.

> 🎯 **At a glance**
>
> | | |
> |---|---|
> | **You'll need** | GitHub repo, Python 3.10+, `anthropic` + `PyGithub`, an Anthropic API key, a scoped GitHub token |
> | **You'll build** | A CI pipeline + `build_fixer_agent.py` that turns a red build into a reviewed PR |
> | **Submit** | Screenshots of the failure, the agent's PR, and the approval-gate pause + a short reflection |
> | **Ties to notes** | [Build-triage agent](week-03-notes.md#61-agents-that-triage-and-fix-failing-builds-and-open-pull-requests) and [guardrails](week-03-notes.md#65-continuous-feedback-loops-and-guardrails-on-autonomous-merges) |

### What you will build

![The lab flow, top to bottom: push code with an intentional bug → CI pipeline runs and the test stage FAILS (continue-on-error lets the agent run next) → the build-fixer agent activates (reads the build log, identifies the failing test and cause, proposes a minimal fix, and opens a PR with write-only, no-merge permission) → a human approval gate pauses the pipeline (a teammate reviews the PR then clicks Approve; it times out to abort, never auto-approves) → optional auto-merge to a feature branch, never to main → a green pipeline confirms the fix.](build-fixer-flow.svg)

### Prerequisites

- A GitHub account and a repository (can fork the course's Jenkins project or any small Python project).
- Python 3.10+ and `pip install anthropic PyGithub`.
- An Anthropic API key (stored as `ANTHROPIC_API_KEY` in GitHub Secrets / Jenkins credentials).
- A GitHub personal access token with `repo` scope (stored as `GH_TOKEN`).

---

### Step 1: Create the intentionally failing application

Create a file `src/calculator.py`:

```python
def add(a, b):
    # Bug: subtraction instead of addition
    return a - b

def multiply(a, b):
    return a * b
```

And a test file `tests/test_calculator.py`:

```python
from src.calculator import add, multiply

def test_add():
    assert add(2, 3) == 5        # This will FAIL (returns -1)

def test_multiply():
    assert multiply(3, 4) == 12  # This will PASS
```

Verify locally:

```bash
pip install pytest
pytest tests/                    # Expected: 1 failed, 1 passed
```

---

### Step 2: Create the CI pipeline

**Option A — GitHub Actions** (`.github/workflows/ci.yml`):

```yaml
name: CI with Build-Fixer Agent
on:
  push:
    branches: ["*"]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    outputs:
      build_failed: ${{ steps.test_step.outcome == 'failure' && 'true' || 'false' }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install pytest
      - id: test_step
        name: Run tests
        run: pytest tests/ --tb=short 2>&1 | tee build_log.txt
        continue-on-error: true           # let the pipeline continue so the agent can run
      - uses: actions/upload-artifact@v4
        with:
          name: build-log
          path: build_log.txt

  agent-fix:
    needs: test
    if: needs.test.outputs.build_failed == 'true'
    runs-on: ubuntu-latest
    environment: agent-proposed           # requires human review
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with: { name: build-log }
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install anthropic PyGithub
      - name: Run build-fixer agent
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GH_TOKEN: ${{ secrets.GH_TOKEN }}
          REPO: ${{ github.repository }}
          BASE_BRANCH: ${{ github.ref_name }}
        run: python scripts/build_fixer_agent.py
```

**Option B — Jenkinsfile** (add to the course's Jenkins Docker setup):

```groovy
pipeline {
  agent any

  environment {
    ANTHROPIC_API_KEY = credentials('anthropic-api-key')
    GH_TOKEN          = credentials('github-token')
  }

  stages {
    stage('Test') {
      steps {
        sh 'pip install pytest'
        script {
          def result = sh(script: 'pytest tests/ --tb=short 2>&1 | tee build_log.txt', returnStatus: true)
          env.TESTS_FAILED = (result != 0) ? 'true' : 'false'
        }
      }
    }

    stage('Agent: Propose Fix') {
      when { expression { env.TESTS_FAILED == 'true' } }
      steps {
        sh 'pip install anthropic PyGithub'
        sh 'python scripts/build_fixer_agent.py'
      }
    }

    stage('Human Approval Gate') {
      when { expression { env.TESTS_FAILED == 'true' } }
      steps {
        input(
          message: "Build-fixer agent has opened a PR. Review it, then approve here to confirm the process completed.",
          submitter: 'team-leads',
          timeout: 60     // minutes — ABORT on timeout, never auto-approve
        )
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'build_log.txt', allowEmptyArchive: true
    }
  }
}
```

---

### Step 3: Write the build-fixer agent script

Create `scripts/build_fixer_agent.py`:

```python
"""
Build-fixer agent.
Reads the build log, asks Claude to identify the failing test and propose a fix,
then opens a GitHub PR with the proposed change.
"""
import os
import json
import anthropic
from github import Github

def run():
    # --- 1. Read context ---
    with open("build_log.txt") as f:
        build_log = f.read()

    with open("src/calculator.py") as f:
        source_code = f.read()

    # --- 2. Call the agent ---
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system="""You are a build-fixer agent. Your only job is to identify
the root cause of a failing Python test and propose the minimal fix to the
source file. Output ONLY valid JSON in this format:
{
  "root_cause": "one sentence explanation",
  "fix_description": "what you changed and why",
  "fixed_file_path": "src/calculator.py",
  "fixed_file_content": "... complete corrected file content ..."
}
Do not add tests. Do not change any file except the one identified.
Do not make stylistic changes unrelated to the bug.""",
        messages=[{
            "role": "user",
            "content": (
                f"Build log:\n```\n{build_log}\n```\n\n"
                f"Source file (src/calculator.py):\n```python\n{source_code}\n```"
            )
        }]
    )

    fix = json.loads(response.content[0].text)
    print(f"Agent identified root cause: {fix['root_cause']}")

    # --- 3. Open a PR ---
    gh = Github(os.environ["GH_TOKEN"])
    repo = gh.get_repo(os.environ["REPO"])
    base = os.environ.get("BASE_BRANCH", "main")
    branch_name = f"bot/fix-build-{os.environ.get('GITHUB_RUN_ID', 'local')}"

    # Create branch
    ref = repo.get_git_ref(f"heads/{base}")
    repo.create_git_ref(f"refs/heads/{branch_name}", ref.object.sha)

    # Update the file
    contents = repo.get_contents(fix["fixed_file_path"], ref=base)
    repo.update_file(
        fix["fixed_file_path"],
        f"[bot] fix: {fix['root_cause'][:72]}",
        fix["fixed_file_content"],
        contents.sha,
        branch=branch_name
    )

    # Open the PR
    pr = repo.create_pull(
        title=f"[Bot Fix] {fix['root_cause'][:60]}",
        body=(
            f"## Agent-Proposed Fix\n\n"
            f"**Root cause:** {fix['root_cause']}\n\n"
            f"**Change:** {fix['fix_description']}\n\n"
            f"---\n"
            f"*This PR was opened by the build-fixer agent. "
            f"A human must review and approve before merging.*\n\n"
            f"**Checklist before approving:**\n"
            f"- [ ] The proposed fix matches the described root cause\n"
            f"- [ ] No unrelated changes are included\n"
            f"- [ ] The fix does not touch infrastructure or deployment files\n"
        ),
        head=branch_name,
        base=base
    )
    print(f"Opened PR #{pr.number}: {pr.html_url}")
    return pr.number

if __name__ == "__main__":
    run()
```

---

### Step 4: Set up the approval gate

In GitHub, configure the `agent-proposed` environment (Settings → Environments → New environment):

1. Name it `agent-proposed`.
2. Enable **Required reviewers** and add yourself and one teammate.
3. Enable **Prevent self-review** if available.

Now when the workflow reaches the `agent-fix` job (which runs in the `agent-proposed` environment), GitHub will pause and send a notification to the designated reviewers. The job cannot proceed until a reviewer clicks "Approve and deploy."

<details><summary>✅ Check your understanding — is your gate actually a gate?</summary>

Your guardrail is real only if **the agent genuinely cannot merge on its own**. Verify:

- The agent's token is scoped to open PRs, **not** to push to `main` or merge (try it — a merge call should be denied).
- The `agent-proposed` environment has **Required reviewers** set, so the job *pauses* rather than proceeding.
- There is **no auto-approve-on-timeout** anywhere; a timeout should abort, not merge.

If you removed the human and nothing dangerous could still happen, the gate is doing its job.

</details>

---

### Step 5: Trigger the full flow

1. Push the code with the bug to a new branch.
2. Watch the `test` job fail.
3. Watch the `agent-fix` job kick off, pause at the environment approval.
4. Open the PR the agent created. Read it. Verify the fix is correct.
5. Approve the environment in GitHub (or click "Proceed" in Jenkins).
6. Observe the pipeline confirm the fix worked.

### Lab Deliverable

A short write-up (1–2 pages or equivalent notes) covering:
- Screenshot or log showing the test failure, the agent's PR, and the approval gate pause.
- The agent's `root_cause` and `fix_description` output — was it accurate?
- One thing you would change about the agent's prompt or the guardrail setup, and why.

---

## Assignment: Agent-Optimized CI Pipeline

**Due:** Before Week 4 session

### Task Description

Build a CI pipeline where an agent performs *two* automation tasks:

1. **Skip unnecessary builds/tests** — implement test-impact analysis or build-skip logic so that the agent selects only the tests relevant to changed files, rather than running the full suite every time.

2. **Auto-remediate one class of failure** — choose one specific, well-defined failure type (for example: import errors caused by a missing `requirements.txt` entry, or a misconfigured environment variable, or a failing linter due to a formatting issue) and implement an agent that detects that failure class and proposes a fix via PR.

### Suggested Structure

Your submission should include:

```
submission/
├── README.md              ← describe your pipeline, design choices, and results
├── .github/workflows/     ← or Jenkinsfile
│   └── ci-agent.yml
├── src/                   ← application code (can be the calculator from the lab or your own)
├── tests/                 ← test suite
├── scripts/
│   ├── select_tests.py    ← test selection / impact analysis
│   └── remediation_agent.py
└── docs/
    └── guardrails.md      ← document your approval gates and blast-radius limits
```

### Rubric Hints

| Area | What reviewers look for |
|---|---|
| **Test selection** | Evidence that the agent actually skips tests on irrelevant changes (show before/after timing or test counts) |
| **Remediation accuracy** | The agent correctly identifies the target failure class and proposes a valid fix (not a spurious or harmful one) |
| **Guardrails** | Approval gate is genuinely blocking — not auto-approving; blast-radius limits are explicitly documented |
| **Prompt engineering** | System prompt is specific, scoped, and instructs the agent what it is *not* allowed to do |
| **Disclosure** | AI tools used in building the pipeline are disclosed; agent-generated code is reviewed |
| **Reflection** | README honestly describes one way the agent failed or surprised you |

### Notes on scope

- You may use any CI platform (GitHub Actions, Jenkins, GitLab CI, CircleCI).
- You may use any LLM API (Anthropic, OpenAI, Google Gemini) — the concepts transfer.
- The application under test can be minimal (5–10 functions) — the pipeline is the focus, not the application.
- Document your guardrails in `docs/guardrails.md` even if they are simple.
