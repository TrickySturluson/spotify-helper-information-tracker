"""Compatibility entry point for the maintained listening-trends module."""
from pathlib import Path
import sys
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts" / "spotify"))
from spotify_listening_trends import *  # noqa: F401,F403
from spotify_listening_trends import generate

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scrobbles", type=Path, default=SCROBBLES)
    parser.add_argument("--profiles", type=Path, default=PROFILES)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    report = generate(args.scrobbles, args.profiles, args.output)
    print("Listening trends generated:", report["coverage"]["status"])

# FILE OVERVIEW
# Purpose: Legacy CLI/import entry point for the maintained listening-trends module.
# Related: scripts/spotify/spotify_listening_trends.py and docs/TRICKY_DAILY_CYCLE.md.
