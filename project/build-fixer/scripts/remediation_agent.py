#!/usr/bin/env python3
"""
remediation_agent.py — CSE636 Week 3 Assignment, Task 2.

Failure class handled (deliberately narrow, per the assignment's "choose
ONE well-defined failure type"): import errors caused by a missing
requirements.txt entry, i.e. a build log containing:

    ModuleNotFoundError: No module named 'X'

Detection is a DETERMINISTIC regex match, not a model guess. The fix is
looked up in a small, hand-curated, version-pinned allowlist
(MODULE_TO_PACKAGE); an unmapped module is refused rather than guessed,
since inventing a PyPI package name from a log file is a supply-chain
risk. Claude is only used AFTER the fix is already decided, to write the
PR description — see docs/guardrails.md.

Mirrors build_fixer_agent.py's conventions: --log/--dry-run/--open-pr.
--requirements accepts a repo-root-relative path when run from the repo
root (Jenkins), same convention as build_fixer_agent.py's --source.

Usage:
    python scripts/remediation_agent.py --log build_log.txt --dry-run
    python scripts/remediation_agent.py --log build_log.txt --open-pr
"""
import argparse
import os
import re
import sys

MODULE_TO_PACKAGE = {
    "yaml": "PyYAML>=6.0,<7",
    "requests": "requests>=2.31,<3",
    "dateutil": "python-dateutil>=2.8,<3",
    "dotenv": "python-dotenv>=1.0,<2",
}

MODULE_NOT_FOUND_RE = re.compile(r"ModuleNotFoundError: No module named ['\"](\w+)['\"]")

SYSTEM_PROMPT = """You write a short, factual PR description for a fully
automated dependency fix. You are NOT deciding what the fix is — that has
already been computed deterministically. Only summarize it in two or
three sentences. Do not speculate about unrelated causes, and do not
suggest any change beyond the one already made."""


def detect_missing_module(build_log: str):
    match = MODULE_NOT_FOUND_RE.search(build_log)
    return match.group(1) if match else None


def explain_with_claude(module, package_line, build_log):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        model = os.environ.get("MODEL", "claude-haiku-4-5")
        resp = client.messages.create(
            model=model,
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": (
                    f"The build failed with ModuleNotFoundError for `{module}`. "
                    f"The deterministic fix is: append `{package_line}` to requirements.txt. "
                    f"Relevant log excerpt:\n```\n{build_log[-800:]}\n```\n"
                    f"Write the PR description."
                ),
            }],
        )
        return next(b.text for b in resp.content if b.type == "text").strip()
    except Exception as e:
        print(f"[remediation_agent] Claude explanation unavailable, using template ({e})", file=sys.stderr)
        return (
            f"CI failed with `ModuleNotFoundError: No module named '{module}'`. "
            f"`{module}` is imported by the application but missing from requirements.txt. "
            f"This PR appends `{package_line}`."
        )


def apply_fix(module, requirements_path):
    package_line = MODULE_TO_PACKAGE[module]
    with open(requirements_path, "a") as f:
        f.write(f"{package_line}\n")
    return package_line


def open_pr(module, package_line, description, requirements_path):
    from github import Github

    gh = Github(os.environ["GH_TOKEN"])
    repo = gh.get_repo(os.environ["REPO"])
    base = os.environ.get("BASE_BRANCH", "main")
    branch_name = f"bot/fix-missing-dep-{module}-{os.environ.get('BUILD_NUMBER', 'local')}"

    ref = repo.get_git_ref(f"heads/{base}")
    repo.create_git_ref(f"refs/heads/{branch_name}", ref.object.sha)

    contents = repo.get_contents(requirements_path, ref=base)
    new_content = contents.decoded_content.decode() + f"{package_line}\n"
    repo.update_file(
        requirements_path,
        f"[bot] fix: add missing dependency '{module}'",
        new_content,
        contents.sha,
        branch=branch_name,
    )

    pr = repo.create_pull(
        title=f"[Bot Fix] Add missing dependency: {module}",
        body=(
            f"## Agent-Proposed Remediation\n\n"
            f"**Failure class:** missing requirements.txt entry (ModuleNotFoundError)\n\n"
            f"{description}\n\n"
            f"**Change:** appended `{package_line}` to `{requirements_path}`. "
            f"No other file was touched.\n\n"
            f"---\n"
            f"*Opened automatically. A human must review and approve before merging. "
            f"The agent's token cannot merge this PR.*\n\n"
            f"**Checklist before approving:**\n"
            f"- [ ] The package name/version pin is correct and expected\n"
            f"- [ ] Only `{requirements_path}` was changed\n"
            f"- [ ] No unrelated lines were modified or removed\n"
        ),
        head=branch_name,
        base=base,
    )
    print(f"Opened PR #{pr.number}: {pr.html_url}")
    return pr.number


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default="build_log.txt")
    ap.add_argument("--requirements", default="requirements.txt")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--open-pr", action="store_true")
    args = ap.parse_args()

    with open(args.log) as f:
        build_log = f.read()

    module = detect_missing_module(build_log)
    if module is None:
        print("[remediation_agent] no ModuleNotFoundError in this log; nothing to do.")
        sys.exit(0)

    print(f"[remediation_agent] detected missing module: {module}")

    if module not in MODULE_TO_PACKAGE:
        print(f"[remediation_agent] '{module}' not in allowlist ({sorted(MODULE_TO_PACKAGE)}); refusing to guess.")
        sys.exit(2)

    package_line = MODULE_TO_PACKAGE[module]

    if args.dry_run:
        print(f"[remediation_agent] (dry-run) would append to {args.requirements}: {package_line}")
        description = explain_with_claude(module, package_line, build_log)
        print(f"[remediation_agent] PR description would be:\n{description}")
        return

    apply_fix(module, args.requirements)
    print(f"[remediation_agent] appended to {args.requirements}: {package_line}")
    description = explain_with_claude(module, package_line, build_log)

    should_open_pr = args.open_pr or "GH_TOKEN" in os.environ
    if should_open_pr:
        open_pr(module, package_line, description, args.requirements)
    else:
        print("[remediation_agent] no GH_TOKEN / --open-pr; change left local (not committed).")


if __name__ == "__main__":
    main()
