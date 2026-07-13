# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Course materials for **CSE636 DevOps with AI**. The bulk of the repo is non-code content:

- `slides/` — lecture decks (`.key`, `.pptx`, `.pdf`) on Git, Docker, Jenkins, Kubernetes, OpenTelemetry, monitoring, AI automation
- `syllabus/`, `homework/`, `class materials/` — `.pdf` / `.pages` documents and cheat sheets

The classroom-ready **teaching notes and labs** live in `weeks/` (Week 0–7, two files per week: `week-NN-notes.md` + `week-NN-lab.md`). See `weeks/README.md` for the course arc, the file conventions, and the "gold-standard week" patterns (linked `.svg` diagrams, `<details>` "Check your understanding" collapsibles, and the learning-path nav strip). `weeks/GROUP_PROJECT_GUIDE.md` consolidates the capstone and exam scope.

Executable code lives under `project/`:

- `project/Jenkins/` — Jenkins-in-Docker teaching setup (details below).
- `project/starter/` — Week 0 on-ramp: a tiny Flask service with tests, Docker, and CI.
- `project/build-fixer/` — Week 3: an agentic CI demo. A buggy `src/calculator.py` makes the build red; `scripts/build_fixer_agent.py` reads the pytest log, asks Claude for the minimal fix, and (in CI) opens a PR behind a human approval gate (`agent-proposed` GitHub environment). Pure log-parser in `scripts/logparse.py` is unit-tested (`make test`, no deps); the agent driver needs `anthropic` (+ `PyGithub` for `--open-pr`). `make demo` dry-runs the agent locally with just `ANTHROPIC_API_KEY`. Note `make test` here covers only the pure core — the calculator tests fail *by design* (that's the demo's red build).
- `project/k8s-demo/` — A three-tier app (React/Nginx + FastAPI + Postgres) deployed to a local single-node Kubernetes (Docker Desktop or Rancher Desktop's dockerd/moby engine), one Deployment + Service per tier in a `k8s-demo` namespace; Nginx reverse-proxies `/api` to the backend, Postgres persists to a PVC. `make check/images/deploy/status/open` is the runbook; `make test` runs the backend's pure FastAPI unit tests (DB mocked, no cluster). Manifests live in `k8s/`. Pairs with Week 4's Kubernetes material.
- `project/forecasting/` — Week 4: Prophet CPU forecast → autoscaling recommendation. Pure scaling logic in `scaling.py` is unit-tested (`make test`) and needs no heavy deps; `forecast.py` (the Prophet driver) needs `make setup`.
- `project/anomaly/` — Week 5: Isolation-Forest anomaly detection scored against ground truth. Pure precision/recall/F1 in `evaluation.py` is unit-tested (`make test`); `detect.py` needs scikit-learn.
- `project/iac/` — Week 7: agent-style Terraform (`s3.tf`) gated by an OPA/Rego policy. `make policy` / `make policy-fail` run `conftest` against bundled plan JSON (works offline; only `conftest` required).

Each starter mirrors the same shape (`Makefile`, `README.md`, a pure tested core + a heavier driver). Everything else — `slides/`, `syllabus/`, `homework/`, `class materials/` — is read-only reference content with nothing to build.

## Jenkins project (`project/Jenkins/`)

A teaching setup for running Jenkins in Docker, presented in several variants. Each `Dockerfile*` is a standalone alternative, not part of one multi-stage build:

- `Dockerfile_Master` — current/preferred master image: official `jenkins/jenkins:2.571-jdk21` + Docker CLI + Blue Ocean / docker-workflow plugins + a Python 3 venv on `PATH` (owned by the `jenkins` user) with the Week 2 lab's deps (`flake8 pytest anthropic mcp requests`) **pre-installed** so `agent any` stages don't `pip install` per build — the stock image is JVM-only and fails with `pip: not found`. The opt-in CA block (below) also appends any trusted corp root into the venv's **certifi** bundle and sets `SSL_CERT_FILE`/`REQUESTS_CA_BUNDLE`, so Python (httpx/requests) trusts a TLS-inspecting proxy — the OS/JVM trust alone doesn't reach Python. This is what real pipeline work should use. Has an **opt-in** CA-trust block: `COPY certs/` then, if a cert is present, trusts it in both the OS store (curl/apt) and the JVM truststore via `keytool` (needed because `jenkins-plugin-cli` is a Java tool) — for building behind a TLS-inspecting proxy. Empty `certs/` (only `.gitkeep`) = no-op. `certs/*.pem`/`*.crt` are gitignored.
- `Dockerfile_Agent_Inbound` — the agent image: official `jenkins/inbound-agent:latest-jdk21` (self-connects to the master over a WebSocket) + the same Python venv/deps and opt-in CA block as `Dockerfile_Master`. Built as `cstu-jenkins-agent` and used by `docker-compose.agent.yml` for the Week 2 lab's distributed-build (master/agent) variant. Pipelines target it with `agent { label 'python-agent' }`. (Replaced the old non-building `Dockerfile_Agent`, an `ubuntu:16.04`/Java 8/Python 2 "slave" reference that was removed.)
- `DEMO.md` — step-by-step demonstration runbook (compose path, scripted path, first-run wizard, teardown).

`docker-compose.yml` expects a locally-built image tagged `cstu-jenkins` (it does not build from a Dockerfile itself), publishes `8080`, sets `container_name: cstu-jenkins`, and persists `/var/jenkins_home` in the `jenkins_data_cstu` volume.

`docker-compose.agent.yml` is the alternative **master + agent** topology: the `cstu-jenkins` controller plus a `cstu-jenkins-agent` inbound agent on a shared `jenkins` network, reusing the same `jenkins_data_cstu` volume. The agent needs a one-time node registration in the UI to obtain its JNLP `JENKINS_SECRET` (passed via a `.env` file); it connects over WebSocket (`JENKINS_WEB_SOCKET=true`), so no TCP agent port is published. See `weeks/week-02/week-02-lab.md` Part 1 variant B.

`automate.py` is the scripted alternative to compose: it uses the `docker` Python SDK (`docker.from_env()`) to build the `cstu-jenkins` image from `Dockerfile_Master` (passed explicitly via `dockerfile=`, so it does not fall back to the non-building default `Dockerfile`), create the volume, run the container, and print the initial admin password. Note its build tag and compose's `image:` must match (`cstu-jenkins`).

### Running it

```bash
cd project/Jenkins

# Option A — scripted (requires `pip install docker`, Docker daemon running)
python automate.py

# Option B — compose (build the image first, since compose only references it by tag)
docker build -t cstu-jenkins -f Dockerfile_Master .
docker compose up -d

# Initial admin password (either path)
docker exec cstu-jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

`run_dind.sh` / `run_jenkin_blueocean.sh` are the Docker-in-Docker lecture demo: run the `docker:dind` container first (`run_dind.sh`), then the Blue Ocean Jenkins container (`run_jenkin_blueocean.sh`). They assume a pre-created `jenkins` Docker network and host paths under `$HOME/Docker/SharedData/Jenkins/`.

## Conventions

- `cstu-jenkins` / `jenkins_data_cstu` naming ties the image, container, and volume together across `automate.py`, `docker-compose.yml`, and the shell scripts — keep them consistent when editing.
- When editing `weeks/` content, follow the patterns documented in `weeks/README.md`: diagrams are **linked `.svg` files** in each week's `images/` subfolder (GitHub strips inline SVG) with full descriptive alt text, referenced as `![alt](images/name.svg)`; interactive checks use `<details><summary>` blocks; each notes file opens with the learning-path strip + 🎯 At-a-glance and closes with a recap. Each week folder keeps its own `images/learning-path.svg` with that week highlighted.
- `.gitignore` excludes `Recording`, `Blurb.pages`, `EvaluationReport.pdf`, and standard Python build artifacts (`__pycache__/`, `*.pyc`, `.venv/`), `.env`, `.DS_Store`, and regenerable lab outputs (the starters' generated CSVs / Terraform plan files). Don't commit those.
