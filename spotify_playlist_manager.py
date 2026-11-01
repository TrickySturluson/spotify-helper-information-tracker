"""Compatibility entry point for scripts/spotify/spotify_playlist_manager.py."""
from pathlib import Path

_source = Path(__file__).resolve().parent / "scripts" / "spotify" / "spotify_playlist_manager.py"
exec(compile(_source.read_text(encoding="utf-8"), str(_source), "exec"), globals())
