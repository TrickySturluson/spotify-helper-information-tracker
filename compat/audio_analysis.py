"""Compatibility entry point for scripts/music/audio_analysis.py."""
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "compat") not in sys.path:
    sys.path.insert(0, str(_ROOT / "compat"))
_source = _ROOT / "scripts" / "music" / "audio_analysis.py"
__file__ = str(_ROOT / "audio_analysis.py")
exec(compile(_source.read_text(encoding="utf-8"), __file__, "exec"), globals())


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Compatibility entry point for scripts/music/audio_analysis.py.
# Role: Compatibility layer only; this file is not the source of business logic.
# Delegation: scripts/music/audio_analysis.py
# Use: Run this legacy entry point to preserve older commands/import names.
# Maintenance: Put all new behavior in the delegated scripts/ implementation.
# Related: See scripts/README.md for package layout and docs/ for feature guides.
# -----------------------------------------------------------------------------
