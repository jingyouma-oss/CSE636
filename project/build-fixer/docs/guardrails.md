# Guardrails — Week 3 Assignment

**Author:** Jingyou Ma

## Approval gate
Both `build_fixer_agent.py` and `remediation_agent.py` only ever OPEN a PR.
Merging is a human action in GitHub, gated behind the Jenkinsfile's `input`
step (wrapped in `timeout` — an unattended build ABORTS, it never
auto-approves). Neither agent's GitHub token has merge permission.

## Blast-radius limits

### remediation_agent.py (Task 2)
- Detection is a deterministic regex match on `ModuleNotFoundError`, never
  an LLM judgment call about whether this failure class applies.
- The fix is a lookup in a small, hand-curated, version-pinned allowlist
  (`MODULE_TO_PACKAGE`). An unmapped module name is refused, not guessed —
  inventing a PyPI package name from log content would be a supply-chain
  risk (typosquatting / attacker-controlled log text).
- Only ever appends a line to `requirements.txt`. Never rewrites or
  deletes existing lines, never touches any other file.
- Claude is only used to word the PR description after the fix is already
  decided; if the API call fails, a templated description is used instead
  and the fix still proceeds — the code change never depends on the model.

### select_tests.py (Task 1)
- Fails safe to the FULL test suite whenever: the diff can't be computed,
  a changed module has no matching test file, or the diff touches a
  "risky" file (Jenkinsfile, requirements.txt, conftest.py, or one of the
  agent scripts themselves). Skipping tests is only trusted when the
  changed-file -> test-file mapping is unambiguous.

## Prompt scoping
`remediation_agent.py`'s system prompt explicitly tells the model the fix
is already decided — its only job is to summarize it in 2-3 sentences and
not suggest anything beyond the change already made.
