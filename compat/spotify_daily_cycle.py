"""Compatibility entry point for the maintained Tricky Daily cycle runner."""
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
_SOURCE = _ROOT / "scripts" / "spotify" / "spotify_daily_cycle.py"
sys.path.insert(0, str(_ROOT / "scripts" / "spotify"))
__file__ = str(_SOURCE)
exec(compile(_SOURCE.read_text(encoding="utf-8"), __file__, "exec"), globals())
