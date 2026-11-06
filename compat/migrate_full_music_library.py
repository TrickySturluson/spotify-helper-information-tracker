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
# Purpose: Backward-compatible command-line launcher for the full canonical Library migration.
# Delegation: Imports and executes scripts/music/migrate_full_music_library.py.
# Behavior: Preserves the established compat/ command path; all migration logic lives
#           in the maintained scripts/music implementation.
# Safety: No-network migration; does not write to Spotify playlists.
# Run: python compat/migrate_full_music_library.py --dry-run (or documented apply mode).
# Related: scripts/music/migrate_full_music_library.py; docs/PER_RECORDING_MUSIC_LIBRARY.md.
# -----------------------------------------------------------------------------
