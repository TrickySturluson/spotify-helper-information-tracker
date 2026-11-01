"""Compatibility entry point for scripts/spotify/playlist_feedback_calibration.py."""
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "compat") not in sys.path:
    sys.path.insert(0, str(_ROOT / "compat"))
_source = _ROOT / "scripts" / "spotify" / "playlist_feedback_calibration.py"
__file__ = str(_ROOT / "playlist_feedback_calibration.py")
exec(compile(_source.read_text(encoding="utf-8"), __file__, "exec"), globals())


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Compatibility entry point for the playlist-fit calibration module.
# Role: Compatibility layer only; canonical implementation lives under scripts/.
# Delegation: scripts/spotify/playlist_feedback_calibration.py
# Related: See docs/PLAYLIST_FEEDBACK_CALIBRATION.md.
# -----------------------------------------------------------------------------
