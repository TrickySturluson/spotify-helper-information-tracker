# Compatibility entry points

This directory contains small legacy command and import shims. Each shim delegates to its maintained implementation in `../scripts/`.

Run a tool with `python compat/TOOL_NAME.py`. The root `sitecustomize.py` keeps legacy imports working for the test suite and existing internal modules.


## File overview
This document explains the compatibility entry-point policy and usage. Use the individual file overviews in the implementation tree for module-specific details.

- `playlist_feedback_calibration.py` — Legacy import shim for the maintained playlist-fit calibration module.

- `spotify_daily_cycle.py` — Launches the DST-aware Tricky Daily rotation at midnight America/New_York; `--force` is for intentional manual runs.
