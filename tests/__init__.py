"""Test package bootstrap for the repository's compatibility modules."""
import sys
from pathlib import Path

_COMPAT = Path(__file__).resolve().parents[1] / "compat"
if str(_COMPAT) not in sys.path:
    sys.path.insert(0, str(_COMPAT))
