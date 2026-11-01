"""Test package bootstrap for the repository's compatibility modules."""
import sys
from pathlib import Path

_COMPAT = Path(__file__).resolve().parents[1] / "compat"
if str(_COMPAT) not in sys.path:
    sys.path.insert(0, str(_COMPAT))

# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Initialize the test package and expose compatibility modules to tests.
# Behavior: Adds the repository's compat/ directory to sys.path once at import.
# Related: tests/ modules import maintained implementations through compat/.
# -----------------------------------------------------------------------------
