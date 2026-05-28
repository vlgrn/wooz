---
name: wooz
description: Pick a song based on what the user is working on in his claude session. Invoke this skill when the user types "wooz".
dependencies:
  - python>=3.12
---

## Overview

wooz is an AI DJ. It reads what you're working on (your project + recent Claude Code session), picks a track that matches the vibe, and plays it in Spotify.

## When to apply

When the user types "wooz", run it in one-shot mode and tell the user what it picked:

```bash
wooz --once
```

For a directed pick, pass a vibe hint:

```bash
wooz --once --mood "deep focus refactor"
```

`wooz --once` picks and plays a single track, then exits.

## Changing the track / chatting

`--once` does NOT stay open — you (the agent) drive the conversation. When the user reacts ("something darker", "too mellow", "next"), turn their request into a short vibe hint and run wooz again, then relay the new pick:

```bash
wooz --once --mood "<the user's request>"
```

Do NOT run plain `wooz` (without `--once`): that launches an interactive REPL which blocks on keyboard input and will hang the agent.

## Requirements

- macOS with the Spotify desktop app open (free or Premium).
- An Anthropic API key. wooz prompts for it on first interactive run and saves it to `~/.wooz/.env`. In `--once` mode it never prompts — if no key is configured it prints an error and exits non-zero.
