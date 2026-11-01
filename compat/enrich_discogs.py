"""Compatibility entry point for scripts/music/enrich_discogs.py."""
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "compat") not in sys.path:
    sys.path.insert(0, str(_ROOT / "compat"))
_source = _ROOT / "scripts" / "music" / "enrich_discogs.py"
__file__ = str(_ROOT / "enrich_discogs.py")
exec(compile(_source.read_text(encoding="utf-8"), __file__, "exec"), globals())


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Compatibility entry point for scripts/music/enrich_discogs.py.
# Role: Compatibility layer only; all business logic lives in scripts/music/.
# Delegation: scripts/music/enrich_discogs.py
# Use: python compat/enrich_discogs.py (requires DISCOGS_USER_TOKEN).
# Related: docs/AUTOMATED_AUDIO_METADATA.md and tests/test_enrich_discogs.py.
# -----------------------------------------------------------------------------
