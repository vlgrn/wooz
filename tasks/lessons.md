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

## README video embeds: GIF, not `<video>` tag with raw repo URL

GitHub's README markdown renderer strips/sandboxes `<video src="https://github.com/owner/repo/raw/...">`
due to CSP — the player won't load, even though the URL resolves. For inline demos
that "just work," use a GIF via `<img src="...gif">` (markdown image syntax always
renders) and wrap it in an `<a href="...mp4">` so clicking opens the full mp4.

The only `<video>` source GitHub honors is `user-images.githubusercontent.com` URLs
produced when you drag a file into a PR/issue comment on github.com.

**Trigger:** any README change embedding a video.

## shields.io stars badge: avoid `?style=social`

The `?style=social` variant of `img.shields.io/github/stars/...` hits an authenticated
GitHub API path on shields.io's side and intermittently fails with "Unable to select
next GitHub token from pool." Default flat style (`?label=Stars&logo=github` if you
want the icon) uses a different, more reliable code path.

**Trigger:** any new shields.io badge that pulls live GitHub data (stars, forks, issues).
