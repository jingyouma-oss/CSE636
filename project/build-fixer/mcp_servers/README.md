# MCP servers — CI build status

Two minimal [MCP](https://modelcontextprotocol.io) servers for the CSE636 Week 2
lab (Part 2). Each exposes "is my build green?" tools to an AI agent (Claude
Code) over stdio. They are intentionally **parallel** — same concept, two CI
backends — so you can see that MCP is CI-agnostic:

| Server | Backend | Tools | Auth scope |
|---|---|---|---|
| [`jenkins_status.py`](jenkins_status.py) | Local Jenkins REST API (`cstu-jenkins` on `http://localhost:8080`) | `list_jobs`, `get_build_status` | Jenkins user + API token |
| [`actions_status.py`](actions_status.py) | GitHub Actions REST API | `list_workflows`, `get_run_status` | GitHub PAT, `actions:read` on one repo |

Each server has a companion **test client** that spawns it over stdio, performs
the MCP handshake, and calls both tools — so you can verify end-to-end without
registering it in `claude.json`:

- [`test_jenkins_status.py`](test_jenkins_status.py)
- [`test_actions_status.py`](test_actions_status.py)

## Install

```bash
pip install mcp requests            # or: use project/build-fixer/.venv (make setup)
```

## Jenkins server

Needs a running Jenkins and a user + API token
(Manage Jenkins → Users → *your user* → Security → API Token → Add new token).

```bash
# Run standalone — blocks on stdin waiting for MCP JSON-RPC (Ctrl-C to exit).
# This only confirms it launches without import errors.
JENKINS_URL=http://localhost:8080 JENKINS_USER=admin JENKINS_TOKEN=<token> \
  python jenkins_status.py

# Verify end-to-end (recommended): spawn + handshake + call both tools.
# Auto-loads JENKINS_* / JOB from project/build-fixer/.env if present.
JENKINS_URL=http://localhost:8080 JENKINS_USER=admin JENKINS_TOKEN=<token> \
  python test_jenkins_status.py
```

Expected:

```
Tools advertised: get_build_status, list_jobs

--- list_jobs ---
Jenkins jobs: ai-review-demo, ...

--- get_build_status (job=ai-review-demo) ---
Job 'ai-review-demo': build #24 — SUCCESS
```

Env: `JENKINS_URL`, `JENKINS_USER`, `JENKINS_TOKEN` (and `JOB` for the test
client, default `ai-review-demo`).

## GitHub Actions server

Needs a token with `actions:read` (a fine-grained PAT scoped to one repo is
ideal — least privilege) and `REPO` as `owner/name`.

```bash
GH_TOKEN=<token> REPO=<owner>/<repo> python actions_status.py           # standalone
GH_TOKEN=<token> REPO=<owner>/<repo> python test_actions_status.py      # end-to-end
# optional branch filter for get_run_status:
GH_TOKEN=<token> REPO=<owner>/<repo> BRANCH=main python test_actions_status.py
```

Env: `GH_TOKEN`, `REPO` (and `BRANCH` for the test client).

## Register with Claude Code

Add to `~/.claude/claude.json` (use an **absolute** path to the server):

```json
{
  "mcpServers": {
    "cse636-jenkins": {
      "command": "python",
      "args": ["/absolute/path/to/project/build-fixer/mcp_servers/jenkins_status.py"],
      "env": {
        "JENKINS_URL": "http://localhost:8080",
        "JENKINS_USER": "admin",
        "JENKINS_TOKEN": "your-token-here"
      }
    }
  }
}
```

Then: `claude "List all Jenkins jobs and tell me the status of the ai-review-demo job."`
A real tool call reports **live** state (actual job names + build number/result),
not a plausible guess. Sanity check: stop Jenkins and ask again — the call now
fails/empties, proving the agent queried live infrastructure.

## Notes

- **Entry point.** `stdio_server()` takes no arguments and yields a
  `(read, write)` stream pair; drive the server with
  `await app.run(read, write, app.create_initialization_options())`.
  `asyncio.run(stdio_server(app))` does **not** work — `stdio_server` is an
  async *context manager*, not a coroutine.
- **The test clients use `sys.executable`**, so the server subprocess runs under
  the same interpreter/venv where you installed `mcp` — no path mismatch.
- **Behind a TLS-inspecting proxy** (e.g. Zscaler), the GitHub server may hit
  `CERTIFICATE_VERIFY_FAILED` reaching `api.github.com`. The Jenkins server
  talks to `localhost` over plain HTTP and is unaffected. See the Week 2 lab's
  CA-trust note for the fix.
