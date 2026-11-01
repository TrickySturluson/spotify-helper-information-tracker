"""Make legacy module imports resolve through the compatibility entry points."""
import sys
from pathlib import Path

_REPOSITORY_ROOT = Path(__file__).resolve().parent
_COMPAT = _REPOSITORY_ROOT / "compat"
if _COMPAT.is_dir() and str(_COMPAT) not in sys.path:
    sys.path.insert(0, str(_COMPAT))


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Add the repository's compat/ directory to Python's startup import path.
# Role: Keeps legacy imports working while maintained code lives under scripts/.
# Safety: Does not execute project commands or modify project data.
# Related: compat/ contains shims; scripts/ contains the canonical implementations.
# -----------------------------------------------------------------------------
