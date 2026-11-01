"""Compatibility entry point for scripts/spotify/track_playlist_removals.py."""
from pathlib import Path

_source = Path(__file__).resolve().parent / "scripts" / "spotify" / "track_playlist_removals.py"
exec(compile(_source.read_text(encoding="utf-8"), str(_source), "exec"), globals())
