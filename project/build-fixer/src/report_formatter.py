"""Formats a status report as YAML.

Intentional bug (Assignment's remediation-agent demo, separate from the
Lab's calculator bug): this module imports `yaml` (PyYAML), which is
missing from requirements.txt. A build using this repo's requirements.txt
fails with:
    ModuleNotFoundError: No module named 'yaml'
This is the exact, well-defined failure class scripts/remediation_agent.py
detects and fixes by appending the missing entry to requirements.txt.
"""
import yaml  # noqa: F401  (intentionally missing from requirements.txt)


def format_report(name: str, healthy: bool) -> str:
    return yaml.safe_dump({"name": name, "status": "ok" if healthy else "down"})
