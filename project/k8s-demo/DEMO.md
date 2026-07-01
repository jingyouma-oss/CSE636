# k8s-demo — Live Demo Runbook (Kubernetes & Node Operations)

A copy-pasteable, classroom-ready walkthrough that shows core Kubernetes
concepts on the running three-tier app. Each **Act** pairs the commands with
**what to point out** and the **real output** captured from a live run on Docker
Desktop / Rancher Desktop (single-node, k3s `v1.36.2`).

> **Before you present:** deploy once and confirm all pods are `Running`.
> ```bash
> cd project/k8s-demo
> make certs      # macOS only, and only behind a TLS-inspecting proxy (Zscaler etc.)
> make images     # build k8s-demo-backend:local + k8s-demo-frontend:local
> make deploy     # namespace first, then all manifests
> make status     # wait until db 1/1, backend 2/2, frontend 2/2
> ```
> Tear down at the end with `make clean`.

The demo tells one story: **each tier is one image → one Deployment → one
Service**, Kubernetes keeps them healthy, and you can scale, update, and survive
failures without downtime.

---

## Act 0 — Deploy and watch pods come up

```bash
make deploy
kubectl get pods -n k8s-demo -w        # Ctrl-C once everything is Running
```

**Point out:** pods move `Pending → ContainerCreating → Running`; the backend
only becomes `Ready` once its readiness probe (`/api/ready`, which pings
Postgres) passes — so pod *start order* doesn't matter.

---

## Act 1 — The core objects

```bash
kubectl get all -n k8s-demo
kubectl get pods -n k8s-demo -o wide
kubectl get svc,pvc,cm,secret -n k8s-demo
```

```text
NAME                           READY   STATUS    RESTARTS   AGE
pod/backend-589f5b5fb8-b6jns   1/1     Running   0          25m
pod/backend-589f5b5fb8-dh7j5   1/1     Running   0          25m
pod/db-78596cb47b-qmf6x        1/1     Running   0          25m
pod/frontend-677c778ff-4p6tl   1/1     Running   0          25m
pod/frontend-677c778ff-gl9jc   1/1     Running   0          25m

NAME               TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/backend    ClusterIP   10.43.154.52   <none>        8000/TCP       25m
service/db         ClusterIP   10.43.234.60   <none>        5432/TCP       25m
service/frontend   NodePort    10.43.49.113   <none>        80:30080/TCP   25m

NAME                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/backend    2/2     2            2           25m
deployment.apps/db         1/1     1            1           25m
deployment.apps/frontend   2/2     2            2           25m
```

**Point out:**
- The **Deployment → ReplicaSet → Pod** hierarchy (`get all` shows all three).
- `backend` and `db` are **ClusterIP** (no `EXTERNAL-IP`) — in-cluster only.
  Only `frontend` is a **NodePort** (`80:30080`) — the single external surface.
- `-o wide` shows every pod's **node** and **pod IP** (`10.42.0.x` on k3s).

---

## Act 2 — It actually works (all three tiers)

```bash
curl -s localhost:30080/api/health
curl -s localhost:30080/api/ready
curl -s localhost:30080/api/items
curl -s -X POST localhost:30080/api/items \
  -H 'Content-Type: application/json' -d '{"name":"added in class"}'
curl -s localhost:30080/api/items
```

```text
{"status":"ok"}
{"status":"ready","db":"reachable"}
{"items":[{"id":1,"name":"hello from postgres"},{"id":2,"name":"three-tier on kubernetes"}]}
{"id":3,"name":"added in class"}
{"items":[{"id":1,...},{"id":2,...},{"id":3,"name":"added in class"}]}
```

**Point out:** the request path — browser → **frontend NodePort** → Nginx
`/api` proxy → **`backend` Service** → FastAPI → **`db` Service** → Postgres.
`health` never touches the DB (liveness); `ready` does (readiness).

---

## Act 3 — Scaling

```bash
kubectl scale deploy/backend --replicas=4 -n k8s-demo
kubectl rollout status deploy/backend -n k8s-demo
kubectl get endpointslices -n k8s-demo -l kubernetes.io/service-name=backend \
  -o jsonpath='{range .items[*]}{.endpoints[*].addresses}{"\n"}{end}'
kubectl scale deploy/backend --replicas=2 -n k8s-demo
```

```text
deployment.apps/backend scaled
deployment "backend" successfully rolled out
["10.42.0.46"] ["10.42.0.47"] ["10.42.0.53"] ["10.42.0.52"]     # all 4 pods now behind the Service
```

**Point out:** the Service's **EndpointSlice** automatically tracks all four pod
IPs — scaling changes the load-balancing set with no config edits.

---

## Act 4 — Self-healing (the most important act)

### 4a — Kill *all* replicas (shows what NOT to do)

```bash
kubectl delete pod -l app=backend -n k8s-demo
curl -s localhost:30080/api/health          # during the churn
```

```text
pod "backend-589f5b5fb8-b6jns" deleted
pod "backend-589f5b5fb8-dh7j5" deleted
<html><head><title>504 Gateway Time-out</title></head>...   # ← brief outage!
```

**Point out:** deleting *every* matching pod at once leaves the Service with
**zero endpoints** for a few seconds → real `504`s until Kubernetes reschedules.

### 4b — Kill *one* replica (true zero-downtime)

```bash
ONE=$(kubectl get pod -n k8s-demo -l app=backend -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod "$ONE" -n k8s-demo
for i in $(seq 1 10); do
  curl -s -o /dev/null -w "attempt $i: HTTP %{http_code}\n" localhost:30080/api/health
  sleep 0.5
done
```

```text
attempt 1: HTTP 200
attempt 2: HTTP 200
...
attempt 10: HTTP 200        # survivor keeps serving while the killed pod is replaced
```

**Point out:** **this is why you run more than one replica.** With a survivor,
the Deployment recreates the dead pod while traffic keeps flowing — 10/10 `200`.

---

## Act 5 — Rolling update + rollback

```bash
kubectl set env deploy/backend -n k8s-demo DEMO_RELEASE=v2   # forces a new rollout
kubectl rollout status deploy/backend -n k8s-demo
kubectl rollout history deploy/backend -n k8s-demo
kubectl get rs -n k8s-demo -l app=backend
kubectl rollout undo deploy/backend -n k8s-demo             # roll back
```

```text
deployment.apps/backend env updated
deployment "backend" successfully rolled out

REVISION  CHANGE-CAUSE
1         <none>
2         <none>

NAME                 DESIRED   CURRENT   READY   AGE
backend-54dff94bf6   2         2         2       13s     # new ReplicaSet
backend-589f5b5fb8   0         0         0       28m     # old ReplicaSet, scaled to 0

deployment.apps/backend rolled back
```

**Point out:** a rollout creates a **new ReplicaSet** and shifts pods over
gradually (old scales to 0, new to 2) — never all-down. `rollout undo` flips
back instantly. Contrast the backend's default **RollingUpdate** with the DB's
**`Recreate`** strategy (a single pod on an RWO volume can't overlap).

> A `Warning` about the `last-applied-configuration` annotation is normal after
> `rollout undo` on an `apply`-managed Deployment — harmless for the demo.

---

## Act 6 — Persistence (the PVC)

```bash
curl -s localhost:30080/api/items            # note id:3 exists
kubectl delete pod -l app=db -n k8s-demo     # kill Postgres
kubectl rollout status deploy/db -n k8s-demo
sleep 4
curl -s localhost:30080/api/items            # id:3 still there
```

```text
{"items":[{"id":1,...},{"id":2,...},{"id":3,"name":"added in class"}]}
pod "db-78596cb47b-qmf6x" deleted
deployment "db" successfully rolled out
{"items":[{"id":1,...},{"id":2,...},{"id":3,"name":"added in class"}]}   # survived!
```

**Point out:** the pod is disposable; the **PersistentVolumeClaim** (`db-pvc`,
`Bound`, StorageClass `local-path` on k3s / `hostpath` on Docker Desktop)
outlives it, so the data persists across restarts.

---

## Act 7 — Node operations

```bash
kubectl get nodes -o wide
kubectl describe node <node-name>            # e.g. lima-rancher-desktop / docker-desktop
kubectl top node
kubectl top pods -n k8s-demo
kubectl cordon <node-name>                   # mark unschedulable
kubectl get nodes
kubectl uncordon <node-name>                 # restore
```

```text
NAME                   STATUS   ROLES                  VERSION        CONTAINER-RUNTIME
lima-rancher-desktop   Ready    control-plane,master   v1.36.2+k3s1   docker://29.1.3

Capacity:
  cpu:                4
Conditions:
  MemoryPressure   False   KubeletHasSufficientMemory
  DiskPressure     False   KubeletHasNoDiskPressure
  PIDPressure      False   KubeletHasSufficientPID
  Ready            True    KubeletReady

NAME                   CPU(cores)   CPU(%)   MEMORY(bytes)   MEMORY(%)
lima-rancher-desktop   179m         4%       1944Mi          8%

NAME                       CPU(cores)   MEMORY(bytes)
backend-589f5b5fb8-7822w   4m           34Mi
db-78596cb47b-hxmlh        8m           18Mi
frontend-677c778ff-4p6tl   1m           5Mi

node/lima-rancher-desktop cordoned
lima-rancher-desktop   Ready,SchedulingDisabled   control-plane,master
node/lima-rancher-desktop uncordoned
lima-rancher-desktop   Ready                      control-plane,master
```

**Point out:**
- `describe node` shows **Capacity vs Allocatable**, node **Conditions** (the
  health signals kubelet reports), and the pods scheduled on it with their
  resource requests.
- `kubectl top` needs **metrics-server** — k3s ships it by default.
- `cordon` marks the node **`SchedulingDisabled`** (no *new* pods land there);
  `uncordon` restores it.
- **Single-node caveat:** the control plane and your workloads share one node.
  `kubectl drain` would *evict everything* (there's nowhere else to reschedule),
  so mention it as a concept rather than running it in class — or run it and
  immediately `uncordon`. On a multi-node cluster, drain safely moves pods to
  other nodes (the basis of rolling node upgrades).

---

## Teardown

```bash
make clean       # deletes the k8s-demo namespace and every resource in it
```

**Point out:** deleting the **namespace** cascades to all Deployments, Services,
Pods, ConfigMaps, the Secret, and the PVC — one command, clean slate.

---

## Suggested timing (≈15–20 min live block)

| Act | Minutes | Skip if short on time? |
|---|---|---|
| 0–2 Deploy + objects + it-works | 5 | No — this is the payoff |
| 3 Scale | 2 | Optional |
| 4 Self-healing (do **4b**) | 3 | No — the key lesson |
| 5 Rolling update + rollback | 3 | Optional |
| 6 Persistence | 2 | No — proves stateful survives |
| 7 Node operations | 3–5 | Trim to `get/describe/top` if short |
