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

![The lab flow, top to bottom: push code with an intentional bug → CI pipeline runs and the test stage FAILS (continue-on-error lets the agent run next) → the build-fixer agent activates (reads the build log, identifies the failing test and cause, proposes a minimal fix, and opens a PR with write-only, no-merge permission) → a human approval gate pauses the pipeline (a teammate reviews the PR then clicks Approve; it times out to abort, never auto-approves) → optional auto-merge to a feature branch, never to main → a green pipeline confirms the fix.](images/build-fixer-flow.svg)

> 💡 **A complete, runnable version of this lab ships in [`project/build-fixer/`](../../project/build-fixer/).** It has the buggy app, the GitHub Actions workflow, and the agent already wired up. You can `make demo` to watch the agent propose a fix locally (just an Anthropic key — no GitHub), then push it as your own repo for the full gated-PR flow. Build it yourself from the steps below for the learning, or start from the starter and modify it for the assignment.

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

**Option B — Jenkins.** Run the same flow on the course's Jenkins-in-Docker setup (`project/Jenkins/`, built in [Week 2](../week-02/week-02-lab.md)). Because the Jenkins path needs a few extra pieces the Actions path gets for free — an image with Python baked in, credentials, a job, and the built-in `input` gate — it has its own complete step-by-step at the end of this lab: **[Running the lab on Jenkins](#running-the-lab-on-jenkins-detailed-walkthrough)**. Steps 3–5 below (the agent script, the guardrail mindset, the deliverable) apply to both paths.

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

    # Structured outputs: output_config.format constrains the response to this
    # JSON schema, so the first text block is guaranteed-valid JSON — no
    # "please output ONLY JSON" begging, no parse failures to handle.
    fix_schema = {
        "type": "object",
        "properties": {
            "root_cause": {"type": "string"},
            "fix_description": {"type": "string"},
            "fixed_file_path": {"type": "string"},
            "fixed_file_content": {"type": "string"},
        },
        "required": [
            "root_cause", "fix_description", "fixed_file_path", "fixed_file_content",
        ],
        "additionalProperties": False,
    }

    response = client.messages.create(
        model="claude-opus-4-8",   # latest Opus; set MODEL=claude-haiku-4-5 for a cheaper run
        max_tokens=2048,
        system="""You are a build-fixer agent. Your only job is to identify
the root cause of a failing Python test and propose the minimal fix to the
source file. Change exactly one file: the source file under test, never the
test file. fixed_file_content must be the complete corrected file. Do not add
tests or make stylistic changes unrelated to the bug.""",
        output_config={"format": {"type": "json_schema", "schema": fix_schema}},
        messages=[{
            "role": "user",
            "content": (
                f"Build log:\n```\n{build_log}\n```\n\n"
                f"Source file (src/calculator.py):\n```python\n{source_code}\n```"
            )
        }]
    )

    fix = json.loads(next(b.text for b in response.content if b.type == "text"))
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

> **On Jenkins** the gate is the built-in **`input` step** (wrapped in `timeout`), not a GitHub environment — see [Running the lab on Jenkins](#running-the-lab-on-jenkins-detailed-walkthrough). The rest of this step is the GitHub Actions path.

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

## Running the lab on Jenkins (detailed walkthrough)

Steps 2–5 use GitHub Actions. Here is the equivalent end-to-end run on the course's **Jenkins-in-Docker** setup ([`project/Jenkins/`](../../project/Jenkins/), first built in [Week 2](../week-02/week-02-lab.md)). The GitHub `agent-proposed` *environment* is replaced by Jenkins' built-in **`input` step** as the human approval gate; everything else — the buggy app, the log, the agent script — is identical.

> **Why the Jenkinsfile has no `pip install`.** The `cstu-jenkins` image (`Dockerfile_Master`) bakes a Python venv onto `PATH` at `/opt/venv` with `pytest` and `anthropic` **pre-installed** — the stock `jenkins/jenkins` image is JVM-only, so a naïve `pip install` fails with `pip: not found`. Call `python` / `pytest` directly. (`PyGithub` is *not* baked in — only the optional "open a real PR" variant in J7 installs it at runtime.)

### J1 · Bring up Jenkins

Follow [`project/Jenkins/DEMO.md`](../../project/Jenkins/DEMO.md) (or Week 2). In short:

```bash
cd project/Jenkins
docker build -t cstu-jenkins -f Dockerfile_Master .
docker compose up -d
docker exec cstu-jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Open **http://localhost:8080**, unlock with that password, install suggested plugins, and create the admin user. (Behind a Zscaler-type TLS-inspecting proxy? Do DEMO.md's **opt-in CA step** first, or the image build fails to download plugins.)

### J2 · Add the API key as a credential

**Manage Jenkins → Credentials → System → Global credentials → Add Credentials:**

| Field | Value |
|---|---|
| Kind | **Secret text** |
| Secret | your `sk-ant-…` key |
| ID | `ANTHROPIC_API_KEY` |

`credentials('ANTHROPIC_API_KEY')` in the Jenkinsfile then exposes it as the `ANTHROPIC_API_KEY` env var — the credential ID and the env var share the same name, which is fine. (For J7's real-PR variant, add a second **Secret text** credential with ID `github-token` = a PAT with `repo` scope.)

### J3 · Give Jenkins the code to build

This walkthrough clones your **private course repo** (`CSE636`) **in full**. The build-fixer starter lives under [`project/build-fixer/`](../../project/build-fixer/), so the pipeline `cd`s into that subfolder with `dir('project/build-fixer')` (already wired into the J5 script below) and archives `project/build-fixer/build_log.txt`.

Because the repo is private, the `git` checkout needs a credential — and the Git plugin **can't** use the *Secret text* credential from J2 for cloning; it needs a **Username with password** one:

**Manage Jenkins → Credentials → System → Global credentials → Add Credentials:**

| Field | Value |
|---|---|
| Kind | **Username with password** |
| Username | your GitHub username |
| Password | a **PAT** — classic with `repo` scope, or fine-grained with **Contents: Read** |
| ID | `github-https` |

The J5 Jenkinsfile passes `credentialsId: 'github-https'` to the `git` step. If you see `No credentials specified` followed by `Authentication failed` in the log, this credential is missing or its **ID** doesn't match.

### J4 · Create the pipeline job

**New Item → Pipeline**, name it `build-fixer-demo`, **OK**. Scroll to **Pipeline**, choose **Pipeline script**, and paste the script from J5 (replace `<you>` with your GitHub username so the clone URL points at your `CSE636` fork). **Save**.

*(Alternative: choose **Pipeline script from SCM**, point it at your `CSE636` repo with the `github-https` credential, set **Script Path** to the committed `Jenkinsfile`. Then swap the `git …` step for `checkout scm` — but keep the `dir('project/build-fixer')` wrappers.)*

### J5 · The Jenkinsfile (dry-run — clones the private course repo)

This mirrors `make demo`: clone your private `CSE636` repo, produce the red build inside `project/build-fixer/`, let the agent propose a fix, print it, and pause for a human. It opens **no** PR, so it needs the `ANTHROPIC_API_KEY` secret (J2) and the `github-https` checkout credential (J3) — but no GitHub *token* for the agent itself.

```groovy
pipeline {
  agent any                    // single-container cstu-jenkins.
                               // For the Week 2 master/agent topology use: agent { label 'python-agent' }

  environment {
    ANTHROPIC_API_KEY = credentials('ANTHROPIC_API_KEY')  // the "Secret text" credential from J2
    MODEL = 'claude-haiku-4-5'                             // cheaper classroom run; omit for the default claude-opus-4-8
  }

  stages {
    stage('Checkout') {
      steps {
        // private repo → the Username/password credential from J3 (replace <you>)
        git branch: 'main',
            url: 'https://github.com/<you>/CSE636.git',
            credentialsId: 'github-https'
      }
    }

    stage('Test (expect red)') {
      steps {
        dir('project/build-fixer') {             // the starter lives in this subfolder of the course repo
          script {
            // returnStatus lets the red build continue so the agent stage can run.
            // Redirect (don't pipe): `pytest … | tee` would report tee's exit code
            // (always 0) and hide the failure, so the gated stages would be skipped.
            def rc = sh(script: 'pytest tests/test_calculator.py --tb=short > build_log.txt 2>&1',
                        returnStatus: true)
            sh 'cat build_log.txt'               // still show the log in the console
            env.TESTS_FAILED = (rc != 0) ? 'true' : 'false'
          }
          echo "Tests failed? ${env.TESTS_FAILED}"
        }
      }
    }

    stage('Agent: propose fix') {
      when { expression { env.TESTS_FAILED == 'true' } }
      steps {
        dir('project/build-fixer') {             // same subfolder as the test stage
          // --dry-run prints the root cause + corrected file and opens NO PR
          sh 'python scripts/build_fixer_agent.py --dry-run'
        }
      }
    }

    stage('Human approval gate') {
      when { expression { env.TESTS_FAILED == 'true' } }
      steps {
        // input pauses the build until a person clicks Proceed. Wrapping it in
        // timeout means an unattended build ABORTS — it never auto-approves.
        timeout(time: 60, unit: 'MINUTES') {
          input message: 'Agent proposed a fix (see the log above). Review it, then Proceed to confirm — or Abort.'
        }
      }
    }
  }

  post {
    // build_log.txt is written inside the subfolder, so archive that path
    always { archiveArtifacts artifacts: 'project/build-fixer/build_log.txt', allowEmptyArchive: true }
  }
}
```

### J6 · Run it and watch the gate

1. **Build Now**, then open the run in **Blue Ocean** (http://localhost:8080/blue) or the classic **Stage View**.
2. **Test (expect red)** goes red — but the pipeline keeps going (that's the `returnStatus` trick; a normal `sh` failure would abort the build here).
3. **Agent: propose fix** prints the agent's `root_cause`, `fix_description`, and the full corrected `calculator.py` in the console log.
4. **Human approval gate** turns **paused/blue** with a prompt. This is the guardrail: nothing proceeds on its own.
5. Read the proposed fix in the log, then click **Proceed** to finish green — or **Abort** to reject it. Leave it untouched for 60 minutes and the `timeout` aborts the build.

`build_log.txt` is archived on every run (**Build → Artifacts**) — a convenient source for your deliverable screenshots.

### J7 · Optional: open a real PR from Jenkins

To mirror the Actions gated-PR flow (agent opens a no-merge PR; a human merges it), add a `github-token` credential (J2), then use these `environment` and stage edits:

```groovy
  environment {
    ANTHROPIC_API_KEY = credentials('ANTHROPIC_API_KEY')
    GH_TOKEN          = credentials('github-token')   // "Secret text" — perms below
    REPO              = '<you>/CSE636'                 // the agent opens the PR here
    BASE_BRANCH       = 'main'
  }
  // …
    stage('Agent: open PR') {
      when { expression { env.TESTS_FAILED == 'true' } }
      steps {
        // Run from the repo root and pass FULL --source/--log paths so the commit
        // lands on the right file inside the monorepo (project/build-fixer/src/...).
        sh 'pip install --quiet PyGithub'   // anthropic is baked into the image; PyGithub is not
        sh '''python project/build-fixer/scripts/build_fixer_agent.py --open-pr \
                --log    project/build-fixer/build_log.txt \
                --source project/build-fixer/src/calculator.py'''
      }
    }
```

**Token permissions** — `github-token` needs *write* access to your fork, and the exact settings matter (a read-only or PRs-only token 403s):
- **Fine-grained PAT:** Repository access = your `CSE636` fork; **Contents: Read and write** *and* **Pull requests: Read and write**. (Contents-write is what commits the fix — the most common miss.)
- **Classic PAT:** the top-level **`repo`** scope.

**How the agent writes the fix:** it commits the corrected file on a `bot/fix-build-<n>` branch and **`git push`**es it, then uses the REST API only to *open* the PR (a call with no source payload). It does **not** use the REST contents API to write files — see the proxy note below for why. The token opens the PR but can't merge; merging stays a human action, exactly as in the Actions path.

Keep the **Human approval gate** stage *after* this one, and read "Proceed" as *"I reviewed the agent's PR on GitHub and merged it myself."*

<details><summary>🌐 Behind a TLS-inspecting corporate proxy (e.g. Zscaler)?</summary>

Two failures you may hit — both come from the proxy, not your code or token:

1. **`certificate verify failed: Basic Constraints of CA cert not marked critical`.** Modern Python / OpenSSL 3.x enables `VERIFY_X509_STRICT`, which rejects the proxy's root CA even though it's trusted. `build_fixer_agent.py` handles this for **both** of its HTTP clients — httpx (Anthropic) and `requests` (PyGithub) — by clearing that one flag while keeping full chain + hostname verification.
2. **A 403 on the GitHub REST *contents* API for source files.** A proxy DLP rule can block `.py` payloads — `GET /repos/.../contents/x.py` returns 403 while `.md` returns 200, at any path depth. A token can't filter by file extension, so this is the proxy, not GitHub auth. The agent sidesteps it by moving the fix over **git** (the pack protocol isn't inspected — your `git clone` / `git push` work) and calling REST only to open the PR.

If even `git push` is blocked, no source can leave the network to GitHub by any channel — run the **dry-run** J5 pipeline in Jenkins and open real PRs from **GitHub Actions** (Option A, outside the proxy) instead.

</details>

<details><summary>✅ Check your understanding — is the Jenkins gate actually a gate?</summary>

- The `input` step **blocks** on a real person — there is no "approve after N minutes." The surrounding `timeout` **aborts**; it never proceeds. Prove it: start a build and walk away — it should end **ABORTED**, not **SUCCESS**.
- The `github-token` can *open* a PR (commit + push a branch) but **cannot merge** — grant it no admin/merge rights and rely on branch protection. The merge is a human click on GitHub.
- Want to restrict *who* may approve? Add `submitter: 'your-username'` to the `input` step — then only that user's Proceed counts.

Remove the human and nothing dangerous can still happen — that is the test of a real gate.

</details>

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
