"""Compatibility entry point for scripts/music/enrich_getsongbpm.py."""
from pathlib import Path

_source = Path(__file__).resolve().parent / "scripts" / "music" / "enrich_getsongbpm.py"
exec(compile(_source.read_text(encoding="utf-8"), str(_source), "exec"), globals())
