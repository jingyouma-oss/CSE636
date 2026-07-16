#!/usr/bin/env python3
"""
Standalone MCP client smoke test for actions_status.py.
CSE636 Week 2 Lab — verify the server end-to-end without touching claude.json.

It spawns actions_status.py as a subprocess over stdio (exactly how Claude Code
would), performs the MCP handshake, lists the advertised tools, and then calls
both `list_workflows` and `get_run_status` — printing whatever the live GitHub
Actions API returns.

Install: pip install mcp requests
Env (same as the server):
  GH_TOKEN  GitHub token with actions:read
  REPO      "owner/name", e.g. "your-username/build-fixer"

Run:
  GH_TOKEN=<token> REPO=<owner/name> python test_actions_status.py
  # optionally filter get_run_status by branch:
  GH_TOKEN=<token> REPO=<owner/name> BRANCH=main python test_actions_status.py
"""
import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "actions_status.py")


def _text(result):
    """Flatten an MCP call_tool result into a plain string."""
    parts = []
    for block in result.content:
        parts.append(getattr(block, "text", str(block)))
    return "\n".join(parts)


async def main():
    if not os.environ.get("REPO"):
        print("Set REPO=owner/name (and GH_TOKEN) before running.", file=sys.stderr)
        return 1

    # Run the server with the same interpreter and pass our env through so it
    # sees GH_TOKEN / REPO.
    params = StdioServerParameters(
        command=sys.executable,
        args=[SERVER],
        env=os.environ.copy(),
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Tools advertised:", ", ".join(t.name for t in tools.tools))

            print("\n--- list_workflows ---")
            print(_text(await session.call_tool("list_workflows", {})))

            branch = os.environ.get("BRANCH")
            args = {"branch": branch} if branch else {}
            label = f" (branch={branch})" if branch else ""
            print(f"\n--- get_run_status{label} ---")
            print(_text(await session.call_tool("get_run_status", args)))

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
