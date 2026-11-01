"""Compatibility entry point for scripts/music/mood_inference.py."""
from pathlib import Path

_source = Path(__file__).resolve().parent / "scripts" / "music" / "mood_inference.py"
exec(compile(_source.read_text(encoding="utf-8"), str(_source), "exec"), globals())
