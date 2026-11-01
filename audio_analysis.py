"""Compatibility entry point for scripts/music/audio_analysis.py."""
from pathlib import Path

_source = Path(__file__).resolve().parent / "scripts" / "music" / "audio_analysis.py"
exec(compile(_source.read_text(encoding="utf-8"), str(_source), "exec"), globals())
