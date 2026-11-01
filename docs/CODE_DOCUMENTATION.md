# Code Documentation Standards

SHIT uses documentation at three levels:

1. **Module docstrings** explain each Python file's responsibility, important inputs and outputs, safety boundaries, and relationship to canonical data.
2. **Function and class docstrings** explain public interfaces, non-obvious behavior, units, return values, and meaningful failure cases. Add them where they clarify the contract; avoid restating an obvious function name.
3. **Inline comments** explain *why* a non-obvious decision exists, especially identity matching, provenance, rate limits, data-quality rules, and safeguards. Do not narrate straightforward syntax.

## Repository conventions

- Keep implementation documentation beside the implementation in `scripts/`.
- Keep compatibility entry points in `compat/` lightweight; their module docstrings should identify the canonical implementation they forward to.
- Keep test module docstrings focused on the behavior or contract being verified.
- Keep operational guides and longer explanations in `docs/`, with links from the README where useful.
- Use native comment syntax for configuration and workflow files when a comment adds operational context.
- Do not insert comments into generated JSON, JSONL, CSV, or source archives. Their schemas and provenance belong in adjacent documentation or manifests.
- Keep documentation factual and synchronized with actual behavior. In particular, distinguish Last.fm scrobbles from measured Spotify playback, and sourced metadata from locally measured audio features.

## Adding or changing a module

When introducing a Python module, begin with a concise module docstring. Document externally used functions and non-obvious data contracts. Update the relevant guide and tests in the same change when behavior, inputs, outputs, or operational requirements change.
