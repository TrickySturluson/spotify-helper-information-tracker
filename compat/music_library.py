#!/usr/bin/env python3
"""Compatibility import for the normalized music library."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "music"))
from music_library import *  # noqa: F401,F403

# File overview
# - Exposes the canonical music-library API to legacy compat/ entrypoints and tests.
