"""Compatibility entry point for scripts/music/lyrics_library.py."""
from pathlib import Path

_source = Path(__file__).resolve().parent / "scripts" / "music" / "lyrics_library.py"
exec(compile(_source.read_text(encoding="utf-8"), str(_source), "exec"), globals())
