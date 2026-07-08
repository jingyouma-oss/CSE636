# Jenkins-in-Docker — Demonstration Runbook

A step-by-step guide to demoing **Jenkins running in a Docker container** with a
persistent volume, Docker CLI baked in, and the Blue Ocean UI. Two equivalent
paths are shown — pick one for class:

- **Path A — Docker Compose** (declarative; easiest to read)
- **Path B — Python automation** (`automate.py`, the Docker SDK)

Both build the same image (`cstu-jenkins`, from `Dockerfile_Master`), publish
port **8080**, and persist Jenkins state in the **`jenkins_data_cstu`** volume.

> **What this demonstrates:** packaging a real CI server as a container, why a
> **named volume** matters (state survives restarts), and how `Dockerfile_Master`
> bakes in the **Docker CLI + Blue Ocean / docker-workflow** plugins so pipelines
> can build containers.

---

## Prerequisites

- **Docker Desktop / Rancher Desktop running** (`docker version` succeeds).
- Port **8080** free (`lsof -i :8080` shows nothing).
- Path B only: `pip install docker` (the Docker SDK for Python).

```bash
cd project/Jenkins
docker version        # confirm the daemon is up
```

---

## Act 1 — Build the image

`Dockerfile_Master` = official `jenkins/jenkins:2.571-jdk21` + the Docker CLI +
`blueocean`, `docker-workflow`, `json-path-api` plugins.

```bash
docker build -t cstu-jenkins -f Dockerfile_Master .
docker images | grep cstu-jenkins
```

**Point out:** we tag it `cstu-jenkins` — the name Compose, `automate.py`, and
the volume all agree on. The Docker CLI is installed *inside* Jenkins so pipeline
steps can run `docker build` / `docker run`.

> The other Dockerfiles are **not** used here: `Dockerfile_Agent` is a legacy,
> non-building reference (`ubuntu:16.04` + a missing `slave.py`); `Dockerfile_1`
> is a minimal `jenkins + git/curl` variant for a bare-bones demo.

---

## Act 2 — Run Jenkins (pick ONE path)

### Path A — Docker Compose

```bash
docker compose up -d           # uses the pre-built cstu-jenkins image
docker compose ps              # STATUS should be "running"/"healthy"
```

### Path B — Python automation

```bash
python automate.py
```

`automate.py` builds the image from `Dockerfile_Master`, creates the
`jenkins_data_cstu` volume if missing, runs the container on `8080`, waits ~15s,
then **prints the initial admin password** for you.

**Point out:** Compose is declarative (one YAML, `up`/`down`); the Python script
is imperative (explicit build → volume → run → read-the-password) and shows the
Docker **SDK** doing what the CLI does.

---

## Act 3 — First-run wizard

```bash
# Compose path: fetch the unlock password (Path B already printed it)
docker exec cstu-jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

1. Open **http://localhost:8080**.
2. Paste the password to **unlock**.
3. Choose **Install suggested plugins** (or *Select plugins* — Blue Ocean is
   already baked in from the image).
4. Create the **first admin user**.
5. Land on the Jenkins dashboard.

**Point out:** the unlock secret lives *inside* the container at
`/var/jenkins_home/secrets/…` — and because that path is on the named volume, it
survives restarts (see Act 5).

---

## Act 4 — Show what the image gives you

```bash
# Docker CLI is available inside the Jenkins container (for docker-workflow pipelines)
docker exec cstu-jenkins docker --version

# Blue Ocean UI (modern pipeline visualization)
open http://localhost:8080/blue
```

**Point out:** a container that can itself run `docker` is what lets a Jenkins
pipeline build and push images. Blue Ocean visualizes pipeline stages.

*(Optional)* Create a trivial **Pipeline** job with this script to prove it end
to end:

```groovy
pipeline {
  agent any
  stages {
    stage('Hello')  { steps { echo 'Hello from Jenkins in Docker' } }
    stage('Docker') { steps { sh 'docker --version' } }
  }
}
```

---

## Act 5 — Persistence (why the named volume matters)

```bash
docker inspect -f '{{ range .Mounts }}{{ .Name }} -> {{ .Destination }}{{ end }}' cstu-jenkins
# jenkins_data_cstu -> /var/jenkins_home

# Restart the container; your admin user + jobs are still there
docker compose restart        # (Path A)   — or:   docker restart cstu-jenkins   (Path B)
```

Reload **http://localhost:8080** — you're still logged in, jobs intact.

**Point out:** the container is disposable; **`jenkins_data_cstu`** holds all of
Jenkins' state (`/var/jenkins_home`). Delete the container and recreate it — the
volume re-attaches and nothing is lost.

---

## Teardown

```bash
# Path A (Compose): stop + remove container, KEEP the volume
docker compose down
# Path A: also delete the persisted data
docker compose down -v

# Path B (script): remove container + volume manually
docker rm -f cstu-jenkins
docker volume rm jenkins_data_cstu
```

**Point out:** `down` (no `-v`) removes the container but **keeps** the volume —
next `up` resumes exactly where you left off. `down -v` is the clean slate.

---

## Advanced (optional) — Docker-in-Docker + Blue Ocean

`run_dind.sh` + `run_jenkin_blueocean.sh` are the classic DinD lecture demo: a
privileged `docker:dind` container provides a Docker daemon, and Jenkins talks to
it over TLS. Prerequisites:

```bash
docker network create jenkins                 # the scripts assume this network exists
mkdir -p "$HOME/Docker/SharedData/Jenkins/Jenkins_Home" \
         "$HOME/Docker/SharedData/Jenkins/Docker-certs"
docker build -t cstu-jenkins -f Dockerfile_Master .   # the blueocean script runs this image

./run_dind.sh                 # 1) start the Docker-in-Docker daemon
./run_jenkin_blueocean.sh     # 2) start Jenkins wired to that daemon
```

**Point out:** DinD gives the pipeline its *own* Docker daemon (isolation) rather
than mounting the host's socket. It's heavier than Acts 1–5 — use it only if the
class is specifically about agent/daemon isolation.

---

## Troubleshooting

- **Build fails with `CERTIFICATE_VERIFY_FAILED` / `unable to get local issuer
  certificate` (`curl: (60)`):** you're behind a TLS-inspecting proxy (e.g.
  Zscaler). The build's `curl`/`apt` (docker-ce-cli) and `jenkins-plugin-cli`
  (plugin downloads) don't trust the proxy's root CA. `Dockerfile_Master` has an
  **opt-in** fix: drop the proxy root CA into `certs/` and rebuild — the
  Dockerfile then trusts it in **both** the OS store (curl/apt) and the **JVM
  truststore** (the plugin installer is a Java tool). On macOS:

  ```bash
  # export your proxy's root CA (adjust the name for your proxy)
  security find-certificate -a -c "Zscaler Root CA" -p \
    /Library/Keychains/System.keychain > certs/corp-ca.pem
  docker build -t cstu-jenkins -f Dockerfile_Master .   # now trusts the CA
  ```

  `certs/*.pem` is gitignored. With `certs/` empty (only `.gitkeep`), the CA
  block is a **no-op**, so the image still builds normally on an open network.
- **Port 8080 in use:** change the left side of the port mapping (Compose:
  `"8081:8080"`; `automate.py`: the `ports={"8080/tcp": 8081}` entry).
- **`docker: command not found` inside the container:** you built the wrong
  image — rebuild with `-f Dockerfile_Master` (only that one installs the CLI).
- **Lost the unlock password:** `docker exec cstu-jenkins cat /var/jenkins_home/secrets/initialAdminPassword`.
```
