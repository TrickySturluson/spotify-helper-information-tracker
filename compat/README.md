# Compatibility entry points

This directory contains small legacy command and import shims. Each shim delegates to its maintained implementation in `../scripts/`.

Run a tool with `python compat/TOOL_NAME.py`. The root `sitecustomize.py` keeps legacy imports working for the test suite and existing internal modules.


## File overview
This document explains the compatibility entry-point policy and usage. Use the individual file overviews in the implementation tree for module-specific details.
