# k8s-demo — a 3-tier app on Docker Desktop Kubernetes

A class demo: **React frontend → FastAPI backend → Postgres database**, each in
its own container, each one Kubernetes Deployment + Service, all in a `k8s-demo`
namespace on your Mac's Docker Desktop Kubernetes.

![Architecture: a Mac browser hits the frontend NodePort on localhost:30080; inside the k8s-demo namespace, the Frontend Deployment (React + Nginx, 2 replicas) reverse-proxies /api to the Backend Deployment (FastAPI, 2 replicas) via the backend ClusterIP Service on port 8000; the backend talks to the Database Deployment (Postgres, 1 replica) via the db ClusterIP Service on 5432; Postgres persists to a 1Gi PersistentVolumeClaim; a Secret supplies the DB password and ConfigMaps supply non-secret settings and the Nginx proxy config.](images/architecture.svg)

## Prerequisites

- **Docker Desktop** with **Kubernetes enabled** (Settings → Kubernetes → Enable Kubernetes → Apply & restart).
- `kubectl` pointed at the `docker-desktop` context (`kubectl config use-context docker-desktop`).

## Quickstart

```bash
cd project/k8s-demo
make check     # confirms Docker Desktop K8s is active
make images    # build k8s-demo-backend:local and k8s-demo-frontend:local
make deploy    # create the namespace and apply all manifests
make status    # wait until every pod is Running / Ready
make open      # opens http://localhost:30080
```

Add an item in the UI — it round-trips React → Nginx `/api` proxy → FastAPI →
Postgres and back.

## How the tiers connect

```
Browser ─> localhost:30080 (frontend NodePort)
   └─ Nginx serves the React build
   └─ React calls /api/* ─> Nginx proxies to backend:8000 (ClusterIP)
                              └─> FastAPI ─> db:5432 (ClusterIP) ─> Postgres
```

The React app runs **in the browser**, so it can't resolve Kubernetes Service
DNS — that's why Nginx reverse-proxies `/api` to the `backend` Service. The
backend↔database hop *does* use Service DNS (`db`). One exposed port total.

## Verify it works

1. `make status` → `db`, `backend` (×2), `frontend` (×2) pods all `Running`.
2. `curl http://localhost:30080/api/health` → `{"status":"ok"}` (liveness).
3. `curl http://localhost:30080/api/ready` → `{"status":"ready",...}` (DB reachable).
4. Open the browser, add an item, refresh — it persists.
5. **Self-healing:** `kubectl delete pod -l app=backend -n k8s-demo` — Kubernetes
   recreates the pod and the app stays up (2 replicas).
6. **Persistence:** `kubectl delete pod -l app=db -n k8s-demo` — once Postgres
   restarts, your items are still there (PVC).

## Teardown

```bash
make clean     # deletes the k8s-demo namespace and everything in it
```

## Notes for the curious

- **DB as a Deployment + PVC** (with `strategy: Recreate`) is used here for
  teaching clarity. Production databases on Kubernetes typically use a
  **StatefulSet** with stable network identity and per-replica storage.
- **The DB password** lives in `k8s/db-secret.yaml` as a committed demo value.
  Real systems inject secrets from a manager (Vault, cloud KMS, sealed-secrets),
  never commit them.
- **`imagePullPolicy: IfNotPresent` + `:local` tags** make Kubernetes use the
  images you built locally instead of trying to pull them from a registry.

## Troubleshooting

- **`ErrImageNeverPull` / `ImagePullBackOff`:** run `make images` first; the
  manifests never pull (`IfNotPresent` + `:local`).
- **PVC stuck `Pending`:** Docker Desktop ships a default `hostpath` StorageClass;
  ensure Kubernetes is fully started (`kubectl get sc`).
- **`make check` fails:** enable Kubernetes in Docker Desktop and switch context
  with `kubectl config use-context docker-desktop`.
- **Port 30080 in use:** edit `nodePort` in `k8s/frontend-service.yaml`.
