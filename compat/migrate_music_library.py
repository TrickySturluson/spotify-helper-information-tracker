#!/usr/bin/env python3
"""Compatibility launcher for the local-only music library migration."""
from pathlib import Path
import runpy
if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts" / "music" / "migrate_music_library.py"), run_name="__main__")

# FILE OVERVIEW
# - Launches the no-network migration from the established compat/ command surface.
