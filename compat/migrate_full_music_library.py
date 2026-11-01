#!/usr/bin/env python3
"""Compatibility launcher for the full offline music-library migration."""
from pathlib import Path
import runpy
import sys
if __name__ == "__main__":
    script = Path(__file__).resolve().parents[1] / "scripts" / "music" / "migrate_full_music_library.py"
    sys.path.insert(0, str(script.parent))
    runpy.run_path(str(script), run_name="__main__")

# FILE OVERVIEW
# Launches the full no-network migration of stored track profiles and
# accessible Spotify playlist snapshots into The Library.
