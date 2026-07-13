"""Build-fixer agent (Week 3).

Reads a failing pytest log, asks Claude to identify the root cause and propose
the *minimal* fix to the offending source file, then either:

  * prints the proposal (default / `--dry-run`) — needs only ANTHROPIC_API_KEY,
    so you can demo the agent locally without touching GitHub, or
  * opens a pull request with the fix (`--open-pr`) — needs GH_TOKEN and runs in
    the CI `agent-fix` job, behind the human approval gate.

The agent is deliberately constrained: it edits exactly one file, never adds or
changes tests, and (in CI) opens a PR it cannot merge. The human approval gate
in ci.yml is the guardrail — see week-03-notes.md on blast-radius limits.
"""

import argparse
import json
import os
import ssl
import sys

import anthropic
import httpx

# Default to the latest Opus; override with MODEL for a cheaper classroom run
# (e.g. MODEL=claude-haiku-4-5). All current models use adaptive thinking — do
# not pass budget_tokens here, it is rejected on Opus 4.7+ / Fable 5.
MODEL = os.environ.get("MODEL", "claude-opus-4-8")

SYSTEM_PROMPT = """\
You are a build-fixer agent. Your only job is to identify the root cause of a
failing Python test and propose the minimal fix to the source file.

Rules:
- Change exactly one file: the source file under test, never the test file.
- Make the smallest change that fixes the root cause. No refactors, no renames,
  no stylistic edits, no new error handling.
- Do not add, remove, or modify tests.
- fixed_file_content must be the complete corrected contents of fixed_file_path."""

# output_config.format guarantees the first response block is text containing
# JSON that validates against this schema — no fragile prompt-for-JSON parsing.
FIX_SCHEMA = {
    "type": "object",
    "properties": {
        "root_cause": {"type": "string", "description": "One sentence explanation."},
        "fix_description": {"type": "string", "description": "What changed and why."},
        "fixed_file_path": {"type": "string"},
        "fixed_file_content": {"type": "string"},
    },
    "required": [
        "root_cause",
        "fix_description",
        "fixed_file_path",
        "fixed_file_content",
    ],
    "additionalProperties": False,
}


def _relaxed_ssl_context():
    """SSLContext that trusts the system / corporate CA bundle but drops the
    extra-strict VERIFY_X509_STRICT flag.

    Modern Python (OpenSSL 3.x — e.g. Homebrew on macOS, or the cstu-jenkins CI
    image) enables VERIFY_X509_STRICT by default, which rejects some corporate
    TLS-inspection roots — e.g. Zscaler — whose Basic Constraints extension isn't
    marked critical ("certificate verify failed: Basic Constraints of CA cert not
    marked critical"). We keep full chain and hostname verification but drop that
    one extra-strict flag, matching what curl/browsers do. Honors SSL_CERT_FILE /
    REQUESTS_CA_BUNDLE when set; falls back to the system trust store otherwise,
    so it's a no-op off-proxy.
    """
    ca = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
    ctx = ssl.create_default_context(cafile=ca)
    ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return ctx


def _make_client():
    """Anthropic client (httpx) whose TLS uses the relaxed context above."""
    # reads ANTHROPIC_API_KEY from the environment
    return anthropic.Anthropic(http_client=httpx.Client(verify=_relaxed_ssl_context()))


def _patch_requests_tls():
    """Make `requests` (used by PyGithub) verify with the relaxed context too.

    PyGithub talks to api.github.com via `requests`, which builds its own SSL
    context and would hit the same VERIFY_X509_STRICT rejection behind a proxy.
    Mounting our context on the HTTPAdapter covers every `requests` session,
    including the one PyGithub creates internally. No-op off-proxy.
    """
    import requests.adapters

    ctx = _relaxed_ssl_context()
    original = requests.adapters.HTTPAdapter.init_poolmanager

    def init_poolmanager(self, *args, **kwargs):
        kwargs.setdefault("ssl_context", ctx)
        return original(self, *args, **kwargs)

    requests.adapters.HTTPAdapter.init_poolmanager = init_poolmanager


def propose_fix(build_log, source_path, source_code):
    """Ask Claude for a fix; return the validated dict from FIX_SCHEMA."""
    client = _make_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        output_config={"format": {"type": "json_schema", "schema": FIX_SCHEMA}},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Build log:\n```\n{build_log}\n```\n\n"
                    f"Source file ({source_path}):\n```python\n{source_code}\n```"
                ),
            }
        ],
    )
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def open_pull_request(fix):
    """Open a no-merge PR with the proposed fix. Requires GH_TOKEN + REPO."""
    _patch_requests_tls()  # trust the corporate proxy CA before PyGithub connects
    from github import Github

    gh = Github(os.environ["GH_TOKEN"])
    repo = gh.get_repo(os.environ["REPO"])
    base = os.environ.get("BASE_BRANCH", "main")
    branch = f"bot/fix-build-{os.environ.get('GITHUB_RUN_ID', 'local')}"

    ref = repo.get_git_ref(f"heads/{base}")
    repo.create_git_ref(f"refs/heads/{branch}", ref.object.sha)

    contents = repo.get_contents(fix["fixed_file_path"], ref=base)
    repo.update_file(
        fix["fixed_file_path"],
        f"[bot] fix: {fix['root_cause'][:60]}",
        fix["fixed_file_content"],
        contents.sha,
        branch=branch,
    )

    pr = repo.create_pull(
        title=f"[Bot Fix] {fix['root_cause'][:60]}",
        body=(
            "## Agent-proposed fix\n\n"
            f"**Root cause:** {fix['root_cause']}\n\n"
            f"**Change:** {fix['fix_description']}\n\n"
            "---\n"
            "*Opened by the build-fixer agent. A human must review and approve "
            "before merging.*\n\n"
            "**Checklist before approving:**\n"
            "- [ ] The fix matches the described root cause\n"
            "- [ ] No unrelated changes are included\n"
            "- [ ] No test or infrastructure files were touched\n"
        ),
        head=branch,
        base=base,
    )
    return pr


def main():
    parser = argparse.ArgumentParser(description="Propose a fix for a failing build.")
    parser.add_argument(
        "--log", default="build_log.txt", help="Path to the pytest log."
    )
    parser.add_argument(
        "--source",
        default="src/calculator.py",
        help="Source file the agent is allowed to edit.",
    )
    parser.add_argument(
        "--open-pr",
        action="store_true",
        help="Open a GitHub PR (needs GH_TOKEN + REPO). Default is dry-run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the proposed fix without opening a PR (default behavior).",
    )
    args = parser.parse_args()

    with open(args.log) as f:
        build_log = f.read()
    with open(args.source) as f:
        source_code = f.read()

    fix = propose_fix(build_log, args.source, source_code)
    # The PR must target the path we were told to edit (--source), not the model's
    # guess. The build log can make the model report a shorter path (e.g.
    # src/calculator.py) that doesn't exist at the repo root in a monorepo, which
    # 404s on get_contents. We already know the path — don't let the LLM pick it.
    fix["fixed_file_path"] = args.source
    print(f"Root cause: {fix['root_cause']}")
    print(f"Fix:        {fix['fix_description']}")
    print(f"File:       {fix['fixed_file_path']}\n")

    if args.open_pr:
        pr = open_pull_request(fix)
        print(f"Opened PR #{pr.number}: {pr.html_url}")
    else:
        print("--- proposed file contents (dry-run, no PR opened) ---")
        print(fix["fixed_file_content"])
        print("Re-run with --open-pr (and GH_TOKEN/REPO set) to open a pull request.")


if __name__ == "__main__":
    try:
        main()
    except StopIteration:
        sys.exit("Agent returned no text content; check the model response.")
