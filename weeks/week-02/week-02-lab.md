# Week 2 — Lab & Assignment

> 🧪 **Hands-on work for Week 2.** For the lecture notes, foundations primer, discussion questions, and references, see **[week-02-notes.md](week-02-notes.md)**.

---

## 🧪 Lab — Week 2

**Goal:** Deploy a pipeline that invokes an AI agent for code review, and connect a simple MCP server that exposes build status to the agent.

**Estimated time:** 2–3 hours (can be split: pipeline in class, MCP server at home)

**What you need:**
- Docker installed and running
- An Anthropic API key (free tier is fine for the lab)
- Git and GitHub account
- Python 3.10+

> 🎯 **At a glance**
>
> | | |
> |---|---|
> | **Part 1** | A Jenkins pipeline (built from `Dockerfile_Master`) with a Lint → Test → **AI Code Review** stage |
> | **Part 2** | A minimal **MCP server** exposing live Jenkins build status to Claude Code |
> | **Submit** | Build screenshot, the AI review report, your MCP server code, and a permissions reflection |
> | **Ties to notes** | The [MCP host/client/server model](week-02-notes.md#concept-the-model-context-protocol-mcp) and [least-privilege](week-02-notes.md#concept-secrets-credentials-and-permission-management-for-agents) |

---

### Part 1: Stand Up the Jenkins Pipeline

**Step 1: Clone the course repository and navigate to the Jenkins project.**

```bash
git clone https://github.com/<your-fork>/CSE636.git
cd CSE636/project/Jenkins
```

**Step 2: Build the Jenkins master image.**

```bash
docker build -t cstu-jenkins -f Dockerfile_Master .
```

This builds the image defined in `Dockerfile_Master` — Jenkins 2.571 on JDK 21, with Docker CLI, Blue Ocean plugins, **and a Python 3 toolchain** (a venv on `PATH`) with the pipeline's dependencies (`flake8`, `pytest`, `anthropic`, `mcp`, `requests`) **pre-installed**. The Lint/Test/AI-Review stages run `python3` directly on the controller (`agent any`), so the image carries Python and its deps — the stock `jenkins/jenkins` image does not, and baking the deps in means builds don't `pip install` on every run. It takes a few minutes the first time.

> ⚠️ **`pip: not found` in the pipeline?** The stock Jenkins image ships only the JVM — no Python, no `pip` — so `pip install ...` fails on `agent any`. The course `Dockerfile_Master` fixes this by installing Python into a venv. If you hit this error, you're running an image built *before* that change (or the stock image): rebuild with `docker build -t cstu-jenkins -f Dockerfile_Master .`, then `docker compose up -d --force-recreate`.

**Step 3: Start Jenkins.**

```bash
docker compose up -d
```

**Step 4: Get the initial admin password and complete setup.**

```bash
docker exec cstu-jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Open `http://localhost:8080` in your browser, enter the password, install suggested plugins, and create your admin user.

> 📁 **Before you build: prepare your sample repo.** The pipeline checks out `sample-python-app` and runs `flake8`, `pytest`, and the AI review against it — so that repo needs source **and a `tests/` directory**, or the Test stage fails with `file or directory not found: tests/`. A minimal layout that exercises every stage:
>
> ```
> sample-python-app/
> ├── app.py                # any Python source for lint + AI review to chew on
> ├── conftest.py           # empty — puts the repo root on sys.path so `import app` works
> ├── scripts/
> │   └── ai_review.py      # the script from Step 6
> └── tests/
> │   └── test_app.py       # at least one test so pytest collects something
> ```
>
> Minimal `app.py` and `tests/test_app.py`:
>
> ```python
> # app.py
> def add(a, b):
>     return a + b
> ```
>
> ```python
> # tests/test_app.py
> from app import add
>
> def test_add():
>     assert add(2, 3) == 5
> ```
>
> **Why `import app` works:** by default `pytest` puts the *test file's* directory (`tests/`) on `sys.path`, **not** the repo root — so a bare `pytest tests/` fails with `ModuleNotFoundError: No module named 'app'`. Two things prevent that, and the lab uses both:
>
> 1. **The pipeline runs `python -m pytest tests/ -v`** (not bare `pytest`). The `-m` form prepends the current working directory — the workspace root, where `app.py` lives — onto `sys.path`, so the import resolves regardless of any config file. This is what actually fixes it in CI.
> 2. **The empty root `conftest.py`** does the same thing for anyone running plain `pytest` **locally**, and is standard practice. Create it empty: `touch conftest.py`.
>
> Commit and push all of these before triggering the pipeline. (A *failing* test should still red the build — that's the point of the Test stage; only a *missing* `tests/` dir is handled gracefully below.)

**Step 5: Create a sample pipeline job.**

In Jenkins, create a new Pipeline job named `ai-review-demo`. Use this starter `Jenkinsfile`:

```groovy
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                deleteDir()   // start every build from an empty workspace
                git url: 'https://github.com/<your-username>/sample-python-app.git',
                    branch: 'main'
            }
        }

        stage('Lint') {
            steps {
                // flake8/pytest/anthropic are pre-installed in the image (see
                // Dockerfile_Master) — no `pip install` needed on every build.
                sh 'flake8 . --max-line-length=120 || true'
            }
        }

        stage('Test') {
            steps {
                sh '''
                    if [ -d tests ]; then
                        python -m pytest tests/ -v
                    else
                        echo "No tests/ directory — add one to your sample repo (see the callout above). Skipping."
                    fi
                '''
            }
        }

        stage('AI Code Review') {
            steps {
                withCredentials([string(credentialsId: 'ANTHROPIC_API_KEY',
                                        variable: 'ANTHROPIC_API_KEY')]) {
                    sh 'python3 scripts/ai_review.py'
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'ai_review_report.txt', allowEmptyArchive: true
            // No deleteDir() here: the workspace persists after the build so you
            // can inspect it (Job → Workspace). Each build still starts clean
            // thanks to the deleteDir() at the top of Checkout.
        }
    }
}
```

> 🧹 **Clean workspace every build.** `deleteDir()` (built into core Pipeline — no plugin) at the **start of Checkout** empties the workspace before the fresh clone, so each run starts from a clean slate and stale files can't mask a problem (e.g. a leftover `ai_review_report.txt` or an old `tests/`). We deliberately do **not** clean in `post`, so the workspace persists after the build for inspection (Job → **Workspace**); `archiveArtifacts` has already copied the report into the build's artifacts either way. If you'd rather leave nothing behind, add `deleteDir()` in `post { always }` **after** `archiveArtifacts` (order matters — archiving reads the report from the workspace, so clean *after*). If you have the **Workspace Cleanup** plugin, `cleanWs()` is a drop-in replacement with extra options (keep patterns, clean only on success/failure).

**Step 6: Create the AI review script.**

Create `scripts/ai_review.py` in your sample repo:

```python
#!/usr/bin/env python3
"""
AI code review step for the CSE636 Week 2 lab.
Reads recently changed Python files and asks Claude for a code review.
"""
import os
import ssl
import subprocess
import certifi
import anthropic
import httpx  # bundled with the anthropic SDK

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# TLS trust behind an inspecting proxy (e.g. Zscaler). The anthropic SDK verifies
# via httpx against certifi's bundle — NOT the OS store. Build the SSL context
# explicitly from a bundle that includes the corporate root CA (SSL_CERT_FILE /
# REQUESTS_CA_BUNDLE, else certifi's default), then clear VERIFY_X509_STRICT:
# Python 3.13 turns on strict RFC 5280 verification by default, and many corporate
# CAs (Zscaler) ship a CA cert whose basicConstraints isn't marked critical, which
# strict mode rejects ("Basic Constraints of CA cert not marked critical"). We
# still require a valid cert, full chain, and hostname match — only the
# over-strict RFC check is relaxed.
_ca_bundle = (os.environ.get("SSL_CERT_FILE")
              or os.environ.get("REQUESTS_CA_BUNDLE")
              or certifi.where())
_ssl_ctx = ssl.create_default_context(cafile=_ca_bundle)
_ssl_ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
client = anthropic.Anthropic(
    api_key=ANTHROPIC_API_KEY,
    http_client=httpx.Client(verify=_ssl_ctx),
)

def get_changed_files():
    """Python files changed in the last commit; fall back to all tracked .py files.

    The diff is empty when the last commit touched no .py file, the repo has a
    single commit (no HEAD~1), or Jenkins did a shallow clone. In those cases we
    review every tracked .py file so the stage always produces output.
    """
    diff = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
        capture_output=True, text=True
    )
    changed = (
        [f for f in diff.stdout.strip().split("\n") if f.endswith(".py")]
        if diff.returncode == 0 else []
    )
    if changed:
        return changed

    # Fallback: review all tracked Python files.
    listed = subprocess.run(
        ["git", "ls-files", "*.py"],
        capture_output=True, text=True
    )
    return [f for f in listed.stdout.strip().split("\n") if f.endswith(".py")]

def read_file(path):
    try:
        with open(path) as fh:
            return fh.read()
    except FileNotFoundError:
        return None

def review_code(filename, content):
    """Ask Claude to review a single file."""
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Please review the following Python file for correctness, "
                    f"style issues, and potential bugs. Be concise.\n\n"
                    f"Filename: {filename}\n\n"
                    f"```python\n{content}\n```"
                )
            }
        ]
    )
    return message.content[0].text

def main():
    changed = get_changed_files()
    if not changed:
        print("No Python files found in the repo. Skipping AI review.")
        with open("ai_review_report.txt", "w") as fh:
            fh.write("No Python files found in the repo.\n")
        return

    report_lines = ["# AI Code Review Report\n"]
    for filepath in changed:
        content = read_file(filepath)
        if content is None:
            continue
        print(f"Reviewing {filepath}...")
        review = review_code(filepath, content)
        report_lines.append(f"\n## {filepath}\n\n{review}\n")
        print(f"Review for {filepath}:\n{review}\n")

    with open("ai_review_report.txt", "w") as fh:
        fh.write("\n".join(report_lines))
    print("AI review complete. Report saved to ai_review_report.txt")

if __name__ == "__main__":
    main()
```

> 🔎 **"No Python files changed. Skipping AI review."** The script reviews files changed in the **last commit** (`git diff HEAD~1 HEAD`). That diff is empty — and you'd see the skip message — when the triggering commit touched no `.py` file, the repo has a single commit (no `HEAD~1`), or Jenkins did a shallow clone. The version above **falls back to reviewing all tracked `.py` files** in that case, so the stage always produces a report. (If you want to keep the strict "only review the diff" behavior, drop the fallback branch — then push a change to a `.py` file to give it something to review.)

**Step 7: Add your API key to Jenkins credentials.**

In Jenkins: Manage Jenkins → Credentials → (global) → Add Credentials → Secret text. Set the ID to `ANTHROPIC_API_KEY` and paste your key.

**Step 8: Trigger a build and verify the AI review report is generated.**

Push a small change to your sample repo. Trigger the pipeline. Check the build artifacts for `ai_review_report.txt`.

> 🔐 **`CERTIFICATE_VERIFY_FAILED` in the AI Code Review stage?** If the API call dies with `[SSL: CERTIFICATE_VERIFY_FAILED] unable to get local issuer certificate`, you're behind a **TLS-inspecting proxy** (e.g. Zscaler on a corporate network). The proxy re-signs HTTPS with a corporate root CA the container doesn't trust — and the Python SDK verifies against its own bundle, separate from the OS and JVM stores. Fix it in three moves:
>
> 1. **Get the corporate root CA** as a PEM (export it from your OS keychain, or ask IT) and drop it at `project/Jenkins/certs/corp-ca.pem`. (`certs/*.pem` is gitignored — it won't be committed.)
> 2. **Rebuild the image and recreate the container.** `Dockerfile_Master`'s CA block adds the cert to the OS trust store (`/etc/ssl/certs/ca-certificates.crt`) and the JVM truststore:
>    ```bash
>    cd project/Jenkins
>    docker build -t cstu-jenkins -f Dockerfile_Master .
>    docker compose up -d --force-recreate
>    ```
> 3. **That's the whole fix.** The rebuilt image bakes your corp CA into Python's **certifi** bundle and sets `REQUESTS_CA_BUNDLE`, so both the anthropic SDK (httpx) *and* the Part 2 MCP server (requests) trust the proxy with **no code changes**. (`ai_review.py` also reads `SSL_CERT_FILE` as a belt-and-suspenders fallback.)
>
> **Key gotcha:** the OS trust store fixing `curl`/`apt` is **not** enough for Python — httpx verifies against certifi, ignoring the OS store *and* `SSL_CERT_FILE`. Baking the CA into certifi (done in `Dockerfile_Master`) is what actually fixes the SDK. So if `openssl ... -CAfile /etc/ssl/certs/ca-certificates.crt` reports `Verify return code: 0 (ok)` but Python still fails with `CERTIFICATE_VERIFY_FAILED`, you have an image built *before* the certifi step — rebuild and `--force-recreate`.
>
> **Second gotcha — `Basic Constraints of CA cert not marked critical`.** Once the CA *is* trusted you may hit this variant. It means the CA was found but rejected under **Python 3.13's strict RFC 5280 verification** (`VERIFY_X509_STRICT`, on by default), because the Zscaler CA cert doesn't mark its `basicConstraints` extension critical — non-compliant, but common. `openssl s_client` passes the same cert because it doesn't use strict mode. `ai_review.py` (Step 6) handles this by building the SSL context and clearing `VERIFY_X509_STRICT` while keeping normal verification (chain, expiry, hostname). If you hit it elsewhere (e.g. the Part 2 `requests`-based MCP server), apply the same `ssl.create_default_context(...)` + `verify_flags &= ~ssl.VERIFY_X509_STRICT` pattern.
>
> See [`project/Jenkins/DEMO.md`](../../project/Jenkins/DEMO.md) for more on the opt-in CA trust. On an open network (no proxy) you won't hit any of this and can skip it entirely.

---

### Part 1 (variant): Run pipeline stages in a Python container

> 🔁 **More production-like.** The main path above runs `python3` **on the Jenkins controller** (`agent any`), which is why the image carries Python and its deps pre-installed. The DevOps-correct pattern is instead to run each build stage in a **throwaway container** — the controller stays lean, and every build gets a clean, pinned toolchain. This uses the `docker-workflow` plugin (already installed in `Dockerfile_Master`). It's optional; do it if you want to see the containerized-agent pattern the rest of the course leans on.
>
> Because each stage starts from a stock `python:3.11-slim`, the deps baked into `cstu-jenkins` **don't apply here** — that's why this variant keeps `pip install` in each stage (a fresh container has no packages). Two consequences: (1) each build re-installs (cache with a persistent pip dir or a custom image if that bothers you); (2) **behind a TLS-inspecting proxy the slim container won't trust your corp CA** (the certifi/OS-store fix lives in `cstu-jenkins`, not `python:3.11-slim`), so on a corporate network prefer the main path, or build a small custom image `FROM python:3.11-slim` that adds your CA and the deps, and reference it in `image '...'`.

**Step 1: Give Jenkins access to the Docker daemon.** A container-based agent means Jenkins must be able to run `docker` against the host daemon, so mount the Docker socket into the Jenkins container. Edit `docker-compose.yml`:

```yaml
services:
  jenkins:
    image: cstu-jenkins
    user: root                                    # needed to access the mounted socket
    ports:
      - "8080:8080"
    volumes:
      - jenkins_data_cstu:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock  # let Jenkins launch sibling containers
    restart: unless-stopped

volumes:
  jenkins_data_cstu:
```

Then recreate the container: `docker compose up -d --force-recreate`.

> ⚠️ **`user: root` is a lab shortcut.** The host socket is owned by `root:docker`, and the in-container `jenkins` user isn't in that group, so the simplest cross-platform fix is to run the container as root. **Don't do this in production** — there it's equivalent to host root. The production-correct alternative is to drop `user: root` and instead add the host's Docker group GID (`getent group docker | cut -d: -f3`) via `group_add: ["<gid>"]`, so only socket access is granted. (On Docker Desktop / Rancher Desktop the in-VM GID varies, which is why `user: root` is the reliable teaching default.)

**Step 2: Use a Docker agent per stage.** Replace the `Jenkinsfile` with this variant. `reuseNode true` runs each stage's container on the same node and **shares the workspace**, so the checkout done on the controller is visible to the Python stages — no `stash`/`unstash` needed. Checkout stays on `agent any` because the `git` step needs a `git` binary (present on the controller; **not** in `python:*-slim`).

```groovy
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/<your-username>/sample-python-app.git',
                    branch: 'main'
            }
        }

        stage('Lint') {
            agent { docker { image 'python:3.11-slim'; reuseNode true } }
            steps {
                sh 'pip install flake8 && flake8 . --max-line-length=120 || true'
            }
        }

        stage('Test') {
            agent { docker { image 'python:3.11-slim'; reuseNode true } }
            steps {
                sh '''
                    pip install pytest
                    if [ -d tests ]; then
                        python -m pytest tests/ -v
                    else
                        echo "No tests/ directory — add one to your sample repo (see the callout above). Skipping."
                    fi
                '''
            }
        }

        stage('AI Code Review') {
            agent { docker { image 'python:3.11-slim'; reuseNode true } }
            steps {
                withCredentials([string(credentialsId: 'ANTHROPIC_API_KEY',
                                        variable: 'ANTHROPIC_API_KEY')]) {
                    sh '''
                        pip install anthropic
                        # Trust the OS CA bundle (includes the corp root CA after
                        # rebuilding the image with certs/ populated — see callout).
                        export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
                        python3 scripts/ai_review.py
                    '''
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'ai_review_report.txt', allowEmptyArchive: true
        }
    }
}
```

**What changed and why it matters:**
- Each Python stage runs in a fresh `python:3.11-slim` container that already has `pip` — so `pip install` works cleanly with **no PEP 668 workaround** (unlike the controller's Debian venv).
- With this variant the controller no longer needs Python baked in; the toolchain lives in the stage image and is **pinned** (`python:3.11-slim`) rather than "whatever the controller happens to have."
- Trade-off: the first build pulls the `python:3.11-slim` image (a one-time delay), and you took on the Docker-socket mount — a real privilege you should scope carefully (hence the `group_add` note above).

---

### Part 1 (variant B): Master + a dedicated Python agent (distributed builds)

> 🏗️ **Classic controller/agent architecture.** The two setups above run builds **on the controller** (`agent any`) or in **throwaway containers** (docker-workflow). This third option is the traditional Jenkins **master/agent** ("controller/node") pattern: a separate long-lived **agent container** registers with the master and executes the builds, so the controller only orchestrates. This is how real Jenkins farms scale out.

> 🧰 **How the agent is built.** The modern, supported way to run an agent is the official **`jenkins/inbound-agent`** image, which self-connects to the master over a WebSocket. The repo ships [`Dockerfile_Agent_Inbound`](../../project/Jenkins/Dockerfile_Agent_Inbound) (inbound-agent + the same Python toolchain as `Dockerfile_Master`) and [`docker-compose.agent.yml`](../../project/Jenkins/docker-compose.agent.yml) (master + agent, sharing the `jenkins_data_cstu` volume). (This replaces the old `jenkins/jenkins`-era "slave" pattern built on EOL `ubuntu:16.04` + Java 8 + Python 2.)

**Step 1: Build both images.**

```bash
cd project/Jenkins
docker build -t cstu-jenkins       -f Dockerfile_Master        .
docker build -t cstu-jenkins-agent -f Dockerfile_Agent_Inbound .
```

**Step 2: Start the master.**

```bash
docker compose -f docker-compose.agent.yml up -d jenkins
```

**Step 3: Register the agent node (one-time — JNLP needs a per-node secret).** In Jenkins → **Manage Jenkins → Nodes → New Node**:
- Name `python-agent`, type **Permanent Agent**
- **Remote root directory:** `/home/jenkins/agent`
- **Labels:** `python-agent`
- **Launch method:** *Launch inbound agent*

Save, open the `python-agent` node page, and copy the **secret** string. Put it in a `.env` file next to the compose file:

```bash
echo "JENKINS_SECRET=<paste-secret>" > .env
```

> Why the manual step? An inbound agent authenticates to the master with a per-node secret that only exists *after* you create the node. Compose can't know it in advance. (Production setups automate this with [JCasC](https://www.jenkins.io/projects/jcasc/) or the master/agent being pre-seeded — out of scope here.)

**Step 4: Start the agent.**

```bash
docker compose -f docker-compose.agent.yml up -d agent
```

The node should go **online** (Manage Jenkins → Nodes → `python-agent`). `JENKINS_WEB_SOCKET=true` means it connects over port 8080 — no TCP agent port to open.

**Step 5: Pin the pipeline to the agent.** Use the same `Jenkinsfile` as Step 5 of the main path, but change the top line from `agent any` to the agent's label — the deps are baked into the agent image, so nothing installs per build:

```groovy
pipeline {
    agent { label 'python-agent' }   // run on the dedicated Python node, not the controller

    stages {
        stage('Checkout') {
            steps {
                deleteDir()
                git url: 'https://github.com/<your-username>/sample-python-app.git',
                    branch: 'main'
            }
        }
        stage('Lint') {
            steps { sh 'flake8 . --max-line-length=120 || true' }
        }
        stage('Test') {
            steps {
                sh '''
                    if [ -d tests ]; then
                        python -m pytest tests/ -v
                    else
                        echo "No tests/ directory — skipping."
                    fi
                '''
            }
        }
        stage('AI Code Review') {
            steps {
                withCredentials([string(credentialsId: 'ANTHROPIC_API_KEY',
                                        variable: 'ANTHROPIC_API_KEY')]) {
                    sh 'python3 scripts/ai_review.py'
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'ai_review_report.txt', allowEmptyArchive: true
        }
    }
}
```

**How the three approaches compare:**

| Approach | Where builds run | Python comes from | Needs |
|---|---|---|---|
| **Main** (`agent any`) | the controller | baked into `cstu-jenkins` | nothing extra |
| **Variant A** (docker-workflow) | throwaway per-stage containers | the stage image (`python:3.11-slim`) | Docker socket mounted |
| **Variant B** (master/agent) | a dedicated agent node | baked into `cstu-jenkins-agent` | the agent container + node registration |

Variant B is the most true-to-production (controller orchestrates, agents execute) and keeps the controller lean without granting Docker-socket access — at the cost of running and registering a second container.

---

### Part 2: Stand Up a Minimal MCP Server

**Step 1: Create the MCP server file.**

In your local environment (not inside Jenkins), create `mcp_servers/jenkins_status.py`:

```python
#!/usr/bin/env python3
"""
Minimal MCP server that exposes Jenkins build status to an AI agent.
CSE636 Week 2 Lab — Part 2.

Install: pip install mcp requests
"""
import os
import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

JENKINS_URL = os.environ.get("JENKINS_URL", "http://localhost:8080")
JENKINS_USER = os.environ.get("JENKINS_USER", "admin")
JENKINS_TOKEN = os.environ.get("JENKINS_TOKEN", "")

app = Server("cse636-jenkins-mcp")

@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_build_status",
            description=(
                "Returns the status and number of the most recent Jenkins build "
                "for a given job. Use this to check if a CI pipeline is currently "
                "passing or failing before making code changes."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "job_name": {
                        "type": "string",
                        "description": "The Jenkins job name, e.g. 'ai-review-demo'"
                    }
                },
                "required": ["job_name"]
            }
        ),
        Tool(
            name="list_jobs",
            description="Returns a list of all Jenkins job names.",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    auth = (JENKINS_USER, JENKINS_TOKEN) if JENKINS_TOKEN else None

    if name == "list_jobs":
        resp = requests.get(
            f"{JENKINS_URL}/api/json?tree=jobs[name]",
            auth=auth, timeout=10
        )
        jobs = [j["name"] for j in resp.json().get("jobs", [])]
        return [TextContent(type="text", text=f"Jenkins jobs: {', '.join(jobs)}")]

    if name == "get_build_status":
        job = arguments["job_name"]
        resp = requests.get(
            f"{JENKINS_URL}/job/{job}/lastBuild/api/json",
            auth=auth, timeout=10
        )
        if resp.status_code == 404:
            return [TextContent(type="text", text=f"Job '{job}' not found.")]
        data = resp.json()
        result = data.get("result", "IN_PROGRESS")
        number = data.get("number", "?")
        return [TextContent(
            type="text",
            text=f"Job '{job}': build #{number} — {result}"
        )]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]

if __name__ == "__main__":
    import asyncio
    asyncio.run(stdio_server(app))
```

**Step 2: Install dependencies and test the server standalone.**

```bash
pip install mcp requests

# Test it directly (press Ctrl-C to exit)
JENKINS_URL=http://localhost:8080 \
JENKINS_USER=admin \
JENKINS_TOKEN=<your-token> \
python mcp_servers/jenkins_status.py
```

**Step 3: Register the MCP server with Claude Code.**

Create or edit `~/.claude/claude.json`:

```json
{
  "mcpServers": {
    "cse636-jenkins": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_servers/jenkins_status.py"],
      "env": {
        "JENKINS_URL": "http://localhost:8080",
        "JENKINS_USER": "admin",
        "JENKINS_TOKEN": "your-token-here"
      }
    }
  }
}
```

**Step 4: Test the integration with Claude Code.**

```bash
claude "List all Jenkins jobs and tell me the status of the ai-review-demo job."
```

Observe: Claude Code should call the `list_jobs` and `get_build_status` tools and incorporate the live results into its response.

<details><summary>✅ Did it work? Confirm it's a real tool call, not a guess</summary>

You've succeeded when the agent's answer reflects **live** state — the actual job names from *your* Jenkins and the real build number/result — not a plausible-sounding invented answer.

- If Claude Code answers without ever calling the tool, check that `~/.claude/claude.json` points at the **absolute path** of `jenkins_status.py` and that the server starts standalone (Part 2, Step 2).
- If the tool call errors, verify `JENKINS_URL`, `JENKINS_USER`, and a valid `JENKINS_TOKEN` (Manage Jenkins → API token).
- Sanity check: stop Jenkins (`docker compose stop`) and ask again — a real tool call now fails/empties, proving the agent was querying live infrastructure rather than its training data.

</details>

---

### Part 2 (variant): GitHub Actions build status

> 🔁 **Prefer managed CI?** This variant exposes **GitHub Actions** run status instead of Jenkins — same MCP concept, no self-hosted server to keep running. The two are intentionally parallel (Jenkins REST API ↔ GitHub Actions REST API); doing both is the clearest way to see that MCP is CI-agnostic. A runnable server ships in [`project/build-fixer/mcp_servers/actions_status.py`](../../project/build-fixer/mcp_servers/actions_status.py), so you can point it at the [build-fixer](../../project/build-fixer/) repo's live Actions runs.

**Step 1: Get the server.** Use the bundled `mcp_servers/actions_status.py`. It exposes two tools — `list_workflows` and `get_run_status` (optionally filtered by branch) — and queries `https://api.github.com/repos/{owner}/{repo}/actions/...` with a token.

**Step 2: Install dependencies and test it standalone.**

```bash
pip install mcp requests

# Test it directly (press Ctrl-C to exit)
GH_TOKEN=<your-token> \
REPO=<your-username>/build-fixer \
python project/build-fixer/mcp_servers/actions_status.py
```

`GH_TOKEN` needs only `actions:read` (a fine-grained PAT scoped to the one repo is ideal — least privilege). `REPO` is `owner/name`.

**Step 3: Register the MCP server with Claude Code.** In `~/.claude/claude.json`:

```json
{
  "mcpServers": {
    "cse636-actions": {
      "command": "python",
      "args": ["/absolute/path/to/project/build-fixer/mcp_servers/actions_status.py"],
      "env": {
        "GH_TOKEN": "your-token-here",
        "REPO": "your-username/build-fixer"
      }
    }
  }
}
```

**Step 4: Test the integration.**

```bash
claude "List the workflows in my repo and tell me whether the latest run on main is green."
```

Claude Code should call `list_workflows` and `get_run_status` and report the **live** run number and conclusion — not a guess. Same sanity check as the Jenkins version: push a commit that fails CI, ask again, and confirm the agent reports the real red run.

> **Why this matters for least privilege:** the Jenkins server held an admin-scoped API token; this one needs only read access to one repo's Actions. Note that contrast in your reflection — narrower scope, smaller blast radius.

---

### What to Submit

1. A **screenshot** of a successful Jenkins build showing the `ai_review_report.txt` artifact.
2. The **`ai_review_report.txt`** file from one run.
3. Your **MCP server** code — `jenkins_status.py` or the `actions_status.py` variant (with comments explaining each section).
4. A **short reflection** (300–500 words): What did the AI review catch that a linter missed? What did it miss? What permissions did you grant the MCP server, and how did you scope them?

---

### 🔑 Lab Rubric Hints

| Element | Points | What we are looking for |
|---|---|---|
| Pipeline runs end-to-end | 30 | All four stages complete; AI Review stage produces a report |
| AI review quality | 20 | Report is substantive (not just "looks good"); shows actual analysis |
| MCP server works | 30 | Claude Code successfully calls at least one MCP tool with live data |
| Permissions reflection | 20 | Thoughtful discussion of what permissions were granted and why; how you would tighten them |

---

## Assignment — Week 2

### Prompt

Compare at least two agent frameworks or AI coding agents and propose an integration **and governance** plan for a mid-sized software team (imagine a team of 25 engineers, a codebase of ~150 repositories, and a production environment on AWS or GCP).

Emphasis is equally split between the **technical integration** plan and the **governance** plan. Many students over-invest in the technology comparison and under-develop the governance half — that is the harder and more important problem.

---

### Suggested Structure

**1. Introduction (1 page)**
- Which two agents/frameworks you are comparing and why you chose them.
- The team context: size, tech stack, current DevOps maturity.

**2. Technical Comparison (2–3 pages)**

For each agent/framework, cover:

| Dimension | Questions to answer |
|---|---|
| Capabilities | What can it do autonomously? What requires human input? |
| Integration | How does it connect to your tools (Git, CI, issue tracker, monitoring)? MCP support? |
| Cost model | Per-token API cost? Flat subscription? Self-hosted option? |
| Autonomy level | Where does it sit on the autonomy spectrum for common DevOps tasks? |
| Strengths | What tasks does it handle well? What is it uniquely good at? |
| Weaknesses / risks | Where does it fail or create risk? What has it been known to do wrong? |

Include a comparison table that summarizes the above for both agents side-by-side.

**3. Integration Plan (1–2 pages)**

Describe *how* you would introduce the chosen agent(s) into the team's workflow:

- What tasks would you automate first? (Start with low-risk, high-value.)
- Which tools need MCP servers or API integrations?
- What does the rollout timeline look like? (Pilot team → broader team → full rollout.)
- How would you measure success? (MTTR reduction, PR review time, test coverage improvement.)

**4. Governance Plan (2–3 pages)** ← This is the important half.

Address all of the following:

**Permissions and credentials:**
- What permissions will the agent have? Be specific (e.g., "read access to all repos in the `backend` GitHub org; write access only to branches prefixed `agent/`").
- How will credentials be stored and rotated?
- How will you implement least privilege?

**Human oversight:**
- For each type of action the agent can take (code change, PR creation, deployment trigger, etc.), what level of human oversight is required?
- Who is the designated reviewer/approver?
- What happens when the agent is uncertain? (It should ask, not guess.)

**Auditability:**
- How will you log every agent action?
- How will you trace a production incident back to an agent-made change if necessary?
- What retention policy applies to agent action logs?

**Failure modes and incident response:**
- What are the three most likely failure modes of your chosen agent in this environment?
- What is the remediation plan for each?
- Under what conditions would you disable the agent entirely?

**Policy and acceptable use:**
- What tasks is the agent explicitly *not* allowed to do? (e.g., merge to main, delete resources, access production databases.)
- How do you enforce these prohibitions technically (not just by policy)?

**5. Conclusion (0.5 page)**
- Key recommendation: which agent (or combination) would you deploy, and what is the first 90-day goal?

---

### Grading Rubric

| Section | Weight | What earns full marks |
|---|---|---|
| Technical comparison | 25% | Both agents covered thoroughly; comparison is fair and evidence-based; not just marketing claims |
| Integration plan | 25% | Realistic, phased, with concrete tooling choices and measurable success criteria |
| Governance — permissions | 15% | Specific, not vague; least privilege actually enforced; credential rotation addressed |
| Governance — oversight & auditability | 20% | Oversight levels clearly defined per action type; audit logging is concrete, not aspirational |
| Governance — failure modes | 10% | Three realistic failure modes with specific mitigations |
| Clarity and writing | 5% | Well-organized, clear, professional |

**Length:** 6–10 pages, excluding appendices. Quality over quantity.

**AI tool use:** You are encouraged to use AI assistants in preparing this assignment. If you do, you must include a one-paragraph disclosure noting which tools you used, what you used them for, and how you verified and edited their output. Undisclosed use is an academic integrity violation.
