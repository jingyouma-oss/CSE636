#!/usr/bin/env python3
"""
Minimal MCP server that exposes GitHub Actions build status to an AI agent.
CSE636 Week 2 Lab — Part 2, GitHub Actions variant (parallel to jenkins_status.py).

This is the managed-CI counterpart to the Jenkins MCP server: instead of polling
a self-hosted Jenkins REST API, it queries the GitHub Actions REST API so the
agent can answer "is my build green?" against a GitHub repo's workflow runs.
Point it at the build-fixer repo (or any repo of yours that runs Actions).

Install: pip install mcp requests
Env:
  GH_TOKEN  GitHub token with `actions:read` (a fine-grained or classic PAT).
  REPO      "owner/name", e.g. "your-username/build-fixer".
"""
import os

import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

GH_TOKEN = os.environ.get("GH_TOKEN", "")
REPO = os.environ.get("REPO", "")
API = "https://api.github.com"

app = Server("cse636-actions-mcp")


def _headers():
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GH_TOKEN:
        h["Authorization"] = f"Bearer {GH_TOKEN}"
    return h


@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_run_status",
            description=(
                "Returns the status and conclusion of the most recent GitHub "
                "Actions run for the repo. Use this to check whether CI is "
                "currently passing or failing before making code changes. "
                "Optionally filter by branch."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "branch": {
                        "type": "string",
                        "description": "Optional branch name, e.g. 'main'.",
                    }
                },
            },
        ),
        Tool(
            name="list_workflows",
            description="Returns the names of all GitHub Actions workflows in the repo.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if not REPO:
        return [TextContent(type="text", text="REPO env var is not set (owner/name).")]

    if name == "list_workflows":
        resp = requests.get(
            f"{API}/repos/{REPO}/actions/workflows", headers=_headers(), timeout=10
        )
        if resp.status_code != 200:
            return [TextContent(type="text", text=f"GitHub API error {resp.status_code}.")]
        names = [w["name"] for w in resp.json().get("workflows", [])]
        return [TextContent(type="text", text=f"Workflows: {', '.join(names) or '(none)'}")]

    if name == "get_run_status":
        params = {"per_page": 1}
        branch = arguments.get("branch")
        if branch:
            params["branch"] = branch
        resp = requests.get(
            f"{API}/repos/{REPO}/actions/runs",
            headers=_headers(),
            params=params,
            timeout=10,
        )
        if resp.status_code != 200:
            return [TextContent(type="text", text=f"GitHub API error {resp.status_code}.")]
        runs = resp.json().get("workflow_runs", [])
        if not runs:
            return [TextContent(type="text", text="No workflow runs found.")]
        run = runs[0]
        # status: queued | in_progress | completed; conclusion: success | failure | ...
        outcome = run.get("conclusion") or run.get("status")
        return [
            TextContent(
                type="text",
                text=(
                    f"{run['name']} #{run['run_number']} on "
                    f"{run['head_branch']}: {outcome}"
                ),
            )
        ]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


if __name__ == "__main__":
    import asyncio

    asyncio.run(stdio_server(app))
