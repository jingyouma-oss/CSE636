# Docker 101

---

## Agenda

- Containers are NOT VMs
- Working with Docker (Build, Ship, Run)
- But Why?
- Getting Started
- Q & A

---

## Docker Containers Are NOT VMs

- Easy connection to make
- Fundamentally different architectures
- Fundamentally different benefits

---

## VMs

> *Diagram: a virtual-machine stack — each app runs on its own guest OS, all sitting on a hypervisor above the host infrastructure.*

---

## Containers

> *Diagram: a container stack — multiple apps with their own bins/libs share a single host OS kernel via the Docker Engine, with no per-app guest OS.*

---

## Docker + Windows Server = Windows Containers

- **Native Windows containers** powered by Docker Engine
- Windows kernel engineered with new primitives to support containers
- Deep integration from 2+ years of engineering collaboration in Docker Engine and Windows Server
- Microsoft is a top-5 Docker open source project contributor and a Docker maintainer

> *Diagram: app + bins/libs layers running on the Docker Engine, atop Windows Server 2016 and the underlying infrastructure.*

---

## They're Different, Not Mutually Exclusive

VMs and containers can be used together. Which to use depends on several variables.

**Variables to consider:**

- Performance
- Security
- Scalability
- Existing skillsets
- Costs
- Etc.

---

## Container Consolidation Testing

How can containers help organizations optimize hardware utilization?

- Testing done by HPE, Docker, and an industry consultant
- **Components:**
  - Docker CS Engine 1.12.3
  - VMware ESXi 6
  - SysBench 1.0 (Nov 2016)
  - RHEL 7.2
  - HPE ProLiant DL360 Gen 9 servers with HPE 3PAR StoreServ 8200 SSD Storage

---

## Testing Scenarios

Measure SysBench performance across 3 configurations:

| Scenario 1 | Scenario 2 | Scenario 3 |
| ---------- | ---------- | ---------- |
| 8 VMs | 1 VM w/ 8 Containers | 8 Containers on Bare Metal |

---

## Results

- Moving from VMs to containers increases performance **27% to 46%**
- Results are after VM and container tuning

---

## Additional Savings

- Docker allowed for savings in memory and disk as well

---

## Key Learnings

Docker containers increase performance and flexibility.

| # | Learning |
| - | -------- |
| 1 | Plan for higher density |
| 2 | Bare metal or bigger VMs |
| 3 | Tune to optimize |

---

## Build, Ship, and Run

---

## Put It All Together: Build, Ship, Run Workflow

| Build | Ship | Run |
| ----- | ---- | --- |
| Developers | | IT Operations |
| Development environments | Create & store images | Deploy, manage, scale |

---

## The Building Block: Docker Engine 1.12

Built-in orchestration with scheduling and networking.

- **Powerful yet simple**, built-in orchestration
- Declarative app services
- Built-in container-centric networking
- Built-in default security
- Extensible with plugins, drivers, and open APIs

**Orchestration components:**

- Swarm Mode Manager / Swarm Mode Worker
- Certificate Authority (TLS)
- Volumes
- Load Balancing
- Service Discovery
- Plugins
- Distributed store
- Container Runtime

---

## Docker Datacenter Platform

A platform that integrates security across the stack.

- **Docker Universal Control Plane** — cluster management
- **Docker Trusted Registry** — image storage
- **Docker Engine** — container runtime, orchestration, networking, volumes, plugins

**Spans:** operating systems, CI/CD, images, networking, volumes, config management, monitoring, logging, and more.

**Runs on:** public cloud, virtualization, and physical infrastructure.

---

## Docker Datacenter Architecture

> *Diagram: a BYO TCP load balancer fronts three UCP Manager nodes that form a Raft consensus group backed by an internal distributed store.*

---

## Docker Datacenter Architecture (continued)

> *Diagram: an admin/user deploys and manages through a BYO TCP load balancer to three UCP Manager nodes (Raft consensus group, internal distributed store), which in turn manage a pool of UCP Worker nodes.*

---

## Docker Datacenter Architecture (continued)

> *Diagram: the full platform — admin/user traffic enters via a BYO TCP load balancer to three UCP Managers (Raft consensus group, internal distributed store) managing UCP Workers; a second load balancer fronts DTR Replicas for image storage with push/pull access; integrated with logging, monitoring, LDAP/AD, an external CA, and an image registry.*

---

## Some Docker Vocabulary

- **Docker Image** — the basis of a Docker container; represents a full application.
- **Docker Container** — the standard unit in which the application service resides and executes.
- **Docker Engine** — creates, ships, and runs Docker containers; deployable on a physical or virtual host, locally, in a datacenter, or on a cloud service provider.
- **Registry Service** (Docker Hub or Docker Trusted Registry) — cloud- or server-based storage and distribution service for your images.

---

## Basic Docker Commands

```bash
$ docker pull mikegcoleman/catweb:1.0
$ docker images
$ docker run -d -p 5000:5000 --name catweb mikegcoleman/catweb:latest
$ docker ps
$ docker stop catweb           # (or <container id>)
$ docker rm catweb             # (or <container id>)
$ docker rmi mikegcoleman/catweb:latest   # (or <image id>)
$ docker build -t mikegcoleman/catweb:2.0 .
$ docker push mikegcoleman/catweb:2.0
```

---

## Dockerfile — Linux Example

- Instructions on how to build a Docker image
- Looks very similar to "native" commands
- Important to optimize your Dockerfile

> *Diagram: a sample Linux Dockerfile listing build instructions.*

---

## Dockerfile — Windows Example

> *Diagram: a sample Windows Dockerfile listing build instructions.*

---

## Demo: Build, Ship, and Run

---

## But Why?

---

## Enterprises Are Looking to Docker for Critical Transformations

- **3 out of 4** — top initiatives revolve around application modernization.
- **80%** — Docker is central to cloud strategy.
- **44%** — looking to adopt DevOps.

> Source: Docker Survey, State of App Development, Q1 2016.

---

## Docker Delivers Speed, Flexibility, and Savings

| Agility | Portability | Control |
| ------- | ----------- | ------- |
| **13X** more software releases | **41%** move workloads across private/public clouds | **62%** report reduction in MTTR |
| **65%** reduction in developer onboarding time | **10X** eliminate "works on my machine" issues | Cost reduction in maintaining existing applications |

> Source: State of App Development Survey, Q1 2016; Cornell University case study.

---

## One Platform Delivers One Journey for All Applications

1. **Containerize legacy applications** — lift and shift for portability and efficiency.
2. **Transform legacy to microservices** — look for shared services to transform.
3. **Accelerate new applications** — greenfield innovation.

---

## Containers in Production with Docker Datacenter

- Enterprise container orchestration, management, and security for dev and ops
- Available today for Linux environments
- Q4 2016 beta for Windows environments

**Platform layers:**

- **Docker Universal Control Plane** with integrated security
- **Docker Trusted Registry**
- **Docker Engine**

**Spans:** CI/CD, images, networking, volumes, config management, monitoring, logging, and more.

**Runs on:** physical, virtual, and public cloud.

---

## Getting Started

---

## Docker on Linux

- Create a Linux VM (or use physical), and install Docker
  - Requires kernel 3.10
- Can also manually install (see docs)

```bash
# Stable builds
curl -sSL https://get.docker.com/ | sh

# Test and experimental builds
curl -sSL https://test.docker.com/ | sh
curl -sSL https://experimental.docker.com/ | sh
```

---

## Docker for Windows / Mac

- Currently in public beta
- Easy to install: get up and running on Docker in minutes
- Leverages Hyper-V (Windows) or xhyve (Mac)
  - Docker for Windows requires Windows 10 Pro, Enterprise, or Education
- Full API / CLI compatibility
- OS integration for increased stability and speed

---

## Docker for Azure / AWS

- Currently in public beta
  - https://beta.docker.com/
- Easily deploy Docker 1.12 Swarm clusters (Linux)
- Scale up and down easily
- Integrate with the underlying platform (e.g. load balancers)

---

## Walk, Jog, Run

**Walk:**

- Set up your preferred Docker environment
- Fire up some prebuilt images (nginx, hello-world, mikegcoleman/catweb)

**Jog:**

- Pick a well-documented solution (WordPress, Jenkins, etc.)
- Build it for yourself (blogs are your friend)

**Run:**

- Extend one of your Walk solutions or Dockerize an existing project
- Build your own Dockerfiles
- Experiment with Docker Compose and Swarm Mode

---

## Hands-on Labs

- http://github.com/docker/labs

---

## Thank You

Questions?
