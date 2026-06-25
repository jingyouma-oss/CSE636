# Design: 3-Tier App on Docker Desktop Kubernetes (`project/k8s-demo/`)

**Date:** 2026-06-25
**Status:** Approved (brainstorming) — pending implementation plan
**Context:** New runnable starter for CSE636 (DevOps with AI). A class-demoable
three-tier application (frontend + backend + database), each in its own
container, managed by Kubernetes, running on a Mac via Docker Desktop's built-in
Kubernetes.

## Goal

Demonstrate, clearly and end-to-end, that **each application tier is one
container image → one Kubernetes Deployment → one Service**, and that the tiers
communicate through Kubernetes networking. The demo must run on a Mac with only
Docker Desktop (Kubernetes enabled) — no extra cluster tools.

## Decisions (locked during brainstorming)

| Decision | Choice | Rationale |
|---|---|---|
| K8s runtime | **Docker Desktop Kubernetes** (single node) | Simplest on Mac; locally-built images are usable directly (no image load step). |
| Stack | **FastAPI** (backend) + **Postgres** (DB) + **React/Vite** (frontend, served by Nginx) | Per user choice. |
| Scope | **Standard 3-tier** | Deployments + Services + Secret + PVC + probes + Nginx `/api` proxy. No autoscaling/rollout demo (deferred). |
| Placement | New starter `project/k8s-demo/`, with a pointer from Week 4 notes | Discoverable, consistent with other starters. |
| DB shape | **Deployment + PVC** with `Recreate` strategy (not StatefulSet) | Clearer teaching shape; README notes production uses StatefulSet. |
| Frontend↔backend | **Nginx reverse-proxies `/api`** to the backend Service | Single exposed port; teaches that browser-side code can't use in-cluster DNS. |
| Diagram | **Include a course-style SVG** in `project/k8s-demo/images/` | Matches the `weeks/` visual convention; aids the demo. |

## Architecture

All objects live in a `k8s-demo` namespace.

| Tier | Container | K8s objects | Replicas | Exposure |
|---|---|---|---|---|
| Frontend | React (Vite) static build served by **Nginx** | Deployment, Service (**NodePort 30080**), ConfigMap (`nginx.conf`) | 2 | `http://localhost:30080` |
| Backend | **FastAPI** (uvicorn, port 8000) | Deployment, Service (ClusterIP), ConfigMap (DB host/name/user) | 2 | in-cluster only |
| Database | **Postgres** (port 5432) | Deployment (`Recreate`), Service (ClusterIP), Secret (password), PVC (1Gi), ConfigMap (`init.sql`) | 1 | in-cluster only |

### Data flow

```
Browser ──> localhost:30080 (frontend NodePort)
   └─ Nginx serves React static files
   └─ React calls /api/* ──> Nginx proxies /api/* ──> backend:8000 (ClusterIP)
                                                          └─> FastAPI ──> db:5432 (ClusterIP) ──> Postgres
```

### Key networking lesson (built into the README)

The React app executes **in the browser**, so it cannot resolve in-cluster
Service DNS — that is why Nginx reverse-proxies `/api` to the backend. The
backend↔DB hop, by contrast, *does* use Service DNS (`backend`, `db`). One
exposed port (the frontend NodePort) is the whole surface area.

## Application behavior (deliberately tiny)

- **Backend endpoints:**
  - `GET /api/health` — returns OK and checks DB connectivity (drives the readiness probe).
  - `GET /api/items` — list rows from the `items` table.
  - `POST /api/items` — insert a row (`{"name": "..."}`).
- **Database:** an `items` table created and seeded on first init via a mounted `init.sql` (Postgres runs `/docker-entrypoint-initdb.d/*.sql` on first boot).
- **Frontend:** a one-page React UI that lists items and adds one — enough to prove all three tiers talk end-to-end.

## File layout

```
project/k8s-demo/
├── README.md
├── Makefile
├── images/
│   └── architecture.svg          # course-style 3-tier diagram (browser → fe → be → db)
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app + routes
│   │   └── db.py                 # connection helper (env-driven), startup retry
│   ├── tests/test_api.py         # pytest: pure logic + TestClient with DB mocked
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/                      # React/Vite app (App.jsx, main.jsx)
│   ├── index.html, package.json, vite.config.js
│   ├── nginx.conf                # serve static + proxy /api -> backend:8000
│   └── Dockerfile                # multi-stage: node build -> nginx:alpine
├── db/
│   └── init.sql                  # CREATE TABLE items + seed rows
└── k8s/
    ├── namespace.yaml
    ├── db-secret.yaml            # POSTGRES_PASSWORD (demo value)
    ├── db-config.yaml            # ConfigMap: POSTGRES_DB/USER + init.sql
    ├── db-pvc.yaml               # 1Gi, default (hostpath) storageClass
    ├── db-deployment.yaml        # Postgres, strategy: Recreate, replicas: 1
    ├── db-service.yaml           # ClusterIP, name: db
    ├── backend-config.yaml       # ConfigMap: DB_HOST=db, DB_NAME, DB_USER
    ├── backend-deployment.yaml   # FastAPI, probes, replicas: 2
    ├── backend-service.yaml      # ClusterIP, name: backend, port 8000
    ├── frontend-config.yaml      # ConfigMap: nginx.conf
    ├── frontend-deployment.yaml  # Nginx+React, replicas: 2
    └── frontend-service.yaml     # NodePort 30080, name: frontend
```

## Configuration & secrets

- **DB password:** a Kubernetes `Secret` (`db-secret`), consumed by both the
  Postgres pod (`POSTGRES_PASSWORD`) and the backend (as `DB_PASSWORD` via
  `secretKeyRef`). README notes the value is a demo placeholder committed for
  convenience and is *not* how real secrets are handled.
- **Non-secret DB settings:** `DB_HOST=db`, `DB_NAME`, `DB_USER` via ConfigMap.
- **Image policy:** all images tagged `:local` with `imagePullPolicy: IfNotPresent`
  so the cluster uses locally-built images and never tries to pull `:latest`.

## Makefile (the demo runbook)

| Target | Action |
|---|---|
| `make check` | Warn if `kubectl config current-context` is not `docker-desktop`; check the Kubernetes node is Ready. |
| `make images` | `docker build` the backend and frontend images, tagged `:local`. |
| `make deploy` | `kubectl apply -f k8s/namespace.yaml` then `kubectl apply -f k8s/`. |
| `make status` | `kubectl get pods,svc,pvc -n k8s-demo`. |
| `make open` | Open `http://localhost:30080`. |
| `make logs` | Tail backend pod logs. |
| `make test` | Run backend pytest (no cluster needed). |
| `make clean` | `kubectl delete namespace k8s-demo`. |

`make deploy` applies the namespace first so namespaced resources don't fail on
a missing namespace (alphabetical `kubectl apply -f k8s/` would otherwise apply
`namespace.yaml` last).

## Robustness & error handling

- **PVC** keeps Postgres data across pod restarts; **`Recreate`** strategy means
  the single DB replica never deadlocks trying to mount an RWO volume held by an
  old pod during a rolling update.
- **Backend readiness probe** on `GET /api/health` (which pings the DB) gates
  traffic until Postgres is up; backend **retries** the DB connection on startup
  so pod start order doesn't matter.
- **Liveness probe** on the backend restarts a wedged pod.
- `make check` catches the most common Mac footgun: wrong kubectl context, or
  Kubernetes not enabled in Docker Desktop.

## Testing

- **Automated:** `make test` runs `backend/tests/test_api.py` — pure
  request/response logic via FastAPI `TestClient` with the DB layer mocked, so it
  passes offline with no cluster or Postgres. Honors the repo's "pure tested
  core" convention.
- **Manual (in README, as a checklist):**
  1. `make images && make deploy && make status` → all pods `Running`.
  2. `curl http://localhost:30080/api/health` → healthy + DB reachable.
  3. Open the browser, add an item, see it persist.
  4. `kubectl delete pod -l app=backend -n k8s-demo` → watch K8s recreate it; the app stays up (2 replicas).
  5. Delete the DB pod → data survives (PVC) once it restarts.

## Course fit

- New starter under `project/`, Makefile + README like the others.
- A short pointer added to `weeks/week-04/week-04-notes.md` (Kubernetes section)
  to this runnable demo.
- `project/k8s-demo/images/architecture.svg` follows the course SVG convention
  (linked file, descriptive alt text) — a labeled diagram showing browser →
  frontend (Nginx+React, NodePort) → backend (FastAPI, ClusterIP) → database
  (Postgres, ClusterIP + PVC), with the namespace boundary and the `/api` proxy
  hop called out.

## Out of scope (deferred)

- Horizontal autoscaling / HPA and rolling-update demos (the "Standard +
  scaling" option) — could be a follow-up that ties into Week 4's autoscaling
  material.
- Ingress controller (NodePort is sufficient on Docker Desktop).
- StatefulSet for the database.
- TLS / real secret management.

## .gitignore note

Add `project/k8s-demo/frontend/node_modules/` and `project/k8s-demo/frontend/dist/`
to `.gitignore` (regenerable build artifacts), consistent with how other
starters exclude generated output.
