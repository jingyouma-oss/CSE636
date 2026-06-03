# CSE 636 — Kubernetes

### Qingsong Zhang, Ph.D.
### October 2025

---

## What is Kubernetes

Kubernetes is an orchestration framework for Docker containers which helps expose containers as services to the outside world.

For example, you can have two services:

- One service would contain nginx and MongoDB.
- Another service would contain nginx and Redis.

Each service can have an IP or service point which can be connected by other applications. Kubernetes is then used to manage these services.

---

## Kubernetes Components

### Control Plane

- **kube-apiserver** — the core component server that exposes the Kubernetes HTTP API.
- **etcd** — consistent and highly-available key-value store for all API server data.
- **kube-scheduler** — looks for pods not yet bound to a node, and assigns each Pod to a suitable node.
- **kube-controller-manager** — runs controllers to implement Kubernetes API behavior.
- **cloud-controller-manager** (optional) — integrates with underlying cloud provider(s).

### Node Components

- **kubelet** — ensures that Pods are running, including their containers.
- **kube-proxy** (optional) — maintains network rules on nodes to implement services.
- **container runtime** — software responsible for running containers.

### Addons

- **DNS** — for cluster-wide DNS resolution.
- **Web UI (dashboard)** — for cluster management via a web interface.
- **Container Resource Monitoring** — for collecting and storing container metrics.
- **Cluster-level Logging** — for saving container logs to a central log store.

---

## What is Kubernetes — Minions, Pods, and Containers

- The **minion** is the node on which all the services run. You can have many minions running at one point in time.
- Each minion will host one or more **POD**. Each POD is like hosting a service.
- Each POD then contains the **Docker containers**. Each POD can host a different set of Docker containers.
- The **proxy** is then used to control the exposing of these services to the outside world.

---

## What is Kubernetes — Pods

Pods are the smallest deployable units of computing that you can create and manage in Kubernetes.

A Pod (as in a pod of whales or pea pod) is a group of one or more containers, with shared storage and network resources, and a specification for how to run the containers.

- A Pod's contents are always co-located and co-scheduled, and run in a shared context.
- A Pod models an application-specific "logical host": it contains one or more application containers which are relatively tightly coupled.

> In non-cloud contexts, applications executed on the same physical or virtual machine are analogous to cloud applications executed on the same logical host.

---

## Kubernetes Architecture

- **etcd** — a highly available key-value store used for storing shared configuration and service discovery. Here the various applications will be able to connect to the services via the discovery service.
- **Flannel** — a backend network which is required for the containers.
- **kube-apiserver** — an API which can be used to orchestrate the Docker containers.
- **kube-controller-manager** — used to control the Kubernetes services.
- **kube-scheduler** — used to schedule the containers on hosts.
- **kubelet** — used to control the launching of containers via manifest files.
- **kube-proxy** — used to provide network proxy services to the outside world.

---

## Kubernetes Architecture

> *Diagram: Kubernetes architecture overview.*

---

## Docker and Kubernetes

Kubernetes and Docker work together to simplify application deployment and management.

- **Docker** packs an application and its dependencies into a portable container that guarantees the same environment at development, staging, testing, and production.
- **Kubernetes** orchestrates all these Docker containers through automation — tasks such as scaling, load balancing, self-healing, and many more.

Kubernetes clusters comprise worker nodes on which the Docker containers run, and a master node managing the state of the cluster.

> By defining desired states of applications in YAML files, Kubernetes continuously monitors the Deployment while adhering to the specifications, therefore providing high availability and efficient resource utilization.

---

## POD Creation

> *Diagram: Pod creation workflow.*
