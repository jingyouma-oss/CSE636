Docker 101

Agenda
Containers are NOT VMs
Working with Docker (Build, Ship, Run)
But Why?
Getting started
Q & A

Containers are not VMs

Docker containers are NOT VMs
• Easy connection to make
• Fundamentally different architectures
• Fundamentally different benefits
4

VMs
5

Containers
6

Docker + Windows Server = Windows Containers
Native Windows containers powered by
Docker Engine
Windows kernel engineered with new
App App App primitives to support containers
Deep integration with 2+ years of engineering
Bins/Libs Bins/Libs Bins/Libs
collaboration in Docker Engine and Windows
Server
Docker Engine
Microsoft is top 5 Docker open source project
Windows Server 2016
contributor and a Docker maintainer
Infrastructure

They’re different, not mutually exclusive
8

Variables to Consider
• Performance
• Security
• Scalability
• Existing Skillsets
• Costs
• Etc.
http://people-equation.com/do-your-words-encourage-or-deflate/math-equation_chalkboard/

Container Consolidation Testing
How can containers help organizations optimize hardware utilization?
• Testing done by HPE, Docker and Industry Consultant
• Components:
− Docker CS Engine 1.12.3
− VMware ESXi 6
− SysBench 1.0 (Nov 2016)
− RHEL 7.2
− HPE ProLiant DL360 Gen 9 servers with HPE 3PAR StorServ 8200 SSD
Storage
10

Need to replace this graphic w/
Testing Scenarios
the one w/ 8 boxes
Measure SysBench performance across 3 configurations
| Scenario 1:  | Scenario 2:          | Scenario 3:                |
| ------------ | -------------------- | -------------------------- |
| 8 VMs        | 1 VM w/ 8 Containers | 8 Containers on Bare Metal |
11

Results
Moving from VMs to containers increases performance 27% to 46%
Results are after VM and Container Tuning
12

Additional Savings
Docker allowed for savings in memory and disk as well
13

Key Learnings
Docker containers increase performance and flexiblity
| 1   | • Plan for Higher Density |     |
| --- | ------------------------- | --- |
|     | • Bare Metal or Bigger    |     |
2
VMs
| 3   | •   | Tune To Optimize |
| --- | --- | ---------------- |
14

Build, Ship, and Run

Put it all together: Build, Ship, Run Workflow
Developers  IT Operations
| BUILD  | SHIP  | RUN  |
| ------ | ----- | ---- |
Development Environments Create & Store Images Deploy, Manage, Scale
17

The building block: Docker Engine 1.12
Built in orchestration with scheduling, networking and scheduling
• Powerful yet simple, built in
Docker Engine
orchestration
• Declarative app services
Orchestration Components
• Built in container centric
Swarm Mode Swarm Mode
networking
Manager Worker
• Built in default security
Certificate Volumes
TLS
Authority
• Extensible with plugins, drivers
and open APIs
Load Service
Plugins
Balancing Discovery
Distributed Container
Networking
store Runtime

Docker Datacenter platform
Operating
Systems CI/CD Images Networking Volumes Config Mgt Monitoring Logging ..more..
Docker Datacenter
Docker Universal Control Plane
Integrated
Security
Docker Trusted Registry
Docker Engine
Container runtime, orchestration, networking, volumes, plugins
Public Cloud Virtualization Physical

Docker Datacenter Architecture
BYO TCP Load Balancer
Raft consensus group
Internal distributed store
| UCP Manager | UCP Manager | UCP Manager |
| ----------- | ----------- | ----------- |

Docker Datacenter Architecture
Admin / User
Deploy / manage
BYO TCP Load Balancer
Raft consensus group
Internal distributed store
| UCP Manager | UCP Manager | UCP Manager |        |        |
| ----------- | ----------- | ----------- | ------ | ------ |
|             | UCP         | UCP         | UCP    | UCP    |
|             | Worker      | Worker      | Worker | Worker |

Docker Datacenter Architecture
Admin / User
Deploy / manage
Logging
BYO TCP Load Balancer
Monitoring
Raft consensus group
|     |     | Internal distributed store |     |     |     | LDAP/AD |
| --- | --- | -------------------------- | --- | --- | --- | ------- |
push / pull
|     |     | UCP Manager | UCP Manager | UCP Manager |     | External CA |
| --- | --- | ----------- | ----------- | ----------- | --- | ----------- |
Image
Storage
BYO TCP Load Balancer
| DTR Replica  | DTR Replica  | DTR Replica  | UCP    | UCP    | UCP    | UCP    |
| ------------ | ------------ | ------------ | ------ | ------ | ------ | ------ |
| Worker       | Worker       | Worker       | Worker | Worker | Worker | Worker |
Image Registry

Some Docker vocabulary
Docker Image
The basis of a Docker container. Represents a full application
Docker Container
The standard unit in which the application service resides and executes
Docker Engine
Creates, ships and runs Docker containers deployable on a physical or
virtual, host locally, in a datacenter or cloud service provider
Registry Service (Docker Hub or Docker Trusted Registry)
Cloud or server based storage and distribution service for your images
23

Basic Docker Commands
$ docker pull mikegcoleman/catweb:1.0
$ docker images
$ docker run –d –p 5000:5000 –-name catweb mikegcoleman/catweb:latest
$ docker ps
$ docker stop catweb (or <container id>)
$ docker rm catweb (or <container id>)
$ docker rmi mikegcoleman/catweb:latest (or <image id>)
$ docker build –t mikegcoleman/catweb:2.0 .
$ docker push mikegcoleman/catweb:2.0

Dockerfile – Linux Example
• Instructions on how
to build a Docker
image
• Looks very similar
to “native”
commands
• Important to
optimize your
Dockerfile
25

Dockerfile – Windows Example

Demo
Build, Ship, and Run

But Why?

Enterprises are looking to Docker for critical transformations
3 out 4
App
Modernization
Top initiatives revolve
around applications
80% 44%
Cloud DevOps
Docker is central to Looking to adopt DevOps
cloud strategy
Docker Survey: State of App development : Q1 - 2016 State of App development Survey: Q1 2016

Docker delivers speed, flexibility and savings
+ +
| Agility                        | Portability              | Control |
| ------------------------------ | ------------------------ | ------- |
| 13X                            | 41%                      | 62%     |
| Move workloads across private/ | Report reduction in MTTR |         |
More software releases
public clouds
| 65%   |     | 10X   |
| ----- | --- | ----- |
Eliminate
“works on my machine”
Cost reduction in maintaining
Reduction in developer
|     | issues  | existing applications |
| --- | ------- | --------------------- |
onboarding time
30
State of App development Survey:  Q1 2016, Cornell University case study

One platform delivers one journey for all applications
1
Containerize Legacy Applications
Lift and shift for portability and efficiency
Transform Legacy to Microservices
2
Look for shared services to transform
Accelerate New Applications
3
Greenfield innovation

Containers in production with Docker Datacenter
• Enterprise container
orchestration, management
CI/CD Images Networking Volumes Config Mgt Monitoring Logging ..more..
and security for dev and ops
Integrated Security
• Available today for Linux
Docker Universal Control Plane
environments
Docker Trusted Registry • Q4 2016 beta for Windows
environments
Docker Engine
Physical Virtual Public Cloud

Getting Started

Docker on Linux
• Create a Linux VM (or use physical), and install Docker
−Requires kernel 3.10
• Stable builds
−curl –sSL https://get.docker.com/ | sh
• Test and experimental builds
−curl –sSL https://test.docker.com/ | sh
−curl –sSL https://experimental.docker.com/ | sh
• Can also manually install (see docs)
34

Docker for Windows / Mac
• Currently in public beta
• Easy to install: Get up and running on Docker in minutes
• Leverages Hyper-V (Windows) or xhyv (Mac)
− Docker for Windows requires Windows Pro 10, Enterprise, or Education
• Full API / CLI compatibility
• OS integration for increased stability and speed

Docker for Azure / AWS
• Currently in public beta
− https://beta.docker.com/
• Easily deploy Docker 1.12 Swarm clusters (Linux)
• Scale up and down easily
• Integrate with underlying platform (i.e. load balancers)

Walk, Jog, Run
Walk:
• Setup your preferred Docker environment
• Fire up some prebuilt images (nginx, hello-world, mikegcoleman/catweb)
Jog:
• Pick a well documented solution (Wordpress, Jenkins, etc)
• Build it for yourself (blogs are your friend)
Run:
• Extend one your Walk solution or Dockerize an existing project
• Build your own Dockerfiles
• Experiment with Docker Compose and Swarm Mode

Hands-on Labs
http://github.com/docker/labs

Thank You.
Questions?