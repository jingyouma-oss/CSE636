#!/usr/bin/env python3
"""
Minimal MCP server that exposes local Jenkins build status to an AI agent.
CSE636 Week 2 Lab — Part 2, Jenkins variant (parallel to actions_status.py).

This is the self-hosted-CI counterpart to the GitHub Actions MCP server: instead
of querying the GitHub Actions REST API, it polls a local Jenkins controller's
REST API so the agent can answer "is my build green?" against your Jenkins jobs.
Point it at the Week 2 lab's local Jenkins (the `cstu-jenkins` container on
http://localhost:8080).

Install: pip install mcp requests
Env:
  JENKINS_URL    Base URL, e.g. "http://localhost:8080".
  JENKINS_USER   Jenkins username, e.g. "admin".
  JENKINS_TOKEN  API token (Manage Jenkins -> your user -> Security -> API Token).
"""
import os

import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

JENKINS_URL = os.environ.get("JENKINS_URL", "http://localhost:8080").rstrip("/")
JENKINS_USER = os.environ.get("JENKINS_USER", "")
JENKINS_TOKEN = os.environ.get("JENKINS_TOKEN", "")

app = Server("cse636-jenkins-mcp")


def _auth():
    return (JENKINS_USER, JENKINS_TOKEN) if JENKINS_TOKEN else None


@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_build_status",
            description=(
                "Returns the status and number of the most recent Jenkins build "
                "for a given job. Use this to check if a CI pipeline is currently "
                "passing or failing before making code changes."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "job_name": {
                        "type": "string",
                        "description": "The Jenkins job name, e.g. 'ai-review-demo'",
                    }
                },
                "required": ["job_name"],
            },
        ),
        Tool(
            name="list_jobs",
            description="Returns a list of all Jenkins job names.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "list_jobs":
        resp = requests.get(
            f"{JENKINS_URL}/api/json?tree=jobs[name]", auth=_auth(), timeout=10
        )
        if resp.status_code != 200:
            return [TextContent(type="text", text=f"Jenkins API error {resp.status_code}.")]
        jobs = [j["name"] for j in resp.json().get("jobs", [])]
        return [TextContent(type="text", text=f"Jenkins jobs: {', '.join(jobs) or '(none)'}")]

    if name == "get_build_status":
        job = arguments["job_name"]
        resp = requests.get(
            f"{JENKINS_URL}/job/{job}/lastBuild/api/json", auth=_auth(), timeout=10
        )
        if resp.status_code == 404:
            return [TextContent(type="text", text=f"Job '{job}' not found (or it has no builds yet).")]
        if resp.status_code != 200:
            return [TextContent(type="text", text=f"Jenkins API error {resp.status_code}.")]
        data = resp.json()
        # result is null while a build is still running.
        result = data.get("result") or "IN_PROGRESS"
        number = data.get("number", "?")
        return [TextContent(type="text", text=f"Job '{job}': build #{number} — {result}")]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def _serve():
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(_serve())
