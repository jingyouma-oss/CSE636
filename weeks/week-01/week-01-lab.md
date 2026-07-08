# Week 1 — Lab & Assignment

> 🧪 **Hands-on work for Week 1.** For the lecture notes, foundations primer, discussion questions, and references, see **[week-01-notes.md](week-01-notes.md)**.

---

## 🧪 Lab: Week 1

**Title:** Cloud DevOps Lab Setup and First AI Agent Run

**Time budget:** ~3 hours (can be spread across the week as take-home work)

**Goal:** Have a working cloud lab environment and have successfully run an AI coding agent against a real repository — so you arrive at Week 2 with hands-on context for the tool comparison discussion.

> 🎯 **At a glance**
>
> | | |
> |---|---|
> | **You'll need** | A cloud free-tier account (or local Docker / Codespaces), an AI agent (Claude Code or Copilot), an Anthropic API key |
> | **You'll produce** | A running lab VM, observations from 4 agent tasks, and saved `ci-build-log.txt` + `system-metrics.txt` (reused in later weeks) |
> | **Submit** | A 1–2 page lab report (Step 6) **and** the assignment below |
> | **Ties to notes** | Watch the agent run the [perceive → plan → act → observe loop](week-01-notes.md#13-anatomy-of-an-ai-agent) live |

---

### Step 1: Set up a cloud-based DevOps lab account

You will need a cloud account with compute resources. All three major providers offer free tiers suitable for this course:

| Provider | Free tier highlights | Best if you already have... |
|---|---|---|
| AWS | 750 hrs/month of t2.micro EC2 for 12 months | AWS experience, US-based |
| Azure | $200 credit for 30 days; some services always free | Microsoft / Office 365 ecosystem |
| GCP | $300 credit for 90 days; always-free Compute Engine | Google Workspace, Kubernetes interest |

**Instructions (AWS example — adjust for your chosen provider):**

```bash
# 1. Create a free-tier AWS account at https://aws.amazon.com/free/
#    You will need a credit card but will not be charged within free tier limits.

# 2. Create an EC2 instance:
#    - AMI: Ubuntu 24.04 LTS
#    - Instance type: t2.micro (free tier eligible)
#    - Storage: 20 GB gp3
#    - Security group: allow SSH (port 22) from your IP only

# 3. SSH into the instance:
ssh -i your-key.pem ubuntu@<your-ec2-public-ip>

# 4. Install basic DevOps tools:
sudo apt-get update && sudo apt-get install -y \
  git curl docker.io python3 python3-pip jq

sudo systemctl start docker
sudo usermod -aG docker $USER
# Log out and back in for group membership to take effect.

# 5. Verify:
git --version
docker --version
python3 --version
```

> **Note:** If setting up a full cloud VM is not possible in the first week, you can use Docker Desktop on your local machine or a free cloud IDE (GitHub Codespaces, Gitpod, Replit) as a substitute. The key is having a Git-enabled environment where you can run shell commands. **Step 1b below walks through the local Docker path end-to-end** — pick either track, then continue with Step 2.

---

### Step 1b (Alternative): Set up a local Docker-based lab environment

No cloud account, no credit card, no free-tier clock ticking. This track gives you the same Git-enabled Linux shell as the EC2 path, but running as a container on your own laptop. **Do this instead of Step 1 if you prefer to work locally** — everything from Step 2 onward is identical.

**Why a container instead of just your host machine?** Working inside a disposable Ubuntu container keeps the lab reproducible (everyone has the same OS and tools), keeps your host clean, and mirrors how DevOps work actually happens — inside images, not on pets. You can `exit` and `docker rm` to reset to a clean slate at any time.

**Prerequisites:**

| Tool | Install | Verify |
|---|---|---|
| Docker Desktop | https://www.docker.com/products/docker-desktop/ (macOS/Windows) | `docker --version` |
| — or Rancher Desktop | https://rancherdesktop.io (free, open-source; pick the `dockerd`/moby engine) | `docker --version` |

> Rancher Desktop is a drop-in, no-license alternative to Docker Desktop and is what the course's `project/Jenkins` and `project/k8s-demo` setups are validated against. Either works for this lab.

There are two ways to do this. **Option A** builds a reusable image from a `Dockerfile` (recommended — one command, and everyone gets the exact same tools). **Option B** starts a bare `ubuntu:latest` container and installs the tools by hand, so you can see each step.

**Option A — build from the provided `Dockerfile` (recommended):**

The lab ships a `Dockerfile` at [`weeks/week-01/lab-env/Dockerfile`](lab-env/Dockerfile) that installs `git`, `curl`, `python3`/`pip`, `jq`, and the Docker CLI on top of `ubuntu:latest`.

```bash
# 1. Confirm the Docker daemon is running (Docker Desktop / Rancher Desktop started):
docker --version
docker run --rm hello-world      # should print "Hello from Docker!"

# 2. Build the lab image (run from the repo root):
docker build -t cse636-lab weeks/week-01/lab-env

# 3. Create a persistent workspace on your host and start the container.
#    -v mounts a host folder so your work survives container resets.
#    The second -v shares your host's Docker daemon via the mounted socket
#    (so `docker` inside the container acts on your real daemon —
#     "Docker-out-of-Docker", enough for this lab and safer than DinD).
mkdir -p ~/lab-data

docker run -it --name cse636-lab \
  -v ~/lab-data:/root/lab-data \
  -v /var/run/docker.sock:/var/run/docker.sock \
  cse636-lab

# 4. Verify (you're now inside the container):
git --version
docker --version        # lists your host's containers/images
python3 --version
docker ps               # proves the mounted socket works
```

<details><summary>📄 What's in the Dockerfile</summary>

```dockerfile
FROM ubuntu:latest

# Non-interactive apt so the image builds without prompting for tzdata etc.
ENV DEBIAN_FRONTEND=noninteractive

# The same toolset the AWS path installs, plus the Docker CLI so this container
# can drive the host daemon via the mounted /var/run/docker.sock.
RUN apt-get update && apt-get install -y --no-install-recommends \
      git curl ca-certificates python3 python3-pip jq docker.io \
    && rm -rf /var/lib/apt/lists/*

# Optional: trust an extra CA for TLS-inspecting proxies (see "Behind a corporate
# proxy?" below). Empty certs/ (only .gitkeep) => no-op on an open network.
COPY certs/ /tmp/extra-ca/
RUN set -eu; \
    if ls /tmp/extra-ca/*.pem >/dev/null 2>&1 || ls /tmp/extra-ca/*.crt >/dev/null 2>&1; then \
      for bundle in /tmp/extra-ca/*.pem /tmp/extra-ca/*.crt; do \
        [ -e "$bundle" ] || continue; \
        awk -v d=/usr/local/share/ca-certificates \
          'BEGIN{n=0} /BEGIN CERTIFICATE/{n++} {print > (d"/extra-"n".crt")}' "$bundle"; \
      done; \
      update-ca-certificates; \
    fi; \
    rm -rf /tmp/extra-ca

# Node/npm (Claude Code's runtime) read TLS trust from this env var.
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt

# Your work lives here; mount a host folder onto it so it survives container resets.
WORKDIR /root/lab-data

CMD ["bash"]
```

Read it top to bottom: it's a literal, checked-in record of the environment — the same idea you'll apply to real services later in the course.

</details>

> **⚠️ Behind a corporate proxy?** (Zscaler, Netskope, etc.) If `curl https://…` fails inside the container with `unable to get local issuer certificate`, your network is doing TLS inspection: it re-signs HTTPS with a corporate CA your host trusts but a fresh container does not. Fix it **once, before you build** — export the CA and drop it into the Dockerfile's `certs/` folder:
>
> ```bash
> # On your macOS host — export the trusted CAs from the System keychain:
> security find-certificate -a -p /Library/Keychains/System.keychain \
>   > weeks/week-01/lab-env/certs/corp-ca.pem
> ```
>
> Then rebuild (`docker build -t cse636-lab weeks/week-01/lab-env`) — the image now trusts the proxy for both `curl`/`apt` and Node/npm. `certs/*.pem` is gitignored, so you won't commit it. On Linux the CAs usually live under `/etc/ssl/certs/`; on Windows, export from `certmgr.msc` (Trusted Root Certification Authorities) as Base-64 `.crt`.

**Option B — start a bare container and install tools by hand:**

```bash
# 1. Confirm the Docker daemon is running:
docker --version
docker run --rm hello-world      # should print "Hello from Docker!"

# 2. Create a persistent workspace and start a plain Ubuntu container:
mkdir -p ~/lab-data

docker run -it --name cse636-lab \
  -v ~/lab-data:/root/lab-data \
  -v /var/run/docker.sock:/var/run/docker.sock \
  ubuntu:latest bash

# 3. Inside the container, install the same DevOps tools as the cloud path
#    (this is exactly what the Dockerfile's RUN line automates):
apt-get update && apt-get install -y \
  git curl ca-certificates python3 python3-pip jq docker.io

# 4. Verify:
git --version
docker --version        # lists your host's containers/images
python3 --version
docker ps               # proves the mounted socket works
```

> **Reconnecting later:** the container keeps running in the background after you detach.
> - Re-enter it: `docker exec -it cse636-lab bash`
> - Stop it: `docker stop cse636-lab` — Restart it: `docker start -ai cse636-lab`
> - Reset to a clean slate: `docker rm -f cse636-lab` and re-run step 2.

> **Even lighter weight:** if installing a full container feels like overkill, you can run every command in the rest of this lab directly in your host terminal (macOS/Linux) or WSL2 (Windows), as long as `git`, `docker`, and `python3` are on your PATH. The container just guarantees a clean, identical environment for everyone.

<details><summary>🛟 Troubleshooting the local path</summary>

- **`Cannot connect to the Docker daemon`** — Docker Desktop / Rancher Desktop isn't running, or the socket mount path differs on your OS. On macOS/Linux the socket is `/var/run/docker.sock`; on Windows use Docker Desktop with the WSL2 backend and run these commands from a WSL2 shell.
- **`permission denied` on the socket** — you're running as `root` inside the container in the example above, so this is usually fine; on your host, add yourself to the `docker` group (`sudo usermod -aG docker $USER`, then re-login).
- **`docker: command not found` inside the container** — the tool install didn't complete. On Option A, rebuild with `docker build -t cse636-lab weeks/week-01/lab-env`; on Option B, re-run `apt-get install -y docker.io`.
- **`sudo: command not found`** — you're already `root` inside the container, so the `sudo` in the Step 3 commands is unnecessary. Just drop it (run `curl … | bash -`, not `curl … | sudo -E bash -`).
- **`curl: (60) … unable to get local issuer certificate`** — a TLS-inspecting corporate proxy. Trust its CA as described in the **"Behind a corporate proxy?"** callout above (drop `corp-ca.pem` into `certs/` and rebuild). If you're on the by-hand Option B, instead run inside the container: `cp /root/lab-data/corp-ca.pem /usr/local/share/ca-certificates/corp-ca.crt && update-ca-certificates && export NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt`.
- **Work disappeared after a restart** — you didn't save it under `/root/lab-data`, the only mounted (persistent) folder. Keep the repo and your collected data there.

</details>

---

### Step 2: Clone a sample repository

You will run the AI agent against a public sample repository with enough code complexity to demonstrate agent capabilities. Good choices:

```bash
# Option A: the course Jenkins project (familiar from the CLAUDE.md context)
git clone https://github.com/your-fork/CSE636.git
cd CSE636/project/Jenkins

# Option B: a Python microservice sample (more variety for the agent to work on)
git clone https://github.com/dockersamples/example-voting-app.git
cd example-voting-app

# Option C: any open-source project you are already familiar with
# (familiarity helps you evaluate whether the agent's suggestions are correct)
```

Spend 5 minutes reading the repository README before you run the agent. Understanding the intent of the code will help you evaluate the quality of the agent's output.

---

### Step 3: Install and run Claude Code (or GitHub Copilot)

**Option A — Claude Code:**

> **On the local Docker track (Step 1b)?** You're already `root` inside the container, so **drop every `sudo`** below (e.g. `curl … | bash -`). The commands otherwise work unchanged.

```bash
# Install Node.js (required for Claude Code) — omit `sudo` if you're inside the container
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Authenticate (you will need an Anthropic API key from https://console.anthropic.com)
export ANTHROPIC_API_KEY="your-key-here"

# Run Claude Code in the repo directory
cd example-voting-app
claude
```

**Option B — GitHub Copilot in VS Code:**
If you prefer a GUI environment, install VS Code, the GitHub Copilot extension, and enable "Agent mode" in Copilot settings. This is equivalent for this lab's purposes.

---

### Step 4: Give the agent a set of tasks and observe its behavior

Run the following tasks one at a time. After each task, **before accepting any changes**, pause and evaluate:
- Does the agent's plan make sense?
- What tools did it call?
- What did it observe from each tool result?
- Is the proposed change correct?

**Suggested tasks:**

```
Task 1 (exploration):
"Read the repository structure and give me a plain-English summary of 
what this application does and how its components are connected."

Task 2 (analysis):
"Find any security issues or hardcoded credentials in this repository 
and list them with the file path and line number."

Task 3 (generation):
"Write a GitHub Actions CI workflow that builds and tests this 
application. Place it in .github/workflows/ci.yml."

Task 4 (iteration):
"The Dockerfile uses an old base image. Update it to use the latest 
stable version and explain the change."
```

<details><summary>✅ Check your understanding — spot the loop</summary>

As the agent works Task 1, try to name each step of the loop from the notes as it happens:

- **Perceive** — it reads files / the repo structure.
- **Plan/Reason** — it states what it will look at next and why.
- **Act** — it calls a tool (read a file, run a command, grep).
- **Observe** — it reads that tool's output, then decides the next step.

If you can point at each of these in the agent's transcript, you've seen the core mental model of the whole course in action. Note **which level of autonomy** it ran at — did it act, or pause for your approval?

</details>

---

### Step 5: Collect CI/CD and monitoring data

The data you collect this week will be used as input to agent tasks in later weeks.

**CI/CD data to collect:**

```bash
# If the sample repo has a CI config, trigger a build and capture the output:
# (For a GitHub Actions pipeline)
# - Go to the repository's "Actions" tab
# - Run the workflow manually
# - Download the build log

# Save it:
mkdir -p ~/lab-data/week01
# Paste or redirect the build log output here:
cat > ~/lab-data/week01/ci-build-log.txt
# (paste the log, then Ctrl+D)
```

**System metrics to collect (from your cloud VM — or from inside your local `cse636-lab` container):**

```bash
# Capture a snapshot of system metrics:
echo "=== CPU ===" > ~/lab-data/week01/system-metrics.txt
top -bn1 | head -20 >> ~/lab-data/week01/system-metrics.txt

echo "=== Memory ===" >> ~/lab-data/week01/system-metrics.txt
free -h >> ~/lab-data/week01/system-metrics.txt

echo "=== Disk ===" >> ~/lab-data/week01/system-metrics.txt
df -h >> ~/lab-data/week01/system-metrics.txt

echo "=== Docker containers ===" >> ~/lab-data/week01/system-metrics.txt
docker ps -a >> ~/lab-data/week01/system-metrics.txt
```

---

### Step 6: Document your observations (what to submit)

Write a short lab report (1–2 pages) covering:

1. **Environment:** which track you used — cloud provider + instance type, or the local Docker container (Step 1b) — and what sample repo you chose.
2. **Agent tasks:** for each task you gave the agent, describe: what the agent did, what tools it called, whether the output was correct, and one thing that surprised you.
3. **Reflection:** At which level of autonomy (1–4) would you feel comfortable running this agent on a *production* repository? Why? What would need to change to move it to the next level?
4. **Data collected:** confirm you have a `ci-build-log.txt` and `system-metrics.txt` file saved. You will use these in later labs.

---

## Assignment: Real-World Agentic DevOps Deployments

**Due:** Before the start of Week 2

**Format:** Written report, 800–1,200 words, submitted as a PDF

**Objective:** Ground the theoretical concepts from Week 1 in real deployments. Distinguish between genuine agentic systems and simpler automation. Think critically about risk and governance.

---

### Task

Research and write about **three distinct real-world deployments** of AI agents in DevOps or software engineering contexts. At least one must be a deployment you found in industry news or a conference talk (not a vendor marketing page). At least one must involve a risk or failure — something that did not go as planned.

For each deployment, answer the following questions:

#### 1. Level of autonomy (25% of grade)
- Where does this system sit on the assistant → human-in-the-loop → human-on-the-loop → autonomous scale?
- What evidence (from the source) supports your classification?
- What keeps the system at this level rather than the next one?

#### 2. Tools and data (25% of grade)
- What tools does the agent use? (CI/CD APIs, monitoring systems, code repositories, ticket systems, etc.)
- What data does the agent consume? (logs, metrics, traces, code, natural-language descriptions?)
- How does the agent connect to these tools? (direct API, CLI, MCP, custom integration?)

#### 3. Measured impact (25% of grade)
- What measurable improvement did the organization report? (MTTR reduction, deployment frequency, cost savings, toil reduction?)
- How credible is the measurement? (Is it controlled, or anecdotal marketing?)
- What baseline did they compare against?

#### 4. Main risks (25% of grade)
- What could go wrong if the agent makes a mistake?
- What guardrails does the organization describe?
- What risks are *not* mentioned that you think are present?

---

### Suggested report structure

```
Title: Real-World Agentic DevOps Deployments
Your name, date, CSE636

Introduction (1 paragraph)
  - What is your selection criterion for the three deployments?
  - What is the key question you are trying to answer?

Deployment 1: [Name / Organization]
  - Source(s)
  - Summary (2–3 sentences)
  - Level of autonomy analysis
  - Tools and data
  - Measured impact
  - Main risks

Deployment 2: [Name / Organization]
  [same structure]

Deployment 3: [Name / Organization]
  [same structure]

Cross-cutting observations (1–2 paragraphs)
  - What patterns do you see across all three?
  - What surprised you?
  - What would you want to study further?

References
```

---

### Grading rubric hints

- **Excellent:** All three deployments are clearly distinct in type (e.g., one coding agent, one incident response agent, one infrastructure agent). The autonomy level classification is argued with evidence, not asserted. Risks identified go beyond what the source explicitly states.
- **Good:** Solid coverage of all four areas. Some analysis goes beyond summarizing the source material.
- **Needs improvement:** Report mostly summarizes source material without analysis. Autonomy levels are asserted without evidence. Risks are thin or generic.
- **Disqualified from full credit:** Vendor marketing pages used as primary source without corroboration. AI-generated report submitted without review or disclosure.

**Finding sources:** IEEE Software, ACM Queue, the DORA State of DevOps report, Anthropic's engineering blog, GitHub's engineering blog, conference talks from KubeCon, SREcon, and DevOpsDays, and case studies from Datadog, PagerDuty, and New Relic are good starting points.
