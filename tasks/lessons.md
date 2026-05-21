# Lessons

## Install instructions: pin Python version explicitly

When documenting `uv tool install` for this project, always include `--python 3.12`
(or the current minimum). Without the pin, uv may pick whatever Python is first on
PATH — commonly conda's `(base)` 3.11 — which silently violates
`requires-python = ">=3.12"` and produces a broken install (e.g. `jiter.jiter`
ModuleNotFoundError because the native extension was built for the wrong ABI).

**Trigger:** any change to install docs, release notes, or quickstart commands.

**Mistake to avoid:** writing the bare `uv tool install git+...` form. It works on
the maintainer's machine and fails on users with conda or older system Python.
