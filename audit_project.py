"""Compatibility entry point for scripts/analytics/audit_project.py."""
from pathlib import Path

_source = Path(__file__).resolve().parent / "scripts" / "analytics" / "audit_project.py"
exec(compile(_source.read_text(encoding="utf-8"), str(_source), "exec"), globals())
