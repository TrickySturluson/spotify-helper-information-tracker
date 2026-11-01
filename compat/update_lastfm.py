"""Compatibility entry point for scripts/lastfm/update_lastfm.py."""
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "compat") not in sys.path:
    sys.path.insert(0, str(_ROOT / "compat"))
_source = _ROOT / "scripts" / "lastfm" / "update_lastfm.py"
__file__ = str(_ROOT / "update_lastfm.py")
exec(compile(_source.read_text(encoding="utf-8"), __file__, "exec"), globals())


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Compatibility entry point for scripts/lastfm/update_lastfm.py.
# Role: Legacy compatibility entry point; implementation is maintained under scripts/lastfm/.
# Use: Run this file to preserve the historical command/import path.
# Maintenance: Put all new behavior in scripts/lastfm/update_lastfm.py.
# Related: See scripts/README.md and docs/ for the project layout and operational guides.
# -----------------------------------------------------------------------------
