# Design — Extend `k8s-demo` into the full capstone pipeline (local Kubernetes)

**Date:** 2026-07-08
**Status:** Approved (design); implementation plan to follow
**Scope target:** [`project/k8s-demo/`](../../../project/k8s-demo/)

## 1. Goal & context

Turn the existing three-tier `k8s-demo` starter (React/Nginx + FastAPI + Postgres,
one Deployment+Service per tier in the `k8s-demo` namespace, Postgres on a PVC)
into a **reference implementation of the full Week 7 capstone** — all five stages
of the agentic DevOps pipeline — running entirely on a **local single-node
Kubernetes** (Docker Desktop or Rancher Desktop's moby engine). Students clone the
repo and study/run it.

This design realizes the pipeline defined in
[weeks/week-07/week-07-lab.md](../../../weeks/week-07/week-07-lab.md) and graded by
its [100-point rubric](../../../weeks/week-07/week-07-lab.md#rubric-100-points).

### Decisions locked during brainstorming

| Decision | Choice |
|---|---|
| Deliverable | Extend `k8s-demo` **in place** as a checked-in reference implementation |
| Stage scope | **All 5 stages** wired into `k8s-demo` end-to-end |
| Observability | **Prometheus + Grafana only** (metrics-first); tracing is a documented upgrade path |
| Agent runtime | **Local CLI** against a **scoped kubeconfig** (dedicated ServiceAccount + namespace Role) |
| Canary | **Blue-green** (two Deployments, Service-selector flip after an error-rate check) |
| Structure | **Approach A** — layered subdirs + staged Makefile targets |

### Known rubric trade-off (accepted)

The rubric line "OTel **spans** for service and agent actions" is only partially met
by a metrics-first stack. Mitigation: agent activity is exported as Prometheus
metrics (e.g. `agent_anomaly_detected`, action counters), and `CAPSTONE.md`
documents an easy upgrade path (add Tempo/Jaeger + the OTel tracing SDK) for teams
that want full spans.

## 2. Architecture & end-to-end data flow

A developer commit flows through five `make`-driven stages, each gated by a
guardrail, all against the local `k8s-demo` namespace.

```
[dev commit]
   │
 ① CI/CD (ci/Jenkinsfile) ── build :local images → run backend tests → kubectl apply
   │                          guardrail: no apply unless tests pass
   ▼
 ② IaC (iac/) ── terraform (kubernetes provider) renders manifests → OPA/conftest gate → human approves → apply
   │              guardrail: no apply unless OPA passes + plan approved
   ▼
 ③ Predictive deploy (agents/scaling_agent.py + k8s/canary/) ── Prophet reads Prometheus CPU history →
   │   recommends HPA min/max → deploy new version as backend-green → error-rate check → flip Service → scale down blue
   │   guardrail: promotion blocked unless green's error-rate metric is under threshold
   ▼
 ④ Observability (k8s/observability/) ── Prometheus scrapes backend + agents; Grafana dashboards;
   │   isolation-forest scores the metric stream for anomalies
   │   guardrail: agent may not remediate until an anomaly/alert is recorded
   ▼
 ⑤ Auto-remediate (agents/remediation_agent.py) ── ReAct agent reads anomaly → proposes action
       (rollout undo / scale) → human approval gate → acts via SCOPED kubeconfig → writes ITSM record + audit log
       guardrail: RBAC Role limits it to k8s-demo namespace; every action logged
```

### Integration seams (what makes it one pipeline, not five demos)

- **Metrics are the shared bus.** The backend exposes `/metrics` (Prometheus
  format). Prometheus is the single source both the scaling agent (CPU history →
  Prophet) and the anomaly detector (error-rate/latency → isolation-forest) read
  from.
- **The scoped kubeconfig is the shared guardrail.** Both agents authenticate as
  the `k8s-demo-agent` ServiceAccount (namespace-scoped Role), never the admin
  context — so blast-radius control and least-privilege are enforced by the
  cluster and provable via `kubectl auth can-i`.
- **The audit log is append-only JSONL.** Both agents write to one `audit.jsonl`
  (timestamp, actor, proposed action, approver, result), backing the
  audit/governance criterion.

## 3. Repository layout (Approach A)

```
project/k8s-demo/
  k8s/                     # unchanged base app (frontend/backend/db)
  k8s/observability/       # prometheus + grafana + scrape config + dashboard JSON
  k8s/canary/              # backend-blue / backend-green + promote.sh (service selector flip)
  k8s/rbac/                # agent-serviceaccount.yaml + agent-role.yaml
  agents/                  # scaling_agent.py, anomaly_detector.py, remediation_agent.py (local CLI)
  iac/                     # terraform (kubernetes provider) + reused OPA rego
  ci/                      # Jenkinsfile (build :local + kubectl apply)
  Makefile                 # + observability, scale-recommend, canary-deploy, promote,
                           #   remediate, agent-kubeconfig, iac-*, lint, e2e
  CAPSTONE.md              # end-to-end runbook: each target → rubric stage → guardrail demo
```

The existing flat `k8s/` base app and the `make check/images/deploy/status/open/
logs/test/clean` runbook are preserved; new stages are added as sibling folders
and new `make` targets so each stage is independently runnable.

## 4. Per-stage components

### ① CI/CD — `ci/`
- `Jenkinsfile` — declarative pipeline: `checkout` → `make test` (backend unit
  tests) → `make images` (`:local`) → `make deploy`. The test stage is a hard
  gate; a red build never reaches apply.
- Reuses the [`project/Jenkins/`](../../../project/Jenkins/) master image as the
  runner (documented in `CAPSTONE.md`, not duplicated).
- Depends on: Jenkins-in-Docker with the host Docker socket + kubeconfig mounted.

### ② IaC — `iac/`
- `main.tf` — Terraform using the **`kubernetes` provider** pointed at the local
  context; renders the backend Deployment + Service + HPA as Terraform resources
  so `terraform apply` genuinely mutates the cluster.
- `policy/` — Rego reused/adapted from [`project/iac/`](../../../project/iac/),
  asserting on the k8s plan JSON (e.g. resource limits set, no `:latest` tags,
  replicas ≥ 2). `make iac-policy` runs `conftest` on `terraform show -json`;
  `make iac-policy-fail` shows a violating variant blocked.
- Guardrail: apply target prints the plan and requires a typed confirmation after
  OPA passes.

### ③ Predictive deploy — `agents/scaling_agent.py` + `k8s/canary/`
- `scaling_agent.py` — local CLI: pulls CPU history from Prometheus, runs Prophet
  (reuses [`project/forecasting/`](../../../project/forecasting/) `scaling.py`
  logic), prints recommended HPA `minReplicas`/`maxReplicas` + a FinOps cost line
  (replicas × node-hour rate), optionally patches the HPA.
- `k8s/canary/` — `backend-green-deployment.yaml` (same image, new version label)
  alongside blue; `promote.sh` flips `backend-service`'s selector `blue→green`
  **only after** querying green pods' error-rate in Prometheus; rollback = flip
  back.
- Guardrail: `promote.sh` exits non-zero (no flip) if error-rate ≥ threshold.

### ④ Observability — `k8s/observability/`
- `prometheus-deployment.yaml` + `prometheus-config.yaml` (scrape backend
  `/metrics` and an agent pushgateway), `grafana-deployment.yaml` + a provisioned
  dashboard JSON (RED metrics + anomaly overlay).
- Backend gains a `/metrics` endpoint (prometheus-client): request count, error
  count, latency histogram, CPU.
- `agents/anomaly_detector.py` — reuses [`project/anomaly/`](../../../project/anomaly/)
  `evaluation.py`; scores the error-rate stream, writes an anomaly record and a
  Prometheus metric (`agent_anomaly_detected`) so agent activity itself is
  observable (the metrics-based substitute for agent spans).
- Guardrail seam: the remediation agent refuses to act unless a fresh anomaly
  record exists.

### ⑤ Auto-remediate — `agents/remediation_agent.py` + `k8s/rbac/`
- `remediation_agent.py` — ReAct loop (reuses the
  [Week 6 lab](../../../weeks/week-06/week-06-lab.md) agent/MCP pattern): reads the
  anomaly → reasons → proposes `rollout undo` or `scale` → **human approval
  prompt** → executes via the scoped kubeconfig → appends to `audit.jsonl` →
  writes a simulated `itsm-ticket-*.json`.
- `k8s/rbac/` — `agent-serviceaccount.yaml` + `agent-role.yaml` (verbs limited to
  get/list/patch on deployments/pods in `k8s-demo` only) + `make agent-kubeconfig`
  to mint the scoped kubeconfig the agents use.
- Guardrail: RBAC caps blast radius; approval gate + audit log cover governance.

## 5. Cross-cutting: guardrails, security & audit

45 of the rubric's 100 points (IaC policy, agent security, remediation
blast-radius, audit/governance) live here.

### The five guardrails (each demoable with one command)

| # | Guardrail | Enforced by | Demo proof |
|---|---|---|---|
| 1 | No merge/deploy on failing tests | Jenkinsfile test stage (hard gate) | Push a red commit → pipeline stops before apply |
| 2 | No IaC apply without policy + approval | `conftest` on plan JSON + typed confirm | `make iac-policy-fail` shows OPA blocking a limit-less Deployment |
| 3 | Canary promotion gated on error-rate | `promote.sh` Prometheus query | Inject errors into green → promote refuses & rolls back |
| 4 | Agent can't act before an anomaly exists | Remediation agent pre-check | Run agent with no anomaly → it declines |
| 5 | Least-privilege / blast-radius | `k8s-demo-agent` RBAC Role | `kubectl auth can-i delete deploy -n kube-system --as=…agent` → **no** |

### Security defenses (rubric wants ≥ 2)

- **Scoped ServiceAccount + namespace Role** — the agent cannot touch anything
  outside `k8s-demo` (provable, not asserted).
- **Human approval gate** in the remediation agent before any mutating call.
- **Prompt-injection defense demo** — anomaly/log text is treated as data, not
  instructions; the agent's action space is a fixed allow-list of tools
  (`rollout undo`, `scale`), so an injected "delete everything" in a log line has
  no reachable tool. `CAPSTONE.md` includes a scripted injection attempt that
  fails harmlessly.

### Audit trail & secrets

- **`audit.jsonl` (append-only):** every agent decision writes one line
  `{ts, stage, actor, anomaly_id, proposed_action, approved_by, result,
  kubeconfig_context}`. `itsm-ticket-*.json` records satisfy "ITSM record
  created."
- **Secrets:** reuse the existing `db-secret.yaml` pattern; `ANTHROPIC_API_KEY`
  comes from the local env, never committed — consistent with the other starters.

## 6. Testing strategy

Mirrors the repo convention (a pure tested core + a heavier driver) so `make test`
stays dependency-light and cluster-free.

| Layer | What's tested | Runs where |
|---|---|---|
| **Pure unit** (`make test`, no cluster/heavy deps) | scaling math (reuse `forecasting/scaling.py` tests), anomaly precision/recall (reuse `anomaly/evaluation.py` tests), audit-record serialization, OPA policy via `conftest` on bundled plan JSON, promote/rollback threshold as a pure function | laptop, CI |
| **Manifest validation** (`make lint`) | `kubectl apply --dry-run=server` on all manifests; `conftest` on rendered Terraform plan | laptop w/ cluster |
| **Integration smoke** (`make e2e`, documented, not in CI) | deploy → generate load → confirm metrics in Prometheus → inject anomaly → agent proposes + (auto-approve flag) remediates → assert rollout reverted | local cluster |

Agents' LLM calls are **not** unit-tested (non-deterministic); their *decision
logic* is factored into pure functions that are. `make test` stays green and fast
— the failing-by-design exception in `build-fixer` does **not** apply here.

## 7. Makefile targets

Extends the existing runbook (`check images deploy status open logs test clean`):

```
observability    ## deploy prometheus + grafana, open grafana
scale-recommend  ## run Prophet scaling agent → print HPA + cost recommendation
canary-deploy    ## roll out backend-green alongside blue
promote          ## error-rate-gated flip blue→green (or rollback)
remediate        ## run the ReAct remediation agent (approval-gated)
agent-kubeconfig ## mint the scoped k8s-demo-agent kubeconfig
iac-plan / iac-policy / iac-policy-fail / iac-apply
lint / e2e
```

## 8. Prerequisites (all local)

Docker Desktop or Rancher Desktop with Kubernetes enabled; `metrics-server`
enabled (needed for HPA); `kubectl`, `terraform`, `conftest`, Python 3.11 + venv;
`ANTHROPIC_API_KEY` in env for the agents; the
[`project/Jenkins/`](../../../project/Jenkins/) image for Stage 1.

## 9. Documentation deliverables

- New `project/k8s-demo/CAPSTONE.md` — end-to-end runbook mapping each `make`
  target → rubric stage → guardrail demo.
- Pointer added from [weeks/week-07/week-07-lab.md](../../../weeks/week-07/week-07-lab.md)
  and the [GROUP_PROJECT_GUIDE.md](../../../weeks/GROUP_PROJECT_GUIDE.md) starter
  list.
- Update [CLAUDE.md](../../../CLAUDE.md)'s `project/k8s-demo/` description to reflect
  the added stages.

## 10. Rubric coverage map

| Rubric criterion (pts) | Covered by |
|---|---|
| End-to-end pipeline integration (20) | §2 data flow; all five `make` stages against one namespace |
| Agentic IaC with policy enforcement (15) | ② `iac/` + OPA gate + approval |
| Agent security and guardrails (15) | §5 scoped RBAC + approval gate + prompt-injection demo |
| Observability, service + agent telemetry (10) | ④ Prometheus/Grafana + `agent_anomaly_detected` metric (span upgrade path noted) |
| Auto-remediation with blast-radius control (10) | ⑤ remediation agent + namespace Role + ITSM record |
| Audit trail and governance (10) | §5 `audit.jsonl` + timestamped approvals |
| Presentation clarity and demo quality (10) | `CAPSTONE.md` one-command-per-guardrail demos |
| Technical report quality (10) | out of scope for this code; supported by the design doc + diagram |

## 11. Out of scope (YAGNI)

- Service mesh / weighted traffic-splitting (blue-green covers the rubric line).
- Distributed tracing spans (documented upgrade path only).
- Real cloud provisioning (Terraform targets the local cluster, not AWS).
- Multi-node cluster concerns (HA, node autoscaling).
- SLSA provenance beyond a signed metadata file generated in CI (optional stretch).
