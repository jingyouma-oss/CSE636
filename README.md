# CSE636 — DevOps with AI

## What this repository is

Course materials for **CSE636 DevOps with AI**, a 7-week (Week 0–7) course on integrating AI agents into DevOps, written for students with no prior DevOps or AI background.

- `weeks/` — **the classroom-ready teaching notes and labs** (two files per week: `week-NN-notes.md` lecture notes + `week-NN-lab.md` hands-on lab), plus SVG diagrams, a learning-path nav strip, and interactive "Check your understanding" checkpoints. Start at [`weeks/README.md`](weeks/README.md) for the course arc and conventions, and [`weeks/GROUP_PROJECT_GUIDE.md`](weeks/GROUP_PROJECT_GUIDE.md) for the capstone + exam scope.
- `slides/` — lecture decks (`.md`, `.key`, `.pptx`, `.pdf`) on Git, Docker, Jenkins, Kubernetes, OpenTelemetry, monitoring, AI automation
- `syllabus/`, `homework/`, `class materials/` — `.pdf` / `.pages` documents and cheat sheets

## Runnable code (`project/`)

Each lab has a small, self-contained starter you can run. They share one shape — a `Makefile`, a `README.md`, a pure/unit-tested core, and a heavier driver — so the tested logic runs with no heavy dependencies.

| Folder | Week | What it is | Quick start |
|---|---|---|---|
| [`project/starter/`](project/starter/) | 0 | Tiny Flask service with tests, Docker, and CI | `make setup && make test && make run` |
| [`project/Jenkins/`](project/Jenkins/) | 2–3 | Jenkins-in-Docker teaching setup (see below) | `docker build -t cstu-jenkins -f Dockerfile_Master .` |
| [`project/forecasting/`](project/forecasting/) | 4 | Prophet CPU forecast → autoscaling recommendation | `make data && make forecast` · `make test` (no Prophet needed) |
| [`project/anomaly/`](project/anomaly/) | 5 | Isolation-Forest anomaly detection vs. ground truth | `make data && make detect` · `make test` (no sklearn needed) |
| [`project/iac/`](project/iac/) | 7 | Agent-style Terraform gated by an OPA/Rego policy | `make policy` (pass) · `make policy-fail` (blocked) — only `conftest` required |

Everything outside `project/` and `weeks/` is read-only reference content.

## Jenkins project (`project/Jenkins/`)

A teaching setup for running Jenkins in Docker, presented in several variants. Each `Dockerfile*` is a standalone alternative, not part of one multi-stage build:

- `Dockerfile_Master` — current/preferred master image: official `jenkins/jenkins:2.571-jdk21` + Docker CLI + Blue Ocean / docker-workflow plugins. This is what real pipeline work should use. Behind a TLS-inspecting proxy, drop the proxy root CA into `certs/corp-ca.pem` (gitignored) and it's trusted at build time in both the OS store and the JVM truststore; empty `certs/` = no-op. See `DEMO.md`.
- `Dockerfile_Agent` — legacy agent ("slave") image on `ubuntu:16.04` (an EOL base). It `ADD slave.py`, which is **not present in the repo**, so it will not build as-is — kept only as a historical/lecture reference.
- `Dockerfile_1` — minimal `jenkins/jenkins:latest` + git/curl, used for simple demos.

See [`project/Jenkins/DEMO.md`](project/Jenkins/DEMO.md) for a step-by-step demonstration runbook.

`docker-compose.yml` expects a locally-built image tagged `cstu-jenkins` (it does not build from a Dockerfile itself), publishes `8080`, and persists `/var/jenkins_home` in the `jenkins_data_cstu` volume.

`automate.py` is the scripted alternative to compose: it uses the `docker` Python SDK (`docker.from_env()`) to build the `cstu-jenkins` image from `Dockerfile_Master`, create the volume, run the container, and print the initial admin password. Note its build tag and compose's `image:` must match (`cstu-jenkins`).

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
- `weeks/` content follows a documented house style (linked SVG diagrams, `<details>` checkpoints, per-week learning-path strip) — see [`weeks/README.md`](weeks/README.md) before editing.
- `.gitignore` excludes `Recording`, `Blurb.pages`, `EvaluationReport.pdf`, plus Python build artifacts (`__pycache__/`, `*.pyc`, `.venv/`), `.env`, `.DS_Store`, and the starters' regenerable outputs.
