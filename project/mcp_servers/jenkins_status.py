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
import html
import os

import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

JENKINS_URL = os.environ.get("JENKINS_URL", "http://localhost:8080").rstrip("/")
JENKINS_USER = os.environ.get("JENKINS_USER", "admin")
JENKINS_TOKEN = os.environ.get("JENKINS_TOKEN", "")

app = Server("cse636-jenkins-mcp")


def _auth():
    return (JENKINS_USER, JENKINS_TOKEN) if JENKINS_TOKEN else None


def _crumb():
    """Return a CSRF crumb header dict for POSTs ({} if crumbs are disabled)."""
    try:
        resp = requests.get(
            f"{JENKINS_URL}/crumbIssuer/api/json", auth=_auth(), timeout=10
        )
    except requests.RequestException:
        return {}
    if resp.status_code != 200:
        return {}
    data = resp.json()
    return {data["crumbRequestField"]: data["crumb"]}


def _flow_definition_xml(pipeline_script):
    """Build config.xml for a Pipeline job with an inline (CPS) script."""
    escaped = html.escape(pipeline_script)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<flow-definition plugin="workflow-job">\n'
        '  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition"'
        ' plugin="workflow-cps">\n'
        f"    <script>{escaped}</script>\n"
        "    <sandbox>true</sandbox>\n"
        "  </definition>\n"
        "  <triggers/>\n"
        "</flow-definition>\n"
    )


@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="create_job",
            description=(
                "Creates (or updates) a Jenkins Pipeline job from an inline "
                "pipeline script. Use this to stand up a CI pipeline. If the job "
                "already exists, its configuration is updated."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Job name, e.g. 'ci-agent-demo'.",
                    },
                    "pipeline_script": {
                        "type": "string",
                        "description": "The declarative Jenkinsfile text to run.",
                    },
                },
                "required": ["name", "pipeline_script"],
            },
        ),
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
        Tool(
            name="trigger_build",
            description=(
                "Triggers a build of a Jenkins job. Returns immediately; poll "
                "get_build_status for the result."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "job_name": {"type": "string", "description": "The job to build."}
                },
                "required": ["job_name"],
            },
        ),
        Tool(
            name="get_build_log",
            description=(
                "Returns the console log of the most recent build of a job. Use "
                "this to diagnose why a build failed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "job_name": {"type": "string", "description": "The job name."}
                },
                "required": ["job_name"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "create_job":
        job = arguments["name"]
        xml = _flow_definition_xml(arguments["pipeline_script"]).encode("utf-8")
        headers = {"Content-Type": "application/xml", **_crumb()}
        exists = (
            requests.get(
                f"{JENKINS_URL}/job/{job}/api/json", auth=_auth(), timeout=10
            ).status_code
            == 200
        )
        if exists:
            resp = requests.post(
                f"{JENKINS_URL}/job/{job}/config.xml",
                data=xml, headers=headers, auth=_auth(), timeout=10,
            )
            verb = "updated"
        else:
            resp = requests.post(
                f"{JENKINS_URL}/createItem", params={"name": job},
                data=xml, headers=headers, auth=_auth(), timeout=10,
            )
            verb = "created"
        if resp.status_code not in (200, 201):
            return [TextContent(type="text", text=f"Jenkins API error {resp.status_code} on create_job.")]
        return [TextContent(type="text", text=f"Job '{job}' {verb}.")]

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

    if name == "trigger_build":
        job = arguments["job_name"]
        resp = requests.post(
            f"{JENKINS_URL}/job/{job}/build", headers=_crumb(), auth=_auth(), timeout=10
        )
        if resp.status_code not in (200, 201, 302):
            return [TextContent(type="text", text=f"Jenkins API error {resp.status_code} on trigger_build.")]
        return [TextContent(
            type="text",
            text=f"Build triggered for '{job}'. Poll get_build_status for the result.",
        )]

    if name == "get_build_log":
        job = arguments["job_name"]
        resp = requests.get(
            f"{JENKINS_URL}/job/{job}/lastBuild/consoleText", auth=_auth(), timeout=10
        )
        if resp.status_code == 404:
            return [TextContent(type="text", text=f"No builds found for '{job}'.")]
        if resp.status_code != 200:
            return [TextContent(type="text", text=f"Jenkins API error {resp.status_code}.")]
        log = resp.text
        if len(log) > 8000:
            log = "...(truncated)...\n" + log[-8000:]
        return [TextContent(type="text", text=log)]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def _serve():
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(_serve())
