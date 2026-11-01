"""Compatibility entry point for scripts/music/enrich_musicbrainz_recording_ids.py."""
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "compat") not in sys.path:
    sys.path.insert(0, str(_ROOT / "compat"))
_source = _ROOT / "scripts" / "music" / "enrich_musicbrainz_recording_ids.py"
__file__ = str(_ROOT / "enrich_musicbrainz_recording_ids.py")
exec(compile(_source.read_text(encoding="utf-8"), __file__, "exec"), globals())
