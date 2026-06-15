# CSE636 Starter Service

A tiny, runnable web service used as the **Week 0 on-ramp** for *CSE636 DevOps with AI*.
It is deliberately small so that students new to DevOps can exercise the entire
loop — **edit code → run tests → start the app → build a container → watch CI pass** —
without getting lost, and so that AI coding agents have a concrete repository to
act on in the Week 1+ labs.

> New to all of this? Follow the guided walkthrough in
> [`../../weeks/week-00/week-00-lab.md`](../../weeks/week-00/week-00-lab.md).
> It explains every command below from scratch.

## What's inside

```
starter/
  app/
    main.py            # Flask app + a pure deployment_risk_score() function
  tests/
    test_main.py       # pytest tests for the function and the endpoints
  .devcontainer/       # one-click identical environment (Codespaces / VS Code)
  .github/workflows/   # CI: runs the tests on every push / pull request
  Dockerfile           # builds the app into a container image
  Makefile             # make setup / test / run / docker-build / docker-run
  requirements.txt     # Flask + pytest
```

## Quick start

You need **Python 3.12+**. Docker is optional (only for the container steps).

```bash
make setup        # create a virtualenv and install dependencies
make test         # run the tests — they should all pass
make run          # start the app at http://localhost:8000
```

Then, in another terminal:

```bash
curl http://localhost:8000/health
curl "http://localhost:8000/risk?files_changed=3&lines_changed=120&tests_passing=true"
```

### Run it in a container

```bash
make docker-build
make docker-run    # serves at http://localhost:8000
```

### No local setup? Use a Dev Container

Open this folder in **GitHub Codespaces** (or VS Code → *Reopen in Container*).
Python, Docker, and dependencies are configured automatically — see
[`.devcontainer/devcontainer.json`](.devcontainer/devcontainer.json).

## The endpoints

| Method | Path | What it does |
|---|---|---|
| GET | `/` | Welcome message and example links |
| GET | `/health` | Returns `{"status":"ok"}` — used by health checks (Week 6) |
| GET | `/risk?files_changed=&lines_changed=&tests_passing=` | Returns a toy deployment-risk score (Week 4 covers the real thing) |

## Where this goes in the course

- **Week 0** — get the toolchain working; run this repo end to end.
- **Week 1** — point an AI coding agent at this repo (summarize it, find issues, add a workflow).
- **Week 3** — have an agent generate more tests and fix a deliberately broken build.
- Later weeks reuse it as a small service to monitor, scale, and deploy.
