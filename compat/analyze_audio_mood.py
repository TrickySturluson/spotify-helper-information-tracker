#!/usr/bin/env python3
"""Compatibility entry point for optional local DEAM audio mood inference."""
from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts" / "music" / "analyze_audio_mood.py"), run_name="__main__")


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Legacy-compatible entry point for local DEAM valence/arousal inference.
# Location: Maintained implementation in scripts/music/analyze_audio_mood.py.
# Safety: Requires local legal audio and explicit non-commercial model acknowledgement.
# Run: python compat/analyze_audio_mood.py <audio-folder> --accept-noncommercial-license
# Related: docs/AUDIO_MOOD_MODELS.md; tests/test_analyze_audio_mood.py.
# -----------------------------------------------------------------------------
