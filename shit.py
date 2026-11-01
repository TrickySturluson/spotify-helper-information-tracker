#!/usr/bin/env python3
"""Spotify Helper & Information Tracker command-line entry point."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.music.library_cli import main

if __name__ == "__main__":
    raise SystemExit(main())

# FILE OVERVIEW
# Purpose: Single native command entry point for Spotify Helper & Information Tracker (SHIT).
# Usage: python shit.py library status|preview|migrate|audit
# Feature logic lives in scripts/; this file only establishes the repository import path
# and delegates to the maintained command implementation.
