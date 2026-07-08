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

This builds the image defined in `Dockerfile_Master` — Jenkins 2.571 on JDK 21, with Docker CLI and Blue Ocean plugins. It takes a few minutes the first time.

**Step 3: Start Jenkins.**

```bash
docker compose up -d
```

**Step 4: Get the initial admin password and complete setup.**

```bash
docker exec cstu-jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Open `http://localhost:8080` in your browser, enter the password, install suggested plugins, and create your admin user.

**Step 5: Create a sample pipeline job.**

In Jenkins, create a new Pipeline job named `ai-review-demo`. Use this starter `Jenkinsfile`:

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
            steps {
                sh 'pip install flake8 && flake8 . --max-line-length=120 || true'
            }
        }

        stage('Test') {
            steps {
                sh 'pip install pytest && pytest tests/ -v'
            }
        }

        stage('AI Code Review') {
            steps {
                withCredentials([string(credentialsId: 'ANTHROPIC_API_KEY',
                                        variable: 'ANTHROPIC_API_KEY')]) {
                    sh '''
                        pip install anthropic
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

**Step 6: Create the AI review script.**

Create `scripts/ai_review.py` in your sample repo:

```python
#!/usr/bin/env python3
"""
AI code review step for the CSE636 Week 2 lab.
Reads recently changed Python files and asks Claude for a code review.
"""
import os
import subprocess
import anthropic

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def get_changed_files():
    """Get Python files changed in the last commit."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
        capture_output=True, text=True
    )
    return [f for f in result.stdout.strip().split("\n") if f.endswith(".py")]

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
        print("No Python files changed. Skipping AI review.")
        with open("ai_review_report.txt", "w") as fh:
            fh.write("No Python files changed in this commit.\n")
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

**Step 7: Add your API key to Jenkins credentials.**

In Jenkins: Manage Jenkins → Credentials → (global) → Add Credentials → Secret text. Set the ID to `ANTHROPIC_API_KEY` and paste your key.

**Step 8: Trigger a build and verify the AI review report is generated.**

Push a small change to your sample repo. Trigger the pipeline. Check the build artifacts for `ai_review_report.txt`.

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
