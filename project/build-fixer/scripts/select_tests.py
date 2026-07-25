#!/usr/bin/env python3
"""
select_tests.py — CSE636 Week 3 Assignment, Task 1: test-impact analysis.

Maps changed files under src/ or scripts/ to the pytest file that covers
them (naming convention: src/foo.py -> tests/test_foo.py, scripts/foo.py
-> tests/test_foo.py) and runs only those, instead of the full suite on
every change.

Fails safe to the FULL suite whenever:
  - the diff can't be computed (no git history / first commit)
  - a changed module has no matching test file (unknown blast radius)
  - the diff touches a "risky" file (Jenkinsfile, requirements.txt,
    conftest.py, or one of the agent scripts themselves) — those can
    change behavior in ways no single test_<module>.py would catch.

Usage:
    python scripts/select_tests.py --base origin/main
    python scripts/select_tests.py --base origin/main --print-only
    python scripts/select_tests.py --changed src/calculator.py   # manual, for demos
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = REPO_ROOT / "tests"

TESTED_SRC_DIRS = ("src", "scripts")

RISKY_FILES = {
    "requirements.txt",
    "conftest.py",
    "Jenkinsfile",
    "scripts/build_fixer_agent.py",
    "scripts/select_tests.py",
    "scripts/remediation_agent.py",
}


def get_changed_files(base: str) -> list[str]:
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...HEAD"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout
        return [line.strip() for line in out.splitlines() if line.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"[select_tests] could not compute git diff against {base} ({e}); "
              f"failing safe to full suite", file=sys.stderr)
        return []


def module_stem(path: str):
    p = Path(path)
    if p.suffix != ".py":
        return None
    if len(p.parts) == 2 and p.parts[0] in TESTED_SRC_DIRS:
        return p.stem
    return None


def select(changed_files):
    all_tests = set(TESTS_DIR.glob("test_*.py"))

    if not changed_files:
        return all_tests, True

    if any(f in RISKY_FILES for f in changed_files):
        return all_tests, True

    stems = set()
    for f in changed_files:
        stem = module_stem(f)
        if stem is not None:
            stems.add(stem)

    if not stems:
        return set(), False

    selected = set()
    for stem in stems:
        candidate = TESTS_DIR / f"test_{stem}.py"
        if candidate.exists():
            selected.add(candidate)
        else:
            return all_tests, True

    return selected, False


def run_pytest(test_files):
    args = ["python", "-m", "pytest", "-q"] + [
        str(t.relative_to(REPO_ROOT)) for t in sorted(test_files)
    ]
    start = time.time()
    result = subprocess.run(args, cwd=REPO_ROOT)
    return result.returncode, time.time() - start


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--changed", nargs="*", help="manual override, for demos")
    ap.add_argument("--print-only", action="store_true")
    args = ap.parse_args()

    changed_files = args.changed if args.changed is not None else get_changed_files(args.base)
    all_tests = set(TESTS_DIR.glob("test_*.py"))
    selected, ran_full = select(changed_files)

    print(f"[select_tests] changed files: {changed_files or '(none detected)'}")
    print(f"[select_tests] full suite size: {len(all_tests)} test file(s)")
    print(f"[select_tests] selected: {len(selected)} test file(s) "
          f"{'(full suite)' if ran_full else '(scoped)'}")
    for t in sorted(selected):
        print(f"  - {t.relative_to(REPO_ROOT)}")

    if args.print_only:
        return

    if not selected:
        print("[select_tests] nothing to run.")
        return

    _, full_elapsed = run_pytest(all_tests) if not ran_full else (None, None)
    rc, scoped_elapsed = run_pytest(selected)

    print(f"\n[select_tests] scoped run: {len(selected)}/{len(all_tests)} files, {scoped_elapsed:.2f}s")
    if full_elapsed is not None:
        saved_pct = 100 * (1 - len(selected) / max(len(all_tests), 1))
        print(f"[select_tests] full run for comparison: {len(all_tests)} files, {full_elapsed:.2f}s "
              f"(~{saved_pct:.0f}% fewer files selected)")

    sys.exit(rc)


if __name__ == "__main__":
    main()
