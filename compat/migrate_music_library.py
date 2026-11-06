#!/usr/bin/env python3
"""Compatibility launcher for the local-only music library migration."""
from pathlib import Path
import runpy
import sys
if __name__ == "__main__":
    script = Path(__file__).resolve().parents[1] / "scripts" / "music" / "migrate_music_library.py"
    sys.path.insert(0, str(script.parent))
    runpy.run_path(str(script), run_name="__main__")

# FILE OVERVIEW
# Purpose: Backward-compatible launcher for the earlier Library migration command.
# Delegation: Imports and executes scripts/music/migrate_music_library.py.
# Behavior: Keeps the established compat/ entry point while the maintained implementation
#           and migration rules live under scripts/music/.
# Safety: No Spotify playlist writes; review the migration's dry-run/report before applying.
# Run: python compat/migrate_music_library.py (repository root; see CLI help).
# Related: scripts/music/migrate_music_library.py; docs/GREAT_MIGRATION.md.
# -----------------------------------------------------------------------------
