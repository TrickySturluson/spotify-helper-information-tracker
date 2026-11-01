"""Compatibility entry point for scripts/analytics/build_stats.py."""
from pathlib import Path

_source = Path(__file__).resolve().parent / "scripts" / "analytics" / "build_stats.py"
exec(compile(_source.read_text(encoding="utf-8"), str(_source), "exec"), globals())
