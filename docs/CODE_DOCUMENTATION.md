# Code Documentation Standards

SHIT uses documentation at three levels:

1. **Bottom-of-file overviews** are the primary navigation aid. Every maintained Python implementation, compatibility entry point, test module, and workflow should end with a clearly labeled `FILE OVERVIEW` block that explains purpose, role, inputs/outputs or delegation, how to run it when applicable, and related files.
2. **Module docstrings** provide a concise summary at the top of Python modules.
3. **Function and class docstrings / inline comments** explain public interfaces, non-obvious behavior, units, return values, meaningful failure cases, and *why* important decisions exist.

## Repository conventions

- The bottom overview should read like a miniature README, not merely repeat the filename. Include concrete data flow, side effects, commands, safeguards, and related modules where relevant.
- Keep implementation documentation beside the implementation in `scripts/`.
- Keep `compat/` launchers lightweight; their overview must name the canonical implementation they delegate to.
- Test overviews should name the behavior under test and show a valid command from the repository root.
- Workflow overviews should describe triggers, key steps, required secrets/permissions, and the implementation they automate.
- Markdown guides are themselves documentation; avoid redundant footer summaries when the document already explains its subject.
- Do not insert comments into generated JSON, JSONL, CSV, or source archives. Document their schemas and provenance in adjacent guides or manifests.
- Keep documentation factual and synchronized with actual behavior. Distinguish Last.fm scrobbles from measured Spotify playback, and sourced metadata from locally measured audio features.

## Adding or changing a module

When introducing a Python module, add a concise module docstring and a bottom `FILE OVERVIEW` block. Document externally used functions and non-obvious data contracts. Update the relevant guide and tests in the same change when behavior, inputs, outputs, or operational requirements change.
