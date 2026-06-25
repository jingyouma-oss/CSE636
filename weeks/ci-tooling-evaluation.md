# CI Tooling for Class Demos — GitHub Actions vs. Jenkins

> Planning note (instructor-facing, not student-facing). Evaluates whether to use
> **GitHub Actions** for the live CI/CD demos in CSE636. Companion to
> [README.md](README.md); references the runnable starters under `project/`.

## TL;DR

Use **GitHub Actions as the default demo runner**, keep **Jenkins as the Week 2
orchestrator deep-dive**, and frame the two explicitly as *managed vs.
self-hosted CI*. The course is ~80% there already; Actions is woven through
Weeks 0, 3, and 7 and is the lower-friction path for a live class.

## Why Actions for *demos* specifically

- **Zero setup.** Jenkins needs `docker build`, `docker compose up`, a volume,
  port 8080, and fetching the initial admin password. Actions needs a `git push`.
  In a 90–120 min session that difference is decisive.
- **Codespaces-native.** Week 0 already recommends Codespaces; Actions runs in
  the same GitHub surface — no local Docker daemon required.
- **Free tier covers it.** Public repos get unlimited minutes; the starter CI
  runs in under a minute.
- **Built-in approval gates.** Actions `environments` + Required reviewers give
  the human-in-the-loop gate the course leans on (Week 3 build-fixer, Week 7 OPA)
  natively — no plugin, no Jenkins `input` step.

## Why Jenkins stays

- **Week 2** is partly *about* the orchestrator itself (controller/agent model,
  an MCP server wrapping build status). That "how a CI server works" lesson
  Actions hides.
- **Industry reality.** Many students will hit Jenkins at work. Teaching the
  contrast (self-hosted server vs. managed YAML runners) is itself valuable.

## Current state by week

| Week | CI in the lab | Actions? |
|---|---|---|
| 0 | `project/starter/.github/workflows/ci.yml` — pytest on push/PR | ✅ primary |
| 2 | Jenkins-in-Docker + MCP build-status server | Jenkins (now also an Actions MCP variant — see below) |
| 3 | Build-fixer agent behind an approval gate | ✅ Option A (Jenkins is Option B) |
| 7 | Conftest/OPA gate in CI | ✅ applicable (Jenkins or Actions) |
| 1, 4, 5, 6 | No hands-on CI (concepts / ML / observability / incident response) | — |

## Gaps found, and what was done

1. **Week 3 build-fixer was described but not shipped.** → Built
   [`project/build-fixer/`](../project/build-fixer/): runnable buggy app, the
   GitHub Actions workflow, a unit-tested log-parser core, and the agent with a
   local dry-run mode (`make demo`, Anthropic key only) plus a `--open-pr` CI
   mode behind the `agent-proposed` approval gate. Also fixed the lab/notes
   snippets (stale `claude-opus-4-5` → `claude-opus-4-8`; fragile "ask for JSON
   in text" → structured outputs).
2. **Week 2 was Jenkins-only.** → Added a parallel **GitHub Actions MCP server**
   ([`project/build-fixer/mcp_servers/actions_status.py`](../project/build-fixer/mcp_servers/actions_status.py))
   and an "Option B — GitHub Actions" section in the Week 2 lab, so students can
   contrast a managed-CI build-status tool against the Jenkins one (and see the
   least-privilege win: one-repo `actions:read` token vs. an admin token).
3. **The starter's `ci.yml` lives under `project/starter/.github/`** so it only
   triggers when the starter becomes a repo root — Week 0 already explains this;
   no change needed.

## Open follow-ups (optional)

- A Week 7 Actions workflow that runs `conftest` against the `project/iac` plan,
  as a copy-paste demo (currently described, runs locally via `make policy`).
- Decide whether Week 2's MCP-build-status lab should *default* to Actions or
  keep Jenkins as the default with Actions as the variant (current choice).

## Recommendation

Adopt Actions as the standard demo runner across Weeks 0, 3, (4), 7; keep
Jenkins as the Week 2 orchestrator deep-dive; present them as managed vs.
self-hosted CI. That strengthens the course rather than duplicating content.
