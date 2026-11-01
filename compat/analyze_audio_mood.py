"""Compatibility entry point for optional local DEAM audio mood inference."""
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "compat") not in sys.path:
    sys.path.insert(0, str(_ROOT / "compat"))
_source = _ROOT / "scripts" / "music" / "analyze_audio_mood.py"
__file__ = str(_ROOT / "analyze_audio_mood.py")
exec(compile(_source.read_text(encoding="utf-8"), __file__, "exec"), globals())


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Legacy-compatible entry point for local DEAM valence/arousal inference.
# Location: Maintained implementation in scripts/music/analyze_audio_mood.py.
# Safety: Requires local legal audio and explicit non-commercial model acknowledgement.
# Run: python compat/analyze_audio_mood.py <audio-folder> --accept-noncommercial-license
# Related: docs/AUDIO_MOOD_MODELS.md; tests/test_analyze_audio_mood.py.
# -----------------------------------------------------------------------------
