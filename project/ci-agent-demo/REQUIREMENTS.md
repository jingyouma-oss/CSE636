# CI/CD Agent-in-the-Loop — Requirements

You are an autonomous CI/CD engineer operating **local Jenkins** through MCP
tools. Read this document, then execute the loop below. Do not touch Jenkins
in any way other than the MCP tools listed.

## Objective

Stand up a CI pipeline for the app in `app/`, drive it to a failing (red)
build, diagnose the failure, apply a **human-approved** minimal fix, and prove
the pipeline goes green — then write a report.

## Success criteria

1. A Jenkins pipeline job named `ci-agent-demo` exists (you create it).
2. Build #1 is RED (the app has a failing test).
3. You correctly identify the failing test and its root cause from the log.
4. You propose a minimal fix and **wait for human approval** before applying it.
5. After approval and a `git push`, a fresh build is GREEN.
6. You write `reports/run-NN.md` (next unused number) summarizing the run.

## Constraints

- **Jenkins only via MCP tools:** `create_job`, `trigger_build`,
  `get_build_status`, `get_build_log`, `list_jobs`. No curl, no REST, no UI.
- **Human approval gate is mandatory.** Present the fix as a diff and stop.
  Do not edit, commit, or push until the instructor approves in the chat.
- **Minimal fix only.** Change the single line that is wrong. Never edit,
  delete, disable, `skip`, or weaken a test to make the build pass.
- **Stop after 2 failed fix attempts** and hand back to the human.

## Pipeline contract

Create `ci-agent-demo` with an inline declarative pipeline that:
1. Checks out the class repo on `main`:
   `git branch: 'main', url: '<CLASS_REPO_HTTPS_URL>'` (add
   `credentialsId: 'github-https'` only if the repo is private).
2. Runs the tests and surfaces failures as a red build:
   `dir('project/ci-agent-demo/app') { sh 'python3 -m pytest -q' }`.

Use `agent any` (single-container `cstu-jenkins`).

## Agent loop

1. Author the Jenkinsfile above; `create_job('ci-agent-demo', <script>)`.
2. `trigger_build('ci-agent-demo')`; note the build number from `get_build_status` and poll `get_build_status` until a NEW build appears and is no longer IN_PROGRESS.
3. If RED: `get_build_log('ci-agent-demo')`; identify the failing test + cause.
4. Propose the minimal fix as a unified diff. **Wait for approval.**
5. On approval: edit the source, `git commit`, `git push origin main`.
6. `trigger_build` again; capture the new build number and poll until that build is GREEN (not a stale earlier result).
7. Write the report (see below). If still red after a 2nd attempt, stop.

## Report format (`reports/run-NN.md`)

```
# CI Agent Run NN — <UTC timestamp>

- Job: ci-agent-demo
- Build #1: <result>   Build #2: <result>

## Failure
- Test: <name>
- Assertion: <what failed>
- Root cause: <one sentence>

## Fix (approved by instructor)
<diff>
Rationale: <one sentence>

## Verification
Build #2: <result> — <n passed>

## MCP calls (audit trail)
- create_job, trigger_build, get_build_status × N, get_build_log, ...
```
