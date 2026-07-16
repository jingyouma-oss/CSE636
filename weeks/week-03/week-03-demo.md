# Week 3 — Class Demo: Claude Code as the CI/CD Agent in the Loop

![Course learning path with Week 3 (CI/CD) highlighted: 0 Setup, 1 Basics, 2 Tooling, 3 CI/CD, 4 Predict, 5 Observe, 6 Respond, 7 Govern.](images/learning-path.svg)

> 📎 **Supplementary demo for Week 3.** The lecture notes are in
> [week-03-notes.md](week-03-notes.md) and the graded lab in
> [week-03-lab.md](week-03-lab.md). This runbook is a **live instructor demo**:
> Claude Code operates local Jenkins through MCP tools to run a full red→green
> CI/CD loop with a human approval gate.

> 🎯 **At a glance**
>
> | | |
> |---|---|
> | **Prerequisites** | Week 2 Jenkins (`cstu-jenkins`) + the Jenkins MCP server registered in Claude Code |
> | **Time budget** | ~10 min live |
> | **What the class sees** | An agent create a pipeline, hit a red build, diagnose it, ask permission, fix it, and prove it green |
> | **Ties into** | [`project/ci-agent-demo/`](../../project/ci-agent-demo/) and [`jenkins_status.py`](../../project/build-fixer/mcp_servers/jenkins_status.py) |

---

## What the class will see

Claude Code, handed [`REQUIREMENTS.md`](../../project/ci-agent-demo/REQUIREMENTS.md),
drives the whole CI/CD lifecycle against local Jenkins **through MCP tools**:

1. Generates a `Jenkinsfile` and **creates** the pipeline job.
2. **Triggers** build #1 → it goes **red** (the app has a planted bug).
3. Reads the **console log**, diagnoses the failing test.
4. Proposes a minimal fix and **pauses for your approval**. 🚦
5. On approval, pushes the fix and re-runs → **green**.
6. Writes a summary report.

The teaching point: the agent *operates* CI/CD the way an engineer would, but
you keep control at the one decision that matters.

---

## Part A — Setup (once, before class)

**A1. Jenkins up.** Confirm `cstu-jenkins` runs at http://localhost:8080
(Week 2). `docker ps` should list it.

**A2. Jenkins API token.** Manage Jenkins → Users → *your user* → Security →
API Token → Add new token. Put credentials in `project/build-fixer/.env`
(gitignored):

```
JENKINS_URL=http://localhost:8080
JENKINS_USER=<user>
JENKINS_TOKEN=<token>
```

**A3. Register the MCP server** in `~/.claude/claude.json` (absolute path):

```json
{
  "mcpServers": {
    "cse636-jenkins": {
      "command": "python",
      "args": ["/absolute/path/to/project/build-fixer/mcp_servers/jenkins_status.py"],
      "env": {
        "JENKINS_URL": "http://localhost:8080",
        "JENKINS_USER": "<user>",
        "JENKINS_TOKEN": "<token>"
      }
    }
  }
}
```

**A4. Smoke-test the MCP write tools** (creates + builds a throwaway job):

```bash
cd project/build-fixer
MCP_WRITE_TEST=1 .venv/bin/python mcp_servers/test_jenkins_status.py
```

Expect `Job 'mcp-selftest' created.`, a `SUCCESS` status, and
`contains 'hello-from-mcp': True`. Delete `mcp-selftest` in the UI afterward.

**A5. Demo project on `main`.** Ensure `project/ci-agent-demo/` (with the
planted bug) is committed and pushed to the class GitHub repo's `main`, and that
you have local `git push` rights (a PAT via your git credential helper). Edit
the repo URL in `REQUIREMENTS.md`'s pipeline contract to your class repo.

**A6. Confirm the bug is armed:**
`cd project/ci-agent-demo/app && python3 -m pytest -q` → `1 failed, 1 passed`.

---

## Part B — Run it live

**B1. Kick off Claude Code** in the repo root:

```
Read project/ci-agent-demo/REQUIREMENTS.md and run the CI/CD agent loop.
Use only the Jenkins MCP tools. Stop and ask me to approve before you apply
any fix.
```

**B2. Narrate as it works:**

- It authors a `Jenkinsfile` and calls `create_job` → point out *no UI clicks*.
- It calls `trigger_build`, then `get_build_status` a few times → the build is red.
- It calls `get_build_log` and reads the pytest failure.

**B3. The approval gate.** 🚦 Claude Code shows the one-line diff
(`price + quantity` → `price * quantity`) and stops. This is the moment: ask
the class *"should we let it push?"* Then approve.

**B4. Green.** Claude Code pushes to `main`, re-triggers, polls to `SUCCESS`,
and writes `project/ci-agent-demo/reports/run-NN.md`. Open the report.

**B5. Prove it's real.** Run the reset from the
[demo README](../../project/ci-agent-demo/README.md#reset-re-arm-the-demo),
re-trigger, and watch the build go red again — proof the agent was operating
live infrastructure, not narrating.

<details><summary>✅ Did it work? What "success" looks like</summary>

- A `ci-agent-demo` job exists that you never created by hand.
- Build #1 = red, build #2 = green, both visible in the Jenkins UI.
- The fix was pushed **only after** you approved it.
- The report names the failing test, the root cause, and the exact fix.

If Claude Code answers without calling tools, re-check A3 (absolute path) and
A4. If `create_job`/`trigger_build` error, re-check the API token (A2) and that
Jenkins is up (A1).

</details>

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Jenkins API error 403` on create/trigger | CSRF crumb / token issue — re-check A2; the MCP server fetches a crumb automatically |
| Build stays `IN_PROGRESS` forever | No executor free, or a syntax error in the generated Jenkinsfile — open the job's console in the UI |
| Checkout fails in the build | Repo URL wrong in `REQUIREMENTS.md`, or a private repo needs a `github-https` credential |
| `git push` rejected | Local PAT missing/expired; the fix only lands once push succeeds |

---

## Recap

- An agent can *operate* CI/CD, not just write code — creating jobs, triggering
  builds, and reading logs through a small MCP tool surface.
- The **human approval gate** is what makes this safe: the blast radius of an
  autonomous agent is bounded by where you require a human "yes."
- Everything ran on **local Jenkins**, mount-free, with the fix delivered by an
  ordinary `git push`.

➡️ Next: [Week 4 — Predict](../week-04/week-04-notes.md).
