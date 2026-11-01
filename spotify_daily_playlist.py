"""Compatibility entry point for scripts/spotify/spotify_daily_playlist.py."""
from pathlib import Path

_source = Path(__file__).resolve().parent / "scripts" / "spotify" / "spotify_daily_playlist.py"
exec(compile(_source.read_text(encoding="utf-8"), str(_source), "exec"), globals())
