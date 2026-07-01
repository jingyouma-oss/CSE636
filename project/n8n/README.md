# n8n — AI Incident-Response Agent (teaching skeleton)

A recreation of the DevOps-with-AI incident-response workflow: a scheduled poll of a
metrics endpoint feeds an **AI Agent** that triages incidents with a fleet of tools and
notifies on-call.

`incident-response-agent.json` is an **importable** n8n workflow. It mirrors the diagram
exactly. The agent's tools are mock `Code` nodes so students can see the flow before
wiring real integrations.

### Runs offline (mostly)

To let you click **Execute workflow** without standing up a monitoring stack:

- **HTTP Request** ships with **pinned mock data** (a fake "firing alert"), so it does
  **not** hit `localhost:9090`. Unpin it (right-click → *Unpin*) to call a real Prometheus.
- **Get a message (Gmail)** and **Send a text message (Telegram)** are **disabled** — they
  need credentials. Re-enable them once configured.
- The **AI Agent still needs an Ollama server** running at `http://localhost:11434` with a
  model pulled (`ollama pull llama3.1`). No Ollama = the agent node errors. Swap it for an
  *Anthropic Chat Model* if you'd rather use Claude (see below).

## Flow

```
Schedule Trigger ─▶ HTTP Request (Prometheus) ─▶ If
                                                  ├─ TRUE  ─▶ Get a message (Gmail)
                                                  │        ─▶ Edit Fields ─▶ AI Agent
                                                  │        ─▶ Send a text message (Telegram)
                                                  └─ FALSE ─▶ Edit Fields1 (healthy)

AI Agent  ◀─ Ollama Chat Model (model)
          ◀─ Simple Memory (memory)
          ◀─ tools: Incident Analyzer · Log Analyzer · Reporter Tool · Decision Router ·
                    CD Analyzer · Docker Restart · Human Review · Deal Action · Approval
```

## Import

1. Open n8n → **Workflows** → **Import from File** (or paste JSON via **Import from URL/Clipboard**).
2. Select `incident-response-agent.json`.
3. Click **Execute workflow** — it runs end-to-end with mock tools.

## Turning the skeleton into a real workflow

| Node | Swap in |
|------|---------|
| HTTP Request | Your real Prometheus URL / PromQL (default `localhost:9090`) |
| Ollama Chat Model | An **Ollama** credential (default `http://localhost:11434`) + a pulled model (`llama3.1`) |
| Get a message | A **Gmail OAuth2** credential |
| Send a text message | A **Telegram Bot** credential + your chat ID |
| Code tools | Replace each mock `jsCode` with a real call (log query, Docker API/SSH, Slack approval, ticket creation) |

> ⚠️ **Docker Restart** and **Deal Action** are destructive in production. The agent's
> system prompt requires **Human Review / Approval** before any destructive action —
> keep that guardrail when you make the tools real.

## Troubleshooting

- **`ECONNREFUSED localhost:9090` / HTTP Request fails** — Prometheus isn't running. The
  node is pinned with mock data by default; if you unpinned it, either re-pin or start
  Prometheus.
- **AI Agent errors / `ECONNREFUSED localhost:11434`** — start Ollama and pull the model,
  or replace the *Ollama Chat Model* node with an *Anthropic Chat Model*.
- **Gmail/Telegram node errors** — they're disabled by default; only enable after adding
  credentials.
- **`No session ID found` (Simple Memory)** — the memory node defaults to reading a session
  ID from a Chat Trigger. This workflow uses a Schedule trigger, so it's set to a **custom
  key** (`incident-{{ $execution.id }}`) instead. Keep that setting for non-chat workflows.
- **HTTP Request: "The service refused the connection - perhaps it is offline"** — this is a
  **Docker networking** issue, not a dead Prometheus. When n8n runs in a container,
  `localhost` means *the n8n container itself*, not your host or the Prometheus container.
  Fixes, depending on how things run:
  - **n8n in Docker, Prometheus in Docker, on the same network** → use the Prometheus
    **container/service name**: `http://prometheus:9090/api/v1/query`.
  - **n8n in Docker, Prometheus reachable on the host** (Docker Desktop / Mac / Windows) →
    `http://host.docker.internal:9090/api/v1/query`. If the two containers were started
    separately (different networks), either use this, or join them:
    `docker network create monitoring && docker network connect monitoring <n8n> && docker network connect monitoring <prometheus>`, then use the container name.
  - **n8n running natively** → `http://localhost:9090` works only if the Prometheus
    container publishes the port (`-p 9090:9090`; check `docker ps`).
  - **Confirm from inside n8n before editing the node:**
    `docker exec -it <n8n-container> sh` then
    `wget -qO- 'http://host.docker.internal:9090/api/v1/query?query=up'` — whichever address
    returns JSON is the one to paste into the HTTP Request URL.

## Notes

- LLM: **Ollama** (as in the source diagram). To use Claude instead, swap the
  *Ollama Chat Model* node for an *Anthropic Chat Model* node and add an API key.
- **Course fit:** this is the no-code companion to **Week 6 — Autonomous Incident Response
  & Agentic SRE**. The guided walkthrough (nav strip, diagram, concept mapping) lives at
  [`weeks/week-06/week-06-demo-n8n.md`](../../weeks/week-06/week-06-demo-n8n.md); the coded
  (Python + MCP) version of the same agent is [`weeks/week-06/week-06-lab.md`](../../weeks/week-06/week-06-lab.md).
