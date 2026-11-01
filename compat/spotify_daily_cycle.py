"""Compatibility entry point for the maintained Tricky Daily cycle runner."""
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
_SOURCE = _ROOT / "scripts" / "spotify" / "spotify_daily_cycle.py"
sys.path.insert(0, str(_ROOT / "scripts" / "spotify"))
__file__ = str(_SOURCE)
exec(compile(_SOURCE.read_text(encoding="utf-8"), __file__, "exec"), globals())


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Legacy import and command entry point for the Tricky Daily midnight cycle.
# Role: Compatibility layer only; canonical implementation lives under scripts/.
# Run: python compat/spotify_daily_cycle.py [--force]
# Related: See docs/TRICKY_DAILY_CYCLE.md and scripts/spotify/spotify_daily_cycle.py.
# -----------------------------------------------------------------------------
