#!/usr/bin/env python3
"""Compatibility import for the normalized music library."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.music.music_library import *  # noqa: F401,F403

# FILE OVERVIEW
# Purpose: Backward-compatible import/command surface for the canonical music Library API.
# Delegation: Re-exports the maintained implementation from scripts/music/music_library.py.
# Behavior: Contains no duplicate identity-resolution or record-write logic; new code should
#           import the scripts.music implementation directly where practical.
# Safety: Preserve stable IDs, aliases, provenance and canonical per-record storage semantics.
# Related: scripts/music/music_library.py; docs/PER_RECORDING_MUSIC_LIBRARY.md.
# -----------------------------------------------------------------------------
