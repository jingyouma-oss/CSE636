# Week 6 — Lab & Assignment

> 🧪 **Hands-on work for Week 6.** For the lecture notes, foundations primer, discussion questions, and references, see **[week-06-notes.md](week-06-notes.md)**.

---

## 🧪 Lab: Build an Incident-Triage Agent with a Gated Remediation

**Time:** ~3 hours (can be split across two sessions)

**Objective:** Build a Python-based agent, with tools exposed via MCP, that receives a simulated incident, triages it using a structured runbook, and triggers a remediation only after passing through a human-approval gate.

---

### What You Will Build

```
Simulated incident event
        │
        ▼
┌───────────────────┐
│   MCP Server      │  ← exposes: get_metrics, get_logs,
│   (incident_tools)│             get_deployment_history,
│                   │             dry_run_rollback, execute_rollback,
│                   │             create_pd_incident, resolve_pd_incident
└────────┬──────────┘
         │ tool calls
         ▼
┌───────────────────┐
│   Python Agent    │  ← ReAct loop: reason → call tool → observe → repeat
│   (react_agent.py)│
└────────┬──────────┘
         │
  Approval gate (terminal input simulating Slack)
         │
         ▼
  Remediation executed (or escalated)
         │
         ▼
  Console postmortem summary printed
```

---

### Step 1: Set Up Your Environment

```bash
# Create a virtual environment
python -m venv week6-lab
source week6-lab/bin/activate      # Windows: week6-lab\Scripts\activate

# Install dependencies
pip install anthropic mcp pydantic
```

You will need an Anthropic API key (set as `ANTHROPIC_API_KEY` in your environment, or use a `.env` file with `python-dotenv`).

---

### Step 2: Create the MCP Server (incident_tools_server.py)

Create a file `incident_tools_server.py`. This server exposes the "operations toolbox" that the agent will use.

```python
# incident_tools_server.py
import asyncio
import json
import random
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("incident-tools")

# --- Simulated data store ---
DEPLOYMENTS = {
    "payment-svc": {
        "current_version": "v1.4.2",
        "previous_version": "v1.4.1",
        "deployed_at": "8 minutes ago",
        "migration_pending": False,
    },
    "cart-svc": {
        "current_version": "v2.1.0",
        "previous_version": "v2.0.9",
        "deployed_at": "2 hours ago",
        "migration_pending": False,
    }
}

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_metrics",
            description="Get current error rate and latency for a service",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {"type": "string", "description": "Service name"}
                },
                "required": ["service"]
            }
        ),
        Tool(
            name="get_recent_logs",
            description="Get recent error log lines for a service",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {"type": "string"},
                    "tail": {"type": "integer", "default": 20}
                },
                "required": ["service"]
            }
        ),
        Tool(
            name="get_deployment_history",
            description="Get deployment history for a service",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {"type": "string"}
                },
                "required": ["service"]
            }
        ),
        Tool(
            name="dry_run_rollback",
            description="Show what a rollback would do, without executing it",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {"type": "string"}
                },
                "required": ["service"]
            }
        ),
        Tool(
            name="execute_rollback",
            description="Execute a rollback. REQUIRES prior human approval.",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {"type": "string"},
                    "approved_by": {"type": "string",
                                    "description": "Name of approver"}
                },
                "required": ["service", "approved_by"]
            }
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_metrics":
        service = arguments["service"]
        # Simulate elevated metrics for payment-svc
        if service == "payment-svc":
            data = {"error_rate": 0.08, "p99_latency_ms": 450,
                    "error_budget_remaining": 0.42}
        else:
            data = {"error_rate": 0.003, "p99_latency_ms": 120,
                    "error_budget_remaining": 0.85}
        return [TextContent(type="text", text=json.dumps(data))]

    elif name == "get_recent_logs":
        service = arguments["service"]
        if service == "payment-svc":
            logs = [
                "ERROR NullPointerException in PaymentProcessor.process() line 142",
                "ERROR NullPointerException in PaymentProcessor.process() line 142",
                "WARN  Cart total $12,450.00 exceeded expected range",
                "ERROR NullPointerException in PaymentProcessor.process() line 142",
            ]
        else:
            logs = ["INFO  Request processed in 115ms", "INFO  Healthcheck OK"]
        return [TextContent(type="text", text="\n".join(logs))]

    elif name == "get_deployment_history":
        service = arguments["service"]
        info = DEPLOYMENTS.get(service, {})
        return [TextContent(type="text", text=json.dumps(info))]

    elif name == "dry_run_rollback":
        service = arguments["service"]
        info = DEPLOYMENTS.get(service, {})
        result = (f"DRY RUN: Would revert {service} from "
                  f"{info.get('current_version')} → "
                  f"{info.get('previous_version')}. "
                  f"Migration pending: {info.get('migration_pending')}")
        return [TextContent(type="text", text=result)]

    elif name == "execute_rollback":
        service = arguments["service"]
        approver = arguments["approved_by"]
        info = DEPLOYMENTS.get(service, {})
        result = (f"ROLLBACK EXECUTED: {service} reverted from "
                  f"{info.get('current_version')} → "
                  f"{info.get('previous_version')}. "
                  f"Approved by: {approver}. ETA: 45 seconds.")
        return [TextContent(type="text", text=result)]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream,
                         server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Step 3: Create the React Agent (react_agent.py)

```python
# react_agent.py
# A ReAct-style agent that uses MCP tools to triage a simulated incident.
# Uses the Anthropic API with tool_use.

import json
import anthropic

# --- Anthropic client ---
client = anthropic.Anthropic()   # reads ANTHROPIC_API_KEY from env

# --- Tool definitions (mirror the MCP server) ---
TOOLS = [
    {
        "name": "get_metrics",
        "description": "Get current error rate and latency for a service",
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {"type": "string", "description": "Service name"}
            },
            "required": ["service"]
        }
    },
    {
        "name": "get_recent_logs",
        "description": "Get recent error log lines for a service (last N lines)",
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {"type": "string"},
                "tail": {"type": "integer"}
            },
            "required": ["service"]
        }
    },
    {
        "name": "get_deployment_history",
        "description": "Get recent deployment history for a service",
        "input_schema": {
            "type": "object",
            "properties": {"service": {"type": "string"}},
            "required": ["service"]
        }
    },
    {
        "name": "dry_run_rollback",
        "description": "Preview a rollback without executing it. Always run this before execute_rollback.",
        "input_schema": {
            "type": "object",
            "properties": {"service": {"type": "string"}},
            "required": ["service"]
        }
    },
    {
        "name": "execute_rollback",
        "description": "Execute a rollback. ONLY call this after human approval has been obtained.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {"type": "string"},
                "approved_by": {"type": "string"}
            },
            "required": ["service", "approved_by"]
        }
    }
]

# --- Simulated tool execution (in a real system, these call the MCP server) ---
def execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "get_metrics":
        s = tool_input["service"]
        if s == "payment-svc":
            return json.dumps({"error_rate": 0.08, "p99_latency_ms": 450,
                               "error_budget_remaining": 0.42})
        return json.dumps({"error_rate": 0.003, "p99_latency_ms": 120,
                           "error_budget_remaining": 0.85})

    elif tool_name == "get_recent_logs":
        s = tool_input["service"]
        if s == "payment-svc":
            return ("ERROR NullPointerException in PaymentProcessor.process() line 142\n"
                    "ERROR NullPointerException in PaymentProcessor.process() line 142\n"
                    "WARN  Cart total $12,450.00 exceeded expected range\n")
        return "INFO  Request processed in 115ms\nINFO  Healthcheck OK"

    elif tool_name == "get_deployment_history":
        s = tool_input["service"]
        if s == "payment-svc":
            return json.dumps({"current": "v1.4.2", "previous": "v1.4.1",
                               "deployed_at": "8 minutes ago",
                               "migration_pending": False})
        return json.dumps({"current": "v2.1.0", "deployed_at": "2 hours ago"})

    elif tool_name == "dry_run_rollback":
        s = tool_input["service"]
        return f"DRY RUN: Would revert {s} v1.4.2 → v1.4.1. No migration pending. Safe to proceed."

    elif tool_name == "execute_rollback":
        s = tool_input["service"]
        approver = tool_input.get("approved_by", "unknown")
        return f"ROLLBACK EXECUTED: {s} reverted to v1.4.1. Approved by {approver}. ETA 45s."

    return f"Unknown tool: {tool_name}"

# --- Approval gate ---
def request_human_approval(action: str) -> tuple[bool, str]:
    print(f"\n{'='*60}")
    print(f"[APPROVAL GATE] Agent requests permission to: {action}")
    print(f"{'='*60}")
    response = input("Approve? (yes/no): ").strip().lower()
    if response == "yes":
        approver = input("Enter your name for the audit log: ").strip()
        return True, approver
    return False, ""

# --- Main agent loop ---
def run_agent(incident: str):
    print(f"\n[Agent] Starting triage for incident: {incident}\n")

    system_prompt = """You are an agentic SRE (Site Reliability Engineer).
Your job is to triage incidents using the available tools and recommend or execute remediations.

Rules you MUST follow:
1. Always run dry_run_rollback BEFORE execute_rollback.
2. NEVER call execute_rollback unless you have stated that you need human approval
   and the field approved_by has been provided to you by the orchestration layer.
3. Always explain your reasoning before each tool call.
4. If you are not confident (e.g., no matching pattern, migration pending), recommend 
   escalation to the human on-call rather than taking action.
5. After resolving an incident (or escalating), summarize what happened in 3-5 bullet points
   suitable for a postmortem draft.
"""

    messages = [
        {
            "role": "user",
            "content": f"Incident alert: {incident}\n\nPlease triage this incident and determine the appropriate remediation."
        }
    ]

    # Agent ReAct loop
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system_prompt,
            tools=TOOLS,
            messages=messages
        )

        # Process the response
        for block in response.content:
            if hasattr(block, "text"):
                print(f"[Agent Thought] {block.text}")

        # Check stop condition
        if response.stop_reason == "end_turn":
            print("\n[Agent] Triage complete.")
            break

        if response.stop_reason != "tool_use":
            print(f"[Agent] Unexpected stop reason: {response.stop_reason}")
            break

        # Process tool calls
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input

                print(f"\n[Agent Action] Calling tool: {tool_name}({json.dumps(tool_input)})")

                # Special handling for destructive action
                if tool_name == "execute_rollback":
                    approved, approver = request_human_approval(
                        f"execute_rollback on {tool_input.get('service')}"
                    )
                    if not approved:
                        tool_result = ("Rollback DECLINED by operator. "
                                       "Escalate to human on-call for manual intervention.")
                    else:
                        tool_input["approved_by"] = approver
                        tool_result = execute_tool(tool_name, tool_input)
                else:
                    tool_result = execute_tool(tool_name, tool_input)

                print(f"[Tool Result] {tool_result}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": tool_result
                })

        # Add assistant response and tool results to message history
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

if __name__ == "__main__":
    incident_description = (
        "ALERT: payment-svc error rate has been above 5% for the past 4 minutes. "
        "This started approximately 8 minutes after a deployment. "
        "Cart-svc latency is also slightly elevated. "
        "Please investigate and remediate."
    )
    run_agent(incident_description)
```

---

### Step 4: Run the Lab and Observe

```bash
python react_agent.py
```

**What to observe:**
- The agent's "thought" text before each tool call (the ReAct pattern).
- How the agent combines metrics + logs + deployment history before deciding on a rollback.
- The approval gate pausing execution before the destructive action.
- The postmortem summary at the end.

**Experiments to try:**
1. Change `migration_pending` to `True` in the simulated data and see how the agent changes its behavior.
2. Decline the approval gate and observe the escalation response.
3. Change `payment-svc` error rate to 0.02 (below 5%) and see if the agent still recommends rollback or concludes the incident is minor.

---

### What to Submit

1. **Your `react_agent.py` and `incident_tools_server.py`** — include your name in a comment at the top.
2. **A terminal transcript** of one full agent run (copy-paste the output), including the approval gate interaction.
3. **A short reflection** (300–400 words) answering:
   - At what level of autonomy did your agent operate? Was that the right choice?
   - What guardrails did you implement beyond the approval gate?
   - What would you need to add to deploy this agent against a real Kubernetes cluster safely?
   - What surprised you about the agent's reasoning?

---

## Assignment: Self-Healing Microservice with Agent-Driven Triggers

**Due:** Before start of Week 7

**Objective:** Design and partially implement a self-healing mechanism for a microservice that uses an agent to decide when and how to remediate, with a mandatory human-approval step for any destructive action.

---

### Suggested Structure

Your submission should include the following components. You do not need to deploy to a real Kubernetes cluster; simulation is acceptable.

**1. Architecture diagram (1 page)**

Draw (pen and paper, Lucidchart, or draw.io) your self-healing architecture:
- What components are in your stack (observability, alert manager, agent, ITSM tool, Kubernetes/target system)?
- Where are the approval gates?
- Which autonomy level applies to each action?
- Where is the kill switch?

**2. Runbook definition (YAML or structured text)**

Write a structured runbook for one failure mode of your chosen microservice. It must include:
- Trigger condition (metric, threshold, duration)
- Diagnostic steps (as tool calls)
- Decision logic (when to auto-remediate vs. escalate)
- Remediation action
- Verification step (how do you confirm it worked?)

**3. Agent code (Python)**

Implement the agent. Your agent must:
- Use the Anthropic API (or another LLM API) with tool calling.
- Expose at least three tools relevant to your scenario.
- Implement the ReAct loop with logged thoughts.
- Include at least one approval gate that blocks execution of a destructive action until human confirmation is received.
- Include at least two blast-radius controls (e.g., rate limit, dry-run, error budget check).

**4. Terminal transcript**

Include a full transcript of your agent triaging a simulated incident, including the approval gate.

**5. Safety discussion (400–600 words)**

Discuss:
- What failure modes exist in your agent implementation? (Think: what could go wrong if the agent misbehaves?)
- How would your blast-radius controls limit damage if the agent made a wrong decision?
- How would you test this agent before deploying it against a real system?
- What additional guardrails would you add before using this in production?

---

### Rubric Hints

| Criterion | What earns full marks |
|---|---|
| Architecture diagram | Clear, correctly labelled, shows approval gates and autonomy levels |
| Runbook definition | Covers trigger, diagnostics, decision logic, remediation, verification |
| Agent code — ReAct loop | Thought text is logged before each action; loop terminates correctly |
| Agent code — approval gate | Destructive action blocked until approval; escalation path if declined |
| Agent code — blast-radius controls | At least 2 controls implemented and demonstrated |
| Safety discussion | Identifies real failure modes; proposes concrete mitigations; not generic |
| Code quality | Readable, commented, handles edge cases (migration pending, budget low) |
