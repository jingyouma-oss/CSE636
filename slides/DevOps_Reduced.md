DevOps Tutorial

Fall, 2025

Qingsong Zhang, Ph. D.

Overview of
DevOps

01

Introduction to DevOps

02 DevOps Lifecycle

03 CI/CD Concepts

04 Key DevOps Tools

05

Cloud, Culture & Best
Practices

What is DevOps?

Definition
DevOps is a set of practices that combines software development (Dev) and IT
operations (Ops). Its goal is to shorten the development lifecycle while delivering
features, fixes, and updates quickly and reliably.

Key Idea

DevOps emphasizes collaboration between developers, operations teams, and
other stakeholders to enable continuous integration, delivery, and monitoring.

Outcome

Organizations adopting DevOps achieve faster releases, higher-quality software,
and improved customer satisfaction.

Why DevOps?

Traditional Challenges

In traditional models, development and operations often worked in
silos, causing delays, miscommunication, and integration issues.

DevOps Benefits

DevOps solves these problems by fostering collaboration,
automating processes, and enabling faster feedback loops.

Student Relevance

Understanding DevOps is essential for modern IT careers, as most
organizations rely on these practices to remain competitive.

Core Principles of DevOps

Collaboration

Breaking down silos between development, operations, QA, and
business teams to improve communication and shared goals.

Automation

Automating repetitive tasks such as builds, tests, and deployments to
reduce errors and speed up delivery.

Continuous Processes
DevOps emphasizes continuous integration, continuous delivery, and
continuous monitoring to maintain rapid and reliable software
development.

DevOps Culture

Mindset Shift

DevOps is not only about tools; it represents a cultural shift where
teams share responsibility for both development and operations.

Collaboration & Trust
Strong communication, mutual trust, and shared accountability
between cross-functional teams are the foundation of DevOps
culture.

Learning & Improvement

Continuous learning, experimentation, and feedback loops help
organizations adapt and improve processes over time.

Roles and Responsibilities of a DevOps
Engineer

Project Management
In addition to monitoring, regulating and updating tools, DevOps
engineers need to track the cost, benefits, risk and various projects
Development

DevOps engineers are required to design, develop and deploy
automated modules within production environments.
Communication
DevOps engineers need to work and coordinate with different
departments and provide support, which requires communication skills

Interpersonal skills
DevOps engineers should be approachable, organized, and
foresighted team players with an ability to multitask.

Troubleshooting
One of the major responsibilities of DevOps engineers is to
troubleshoot and come up with solutions for various errors.

DevOps Lifecycle Preview

Plan & Code

Teams start by planning features and writing code with version
control systems like Git.

Build & Test

Code is built into applications and tested automatically to ensure
quality and functionality.

Release & Monitor

Software is released into production, monitored for performance, and
continuously improved based on feedback.

DevOps Lifecycle Overview

Purpose
The DevOps lifecycle represents the continuous process of software
development and delivery, ensuring rapid, reliable, and collaborative
workflows.

Stages

It includes planning, coding, building, testing, releasing, deploying,
operating, and monitoring, all connected in a continuous cycle.

Key Idea

Every stage feeds into the next, creating a feedback-driven system that
allows organizations to improve continuously.

DevOps Lifecycle Diagram

Planning Stage

Goal

In this stage, teams gather requirements, set priorities, and plan
features or fixes to be developed.

Practices

Agile methods, sprint planning, and backlog refinement are
commonly used during the planning phase.

Tools

Popular tools include Jira, Trello, or Azure Boards for managing
tasks and user stories.

Coding Stage

Goal

In this stage, developers write and manage code, ensuring it is
versioned and collaborative.

Practices

Teams follow coding standards, perform code reviews, and use
branching strategies for better collaboration.

Tools

Git, GitHub, GitLab, and Bitbucket are widely used for version control
and collaborative coding.

Building Stage

Goal

The build stage transforms source code into executable applications
by compiling, packaging, or containerizing.

Practices

Build automation ensures consistency and repeatability. Continuous
Integration (CI) tools help streamline this process.

Tools

Maven, Gradle, Jenkins, and Docker are commonly used to
automate and manage builds.

Testing Stage

Goal

The testing stage validates software quality by detecting bugs,
performance issues, and security flaws before release.

Practices

Automated testing, unit tests, integration tests, and continuous
testing pipelines are widely adopted.

Tools

Selenium, JUnit, TestNG, and JMeter are commonly used for
functional and performance testing in DevOps.

Release Stage

Goal

The release stage focuses on preparing and approving software for
deployment into production environments.

Practices

Release management includes versioning, change approvals, and
ensuring deployment readiness.

Tools

Jenkins, GitLab CI/CD, and Spinnaker are widely used to coordinate
and automate release pipelines.

Deployment Stage

Goal

The deployment stage delivers software into production
environments where it becomes accessible to end users.

Practices

Automated deployments, blue-green deployments, and canary
releases reduce downtime and risk.

Tools

Kubernetes, Docker Swarm, and Ansible are commonly used to
automate and orchestrate deployments.

Operations Stage

Goal

The operations stage focuses on managing and maintaining
applications in production environments.

Practices

Infrastructure as Code (IaC), configuration management, and
proactive monitoring are critical practices.

Tools

Tools like Ansible, Puppet, Chef, and Terraform help automate and
manage infrastructure at scale.

Monitoring Stage

Goal

The monitoring stage ensures applications and infrastructure are
continuously observed for performance, availability, and security.

Practices

Monitoring includes real-time alerts, logging, and proactive incident
response to minimize downtime.

Tools

Prometheus, Grafana, ELK Stack, and Datadog are commonly used
for monitoring and visualization.

Continuous Feedback Loop

Overview of CI/CD

Definition

CI/CD stands for Continuous Integration and Continuous Delivery/
Deployment. It automates software integration, testing, and release.

Purpose

The goal of CI/CD is to deliver software quickly, safely, and reliably
by automating development and operations tasks.

Key Idea

Every code change is integrated, tested, and delivered through
automated pipelines, reducing human errors and delays.

Continuous Integration (CI)

Definition
Continuous Integration is the practice of frequently merging code
changes into a shared repository, followed by automated builds and
tests.

Practices

CI involves automated testing, linting, and code quality checks to
ensure every commit is stable and functional.

Tools

Popular CI tools include Jenkins, GitHub Actions, GitLab CI, and
CircleCI.

CI Tools & Examples

Jenkins

An open-source automation server widely used for building, testing,
and integrating code.

GitHub Actions & GitLab CI

Provide integrated CI/CD features within code repositories, making
automation simpler and faster.

Other Tools

CircleCI, Travis CI, and Bamboo are also popular for managing CI
pipelines.

Continuous Delivery (CD)

Definition
Continuous Delivery ensures that code changes are automatically
prepared for release to production through automated testing and
staging.

Practices

Includes automated deployment pipelines, release approvals, and
frequent production-ready builds.

Tools

Jenkins, Spinnaker, and ArgoCD are often used to implement
continuous delivery pipelines.

Continuous Deployment

Definition
Continuous Deployment goes one step further than Continuous
Delivery by automatically deploying every code change to production
without manual approval.

Practices

Requires high test coverage, strong monitoring, and rollback
mechanisms to ensure safe, automated releases.

Tools

Kubernetes, ArgoCD, and Spinnaker are widely used to support
continuous deployment strategies.

Benefits of CI/CD

Speed

CI/CD pipelines accelerate the software development lifecycle,
reducing time-to-market for new features.

Quality

Automated testing and integration ensure higher software quality and
fewer production issues.

Reliability

Frequent releases and continuous monitoring make software more
reliable and stable for end users.

CI/CD Pipeline Diagram

CI/CD in AWS

Challenges in CI/CD

Complexity

Setting up and maintaining CI/CD pipelines can be complex,
requiring integration of many tools and processes.

Testing Coverage

Automated tests must be comprehensive; gaps in coverage can
allow bugs into production.

Cultural Barriers

Successful CI/CD adoption depends on strong collaboration and
cultural alignment across teams.

Overview of DevOps Tools

Purpose

DevOps tools support automation, collaboration, and monitoring
across the entire software development lifecycle.

Categories
Key categories include version control, CI/CD, containerization,
configuration management, infrastructure as code, monitoring, and
collaboration.

Integration

These tools are often integrated into toolchains, ensuring seamless
workflows from coding to production.

Version Control: Git

Purpose

Git is a distributed version control system that tracks changes in
source code during software development.

Benefits

It enables collaboration, branching, merging, and maintaining project
history with ease.

Platforms

Popular platforms built on Git include GitHub, GitLab, and Bitbucket,
which provide additional collaboration features.

CI/CD: Jenkins

Purpose

Jenkins is an open-source automation server used to build, test, and
deploy applications as part of CI/CD pipelines.

Features

It supports plugins for integration with thousands of
tools, enabling flexibility and scalability.

Use Case

Jenkins automates repetitive tasks, ensuring faster
and more reliable delivery of software.

CI/CD Alternatives: GitLab CI & GitHub Actions

GitLab CI

Provides built-in CI/CD pipelines tightly integrated with GitLab
repositories, supporting automation and containerization.

GitHub Actions

Allows developers to automate workflows directly in GitHub,
supporting CI/CD, testing, and deployment.

Other Options

Alternatives like CircleCI and Travis CI also provide cloud-based CI/
CD solutions.

Containerization: Docker

Purpose
Docker allows applications to be packaged with all their
dependencies into containers, ensuring consistency across
environments.

Benefits

Containers provide portability, scalability, and efficient resource
usage compared to traditional virtual machines.

Use Case

Docker is widely used for microservices architectures, enabling rapid
development and deployment.

Container Orchestration:

Purpose

Kubernetes automates the deployment, scaling, and management of
containerized applications across clusters of machines.

Benefits

It provides high availability, scalability, and efficient resource
utilization, making it ideal for large-scale applications.

Use Case

Kubernetes is widely used in cloud-native environments to manage
microservices and support DevOps workflows.

Configuration Management: Ansible

Purpose
Ansible automates configuration management, application
deployment, and infrastructure provisioning using simple YAML
scripts.

Benefits

It is agentless, easy to learn, and integrates well with cloud
platforms, making automation accessible to teams.

Use Case

Ansible is commonly used to configure servers, deploy applications,
and manage infrastructure as code (IaC).

Configuration Management: Puppet & Chef

Puppet

Puppet uses a declarative language to define desired system states
and ensures consistency across infrastructure.

Chef

Chef automates infrastructure using Ruby-based recipes and
cookbooks, providing flexibility for complex setups.

Comparison

Both tools are powerful for large-scale automation but often require
more setup compared to Ansible.

Infrastructure as Code: Terraform

Purpose

Terraform automates infrastructure provisioning using declarative
configuration files, enabling reproducibility and consistency.

Benefits

It works across multiple cloud providers, supports modular
infrastructure, and integrates with CI/CD pipelines.

Use Case

Terraform is widely used for creating cloud infrastructure like servers,
databases, and networking resources.

Monitoring: Prometheus

Purpose

Prometheus is an open-source monitoring system that collects
metrics from applications and infrastructure in real time.

Benefits

It provides powerful query capabilities, alerting, and time-series data
storage for performance monitoring.

Use Case

Prometheus is commonly used with Kubernetes and cloud-native
systems for observability and reliability.

Monitoring & Visualization: Grafana

Purpose

Grafana is an open-source visualization tool that turns monitoring
data into interactive dashboards.

Benefits

It supports multiple data sources like Prometheus, InfluxDB, and
Elasticsearch, making it versatile for observability.

Use Case

Grafana is widely used to monitor system health, application
performance, and business KPIs through customizable dashboards.

Logging & Analytics: ELK Stack

Purpose

The ELK Stack (Elasticsearch, Logstash, Kibana) is a set of tools for
centralized logging, search, and visualization.

Benefits

It helps organizations analyze logs, detect issues, and gain insights
from large volumes of data.

Use Case

The ELK Stack is widely used for log management, security analysis,
and monitoring applications in production environments.

Collaboration Tools: Slack, Teams, Jira

Slack & Teams

These messaging platforms improve real-time communication,
integrating with DevOps tools for alerts and collaboration.

Jira

Jira is a project management tool widely used for tracking issues,
managing sprints, and planning workflows.

Integration

Collaboration tools connect with CI/CD, monitoring, and version
control systems to streamline teamwork.

Security in DevOps Tools

DevSecOps

Security is integrated into the DevOps pipeline, ensuring
vulnerabilities are identified and fixed early.

Tools

Popular security tools include SonarQube for code quality, OWASP
ZAP for security testing, and Snyk for dependency scanning.

Benefits

Shifting security left reduces risks, ensures compliance, and builds
trust in software delivery.

DevOps Toolchain Integration

Cloud in DevOps

Purpose

Cloud platforms provide scalable infrastructure, enabling on-demand
resources and automation critical to DevOps practices.

Benefits

They reduce hardware costs, improve scalability, and support rapid
deployments with global reach.

Relevance

Cloud services like AWS, Azure, and Google Cloud offer integrated
DevOps tools to streamline workflows.

AWS for DevOps

Services

AWS offers services like CodePipeline, CodeBuild, and CodeDeploy
to automate CI/CD pipelines.

Benefits

Provides scalability, global infrastructure, and deep integration with
other AWS cloud services.

Use Case

Organizations use AWS DevOps services to build, test, and deploy
applications seamlessly across cloud environments.

Azure for DevOps

Services

Azure DevOps offers services like Azure Pipelines, Repos, Boards,
and Test Plans for end-to-end DevOps workflows.

Benefits

It integrates seamlessly with Microsoft products, supports hybrid
environments, and provides enterprise-grade scalability.

Use Case

Organizations use Azure DevOps for managing code repositories,
automating builds, and tracking work with agile boards.

Google Cloud for DevOps

Services

Google Cloud provides tools like Cloud Build, Cloud Deploy, and
Operations Suite for CI/CD and monitoring.

Benefits

It offers strong Kubernetes integration, AI-driven insights, and global
scalability for modern applications.

Use Case
Organizations use Google Cloud to implement cloud-native DevOps
workflows, especially with containerized and microservices-based
systems.

Infrastructure as Code (IaC) Principles

Definition

IaC is the practice of managing and provisioning infrastructure using
code instead of manual processes.

Benefits

It enables automation, consistency, and repeatability across
environments, reducing human error.

Approaches

IaC can be declarative (Terraform, CloudFormation) or imperative
(Ansible, scripts), depending on project needs.

Cloud & IaC Integration

Importance of Collaboration in DevOps

Breaking Silos

DevOps eliminates silos between development, operations, QA, and
business teams to improve efficiency.

Shared Goals

Teams work together with shared objectives, ensuring alignment
between business needs and technical delivery.

Communication

Collaboration is supported through tools, meetings, and cultural
practices that emphasize transparency and trust.

DevOps Culture & Mindset

Shift in Thinking

DevOps is more than tools—it’s a mindset focused on collaboration,
accountability, and continuous improvement.

Key Values

Trust, transparency, and shared responsibility are central to building
a strong DevOps culture.

Learning Environment

DevOps encourages experimentation, feedback loops, and
knowledge sharing across teams.

Agile & DevOps Integration

Agile Practices

Agile focuses on iterative development, customer feedback, and
flexibility in delivering value.

DevOps Alignment

DevOps extends Agile by automating delivery, testing, and
operations, enabling faster release cycles.

Combined Benefits

Together, Agile and DevOps accelerate time-to-market while
improving software quality and team collaboration.

Difference between Agile and DevOps

Agile

Agile focuses on collaboration,
customer feedback and small rapid
changes

It does not focus on automation

The development process is inherent
in Agile, making it less focused on
testing and implementation
processes
It overcomes the gap between
customers and developers

DevOps
DevOps brings development
and operation teams
together

It focus on automation to
increase efficiency with
deployment

DevOps focus on all
development, testing, and
implementation phases with
equal importance
It overcomes the gap
between the development
and operation folks

Roles & Responsibilities in DevOps Teams

Developers

Write code, integrate with CI/CD pipelines, and collaborate on
deployments and monitoring.

Operations Engineers

Manage infrastructure, ensure stability, automate provisioning, and
handle incident response.

Shared Responsibility

DevOps teams share accountability for software delivery, quality, and
uptime across all roles.

Introduction to DevSecOps

Definition

DevSecOps integrates security practices into every stage of the
DevOps lifecycle, rather than treating security as a separate phase.

Purpose

Its goal is to identify and fix vulnerabilities early, making security a
shared responsibility across teams.

Approach

Security checks, automated scans, and compliance validation are
built directly into CI/CD pipelines.

Shifting Security Left

Concept

Shifting security left means integrating security early in the
development lifecycle rather than waiting until deployment.

Practices

Includes secure coding standards, automated vulnerability scans,
and static code analysis during development.

Benefits

Identifying issues earlier reduces costs, minimizes risks, and ensures
more secure applications.

Common DevSecOps Tools

Static Analysis

Tools like SonarQube and Checkmarx analyze source code for
vulnerabilities and code quality issues.

Dynamic Analysis

OWASP ZAP and Burp Suite test running applications for security
flaws such as SQL injection or XSS.

Dependency Scanning

Snyk and WhiteSource detect vulnerabilities in open-source libraries
and third-party components.

Benefits of DevSecOps

Improved Security

Embedding security in every stage reduces vulnerabilities and
strengthens overall application safety.

Faster Delivery

Automated security checks allow teams to release software quickly
without sacrificing quality.

Compliance

DevSecOps ensures continuous compliance with industry standards
and regulations by automating checks.

Why Case Studies Matter in DevOps

Practical Insights

Case studies show how DevOps principles are applied in real
organizations, moving beyond theory.

Challenges & Solutions

They highlight common challenges and demonstrate practical
solutions used in real-world scenarios.

Learning Value

Students gain a deeper understanding by seeing how DevOps
practices drive success in diverse contexts.

General Example: Large Tech Companies

Scale

Large tech companies use DevOps to manage complex systems
with millions of users and frequent updates.

Practices

They rely heavily on automation, microservices, and CI/CD pipelines
to ensure speed and reliability.

Outcome

These practices allow them to release features faster, minimize
downtime, and maintain global scalability.

General Example: Startups & Small Teams

Scale

Startups and small teams adopt DevOps to maximize efficiency and
compete with limited resources.

Practices

They often use cloud-native services, lightweight CI/CD tools, and
containerization for agility.

Outcome

DevOps enables faster iteration, cost savings, and the ability to pivot
quickly based on customer feedback.

Lessons Learned from Real-World DevOps

Cultural Shift

Successful DevOps adoption requires strong collaboration,
communication, and cultural change beyond tools.

Automation

Automation of testing, deployment, and monitoring is essential to
achieve speed and reliability.

Continuous Improvement

Real-world cases show that DevOps is an ongoing journey, requiring
adaptation and learning.

Challenges & Best Practices in DevOps

Challenges

Common challenges include tool complexity, cultural resistance, and
ensuring security at scale.

Best Practices

Start small, embrace automation, foster collaboration, and integrate
monitoring and feedback.

Outcome

Following best practices helps organizations overcome barriers and
achieve DevOps success.

