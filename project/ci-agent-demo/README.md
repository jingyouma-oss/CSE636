# CI/CD Agent-in-the-Loop Demo — Week 3

Claude Code, given [`REQUIREMENTS.md`](REQUIREMENTS.md), operates **local
Jenkins** through MCP tools to: create a pipeline, produce a red build, diagnose
it, apply a **human-approved** fix, and verify the build goes green — then write
a report to [`reports/`](reports/).

This is the Claude-Code-native companion to [`../build-fixer/`](../build-fixer/)
(which uses a hand-written SDK script + a Jenkins `input` gate). Here the agent
*operates* the CI system through a tool interface, with the human approving the
one change that matters.

## Layout

| Path | What it is |
|---|---|
| `REQUIREMENTS.md` | The spec Claude Code reads to run the loop |
| `app/pricing.py` | Tiny app with a planted bug (`item_total` adds instead of multiplies) |
| `app/test_pricing.py` | 2 tests — 1 fails by design, 1 passes |
| `reports/` | Claude Code writes `run-NN.md` here |

## Run it

See the instructor runbook: [`weeks/week-03/week-03-demo.md`](../../weeks/week-03/week-03-demo.md).
The Jenkins MCP server it uses is
[`../build-fixer/mcp_servers/jenkins_status.py`](../build-fixer/mcp_servers/jenkins_status.py).

## Reset (re-arm the demo)

After a run, `main` holds the fixed code. To re-arm the bug for another run,
restore the buggy line and push:

```bash
cd project/ci-agent-demo/app
python3 -c "import pathlib,re; p=pathlib.Path('pricing.py'); \
p.write_text(p.read_text().replace('return price * quantity','return price + quantity  # BUG: should be price * quantity'))"
python3 -m pytest -q          # expect: 1 failed, 1 passed
git commit -am "chore(ci-agent-demo): re-arm planted bug" && git push origin main
```

This is also the "prove it's real" check: revert the fix, re-run the pipeline,
and watch it go red again.
