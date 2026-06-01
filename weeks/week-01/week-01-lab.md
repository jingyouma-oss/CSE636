# Week 1 — Lab & Assignment

> 🧪 **Hands-on work for Week 1.** For the lecture notes, foundations primer, discussion questions, and references, see **[week-01-notes.md](week-01-notes.md)**.

---

## 🧪 Lab: Week 1

**Title:** Cloud DevOps Lab Setup and First AI Agent Run

**Time budget:** ~3 hours (can be spread across the week as take-home work)

**Goal:** Have a working cloud lab environment and have successfully run an AI coding agent against a real repository — so you arrive at Week 2 with hands-on context for the tool comparison discussion.

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

> **Note:** If setting up a full cloud VM is not possible in the first week, you can use Docker Desktop on your local machine or a free cloud IDE (GitHub Codespaces, Gitpod, Replit) as a substitute. The key is having a Git-enabled environment where you can run shell commands.

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

```bash
# Install Node.js (required for Claude Code)
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

**System metrics to collect (from your cloud VM):**

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

1. **Environment:** which cloud provider and instance type you used; what sample repo you chose.
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
