# k8s-demo — a 3-tier app on Docker Desktop Kubernetes

A class demo: **React frontend → FastAPI backend → Postgres database**, each in
its own container, each one Kubernetes Deployment + Service, all in a `k8s-demo`
namespace on your Mac's local single-node Kubernetes — **Docker Desktop** or
**Rancher Desktop** both work.

![Architecture: a Mac browser hits the frontend NodePort on localhost:30080; inside the k8s-demo namespace, the Frontend Deployment (React + Nginx, 2 replicas) reverse-proxies /api to the Backend Deployment (FastAPI, 2 replicas) via the backend ClusterIP Service on port 8000; the backend talks to the Database Deployment (Postgres, 1 replica) via the db ClusterIP Service on 5432; Postgres persists to a 1Gi PersistentVolumeClaim; a Secret supplies the DB password and ConfigMaps supply non-secret settings and the Nginx proxy config.](images/architecture.svg)

## Prerequisites

A local single-node Kubernetes on your Mac. Either works:

- **Docker Desktop** — Settings → Kubernetes → Enable Kubernetes → Apply & restart.
  Then: `kubectl config use-context docker-desktop`.
- **Rancher Desktop** — Preferences → Kubernetes → Enable Kubernetes. Use the
  **dockerd (moby)** container engine (Preferences → Container Engine) so
  `docker build` images are visible to the cluster. Then:
  `kubectl config use-context rancher-desktop`.

> **Rancher Desktop on the `containerd` engine instead?** k3s then reads images
> from containerd's `k8s.io` namespace, which `docker build` doesn't populate.
> Either switch the engine to dockerd (moby), or build with nerdctl into that
> namespace: `nerdctl --namespace k8s.io build -t k8s-demo-backend:local ./backend`
> (and likewise for the frontend). `make images` uses `docker build`, which is
> correct for Docker Desktop and Rancher Desktop's moby engine.

## Quickstart

```bash
cd project/k8s-demo
make check     # confirms Docker Desktop K8s is active
make certs     # (macOS, optional) only if you're behind a TLS-inspecting proxy — see below
make images    # build k8s-demo-backend:local and k8s-demo-frontend:local
make deploy    # create the namespace and apply all manifests
make status    # wait until every pod is Running / Ready
make open      # opens http://localhost:30080
```

Add an item in the UI — it round-trips React → Nginx `/api` proxy → FastAPI →
Postgres and back.

> 🎬 **Presenting in class?** [`DEMO.md`](DEMO.md) is a copy-pasteable, annotated
> runbook (scaling, self-healing, rolling updates, persistence, and node
> operations) with real captured output and suggested timing.

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

- **`make images` fails with `CERTIFICATE_VERIFY_FAILED` / `unable to get local
  issuer certificate`:** you're on a network with a TLS-inspecting proxy (e.g.
  Zscaler) whose root CA the base images don't trust. On macOS, run `make certs`
  once (it exports your Keychain CA bundle into the build contexts, gitignored),
  then `make images` again. The Dockerfiles trust the bundle only if present, so
  builds still work on an open network without it.
- **`ErrImageNeverPull` / `ImagePullBackOff`:** run `make images` first; the
  manifests never pull (`IfNotPresent` + `:local`). On **Rancher Desktop**, make
  sure the container engine is **dockerd (moby)** — on the containerd engine,
  `docker build` images aren't visible to k3s (see Prerequisites).
- **PVC stuck `Pending`:** both runtimes ship a default StorageClass — `hostpath`
  on Docker Desktop, `local-path` on Rancher Desktop (`kubectl get sc`). With
  `local-path`'s `WaitForFirstConsumer` mode the PVC stays `Pending` until the
  `db` pod is scheduled — that's expected, not an error.
- **`make check` fails:** enable Kubernetes in Docker Desktop or Rancher Desktop
  and switch context (`kubectl config use-context docker-desktop` or
  `rancher-desktop`).
- **`localhost:30080` doesn't respond:** both runtimes forward NodePorts to
  localhost, but if it doesn't, forward it yourself:
  `kubectl port-forward -n k8s-demo svc/frontend 30080:80`.
- **Port 30080 in use:** edit `nodePort` in `k8s/frontend-service.yaml`.
