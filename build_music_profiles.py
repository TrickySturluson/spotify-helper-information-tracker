"""Compatibility entry point for scripts/music/build_music_profiles.py."""
from pathlib import Path

_source = Path(__file__).resolve().parent / "scripts" / "music" / "build_music_profiles.py"
exec(compile(_source.read_text(encoding="utf-8"), str(_source), "exec"), globals())
