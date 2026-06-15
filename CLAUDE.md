# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Course materials for **CSE636 DevOps with AI**. The bulk of the repo is non-code content:

- `slides/` — lecture decks (`.key`, `.pptx`, `.pdf`) on Git, Docker, Jenkins, Kubernetes, OpenTelemetry, monitoring, AI automation
- `syllabus/`, `homework/`, `class materials/` — `.pdf` / `.pages` documents and cheat sheets

Executable code lives in `project/Jenkins/` (Jenkins-in-Docker teaching setup) and `project/starter/` (the Week 0 beginner on-ramp — a tiny Flask service with tests, Docker, and CI). Treat everything else as read-only reference content — there is nothing to build, lint, or test outside those folders.

## Jenkins project (`project/Jenkins/`)

A teaching setup for running Jenkins in Docker, presented in several variants. Each `Dockerfile*` is a standalone alternative, not part of one multi-stage build:

- `Dockerfile_Master` — current/preferred master image: official `jenkins/jenkins:2.528-jdk21` + Docker CLI + Blue Ocean / docker-workflow plugins. This is what real pipeline work should use.
- `Dockerfile` and `Dockerfile_Agent` — identical legacy agent ("slave") images on `ubuntu:16.04`. Both `ADD slave.py`, which is **not present in the repo** — these will not build as-is and are kept for historical/lecture reference.
- `Dockerfile_1` — minimal `jenkins/jenkins:latest` + git/curl, used for simple demos.

`docker-compose.yml` expects a locally-built image tagged `cstu-jenkins` (it does not build from a Dockerfile itself), publishes `8080`, and persists `/var/jenkins_home` in the `jenkins_data_cstu` volume.

`automate.py` is the scripted alternative to compose: it uses the `docker` Python SDK (`docker.from_env()`) to build the `cstu-jenkins` image from the current directory, create the volume, run the container, and print the initial admin password. Note its build tag and compose's `image:` must match (`cstu-jenkins`).

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
- `.gitignore` excludes `Recording`, `Blurb.pages`, and `EvaluationReport.pdf` — these are intentionally kept out of the repo.
