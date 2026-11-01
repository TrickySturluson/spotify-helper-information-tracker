"""Compatibility entry point for scripts/lastfm/update_lastfm.py."""
from pathlib import Path

_source = Path(__file__).resolve().parent / "scripts" / "lastfm" / "update_lastfm.py"
exec(compile(_source.read_text(encoding="utf-8"), str(_source), "exec"), globals())
