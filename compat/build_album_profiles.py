#!/usr/bin/env python3
"""Compatibility entry point for the maintained album-profile enrichment script."""
from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts" / "music" / "build_album_profiles.py"), run_name="__main__")


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Legacy-compatible entry point for incremental Last.fm album profiles.
# Location: Maintained implementation in scripts/music/build_album_profiles.py.
# Run: python compat/build_album_profiles.py
# Related: tests/test_build_album_profiles.py; docs/TRANSITION_SCORING.md.
# -----------------------------------------------------------------------------
