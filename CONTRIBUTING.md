# Contributing to the Wendell CLI

Thanks for helping improve the Wendell CLI. This package is the open source
command-line runner published to PyPI as `wendell`.

## Scope

The open source CLI lives in this repository.

The CLI:

- authenticates a local or CI runner
- fetches hosted Wendell suites
- invokes the user's agent adapter
- uploads run traces and prints gate results

The hosted Wendell service, internal suite compiler, scoring service, web app,
and production infrastructure are not part of the public CLI package.

## Development Setup

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]" build twine
```

Run the CLI tests:

```bash
python -m pytest
```

Build and validate the package:

```bash
python -m build
python -m twine check dist/*
```

## Pull Requests

Keep changes focused and include tests for user-visible behavior. If a change
modifies packaged CLI files, bump `[project].version` in `pyproject.toml`
so the package can be published from CI after merge.

Do not commit API keys, customer transcripts, local credentials, generated run
outputs, or production infrastructure credentials.
