```
██╗    ██╗ ██████╗  ██████╗ ███████╗
██║    ██║██╔═══██╗██╔═══██╗╚══███╔╝
██║ █╗ ██║██║   ██║██║   ██║  ███╔╝
██║███╗██║██║   ██║██║   ██║ ███╔╝
╚███╔███╔╝╚██████╔╝╚██████╔╝███████╗
 ╚══╝╚══╝  ╚═════╝  ╚═════╝ ╚══════╝
```

**AI DJ for your terminal — reads what you are working on, plays the right music.**

`wooz` is a chat-style CLI. It reads your current project + recent Claude Code session, picks one track that matches the vibe, plays it in Spotify, and drops you into a chat where you can ask for the next track, pause, or shift the vibe — all without leaving the terminal.

---

## Quick start

```bash
uv tool install git+https://github.com/valentingarnier/wooz
cd <your-project>
wooz
```

That's it. First run prompts you once for an [Anthropic API key](https://console.anthropic.com/settings/keys) (saved to `~/.wooz/.env` so you never have to do it again). No Spotify dev app. No client IDs. No OAuth dance.

You need:
- macOS (Linux/Windows support coming)
- Spotify Premium (Spotify's requirement, not ours)
- The Spotify desktop app installed (wooz auto-launches it if needed)

---

## What it looks like

```
$ wooz
[banner]
✓ anthropic key ready
✓ spotify ready

▶ read_project_context
  ⎿ project=wooz · branch=main · 5 recent commits
    files: .py(11), .md(2), .yml(2)
▶ read_claude_session
  ⎿ 20 messages · latest [user]: lets ship the readme
▶ spotify_search (query='minimal hypnotic electronic for focused coding')
  ⎿ 10 tracks · ♪ Says — Nils Frahm  · ♪ Modularity — Cignol  · ...
▶ spotify_play_track
  ⎿ ♪ now playing: Says — Nils Frahm

type /help for commands, or just chat in natural language
> /next
[searches again, plays a different track in the same vibe]
> more upbeat
[shifts the vibe to something with more energy]
> /pause
⏸  paused
> /exit
bye.
```

---

## Commands

| Command | What it does |
|---|---|
| `/next` | Re-read context, search, play a new track in the current vibe |
| `/pause` | Pause the current track |
| `/play` | Resume |
| `/vibe` | Show the current vibe |
| `/help` | List commands |
| `/exit` (also `/quit`, `/q`, Ctrl+D) | Quit |
| _anything else_ | Free-form hint passed to the agent: `more chill`, `something with vocals`, `pick a deep cut from the 70s` |

CLI flags:

```bash
wooz                     # default
wooz --mood "energetic"  # hint for the first track
wooz --verbose           # show Claude's full reasoning inline
wooz version
```

---

## How it works

```
┌────────────────────────────────────────────────────────────┐
│  wooz                                                      │
│                                                            │
│   ┌─────────────┐    ┌─────────┐    ┌──────────────────┐   │
│   │   Claude    │───▶│  tools  │───▶│ Spotify search   │   │
│   │ tool-use    │◀───│         │◀───│  (catalog API)   │   │
│   │   loop      │    │         │    └──────────────────┘   │
│   └─────────────┘    │         │    ┌──────────────────┐   │
│                      │         │───▶│  AppleScript     │   │
│                      │         │    │  ↳ Spotify.app   │   │
│                      │         │    └──────────────────┘   │
│                      │         │    ┌──────────────────┐   │
│                      │         │───▶│ project context  │   │
│                      │         │    │  (cwd, git, fs) │   │
│                      │         │    └──────────────────┘   │
│                      │         │    ┌──────────────────┐   │
│                      └─────────┘───▶│ Claude Code      │   │
│                                     │  session (jsonl) │   │
│                                     └──────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

**Tools Claude has access to:**

| Tool | What it does |
|---|---|
| `read_project_context` | cwd, project name, git branch, last 5 commits, top file extensions, README excerpt |
| `read_claude_session` | recent user/assistant messages from `~/.claude/projects/<encoded-cwd>/<session>.jsonl` |
| `spotify_search` | Spotify catalog search via app-credentials flow — no per-user OAuth |
| `spotify_play_track` | start one track on the local Spotify desktop app via AppleScript |

After the first run, every `/next` or natural-language hint kicks off a fresh agent loop with the **current vibe + recently played URIs** injected into the prompt. The agent picks a different track in the same mood (or shifts it when you ask).

---

## Why there is no Spotify setup

Spotify locked down their Web API in Feb 2026: new dev apps can no longer write playlists or control playback for arbitrary users, and Extended Quota Mode is denied to individuals.

`wooz` works around this by:

- Using **`client_credentials` for search** — a single shared app key baked into wooz. It only authorises catalog reads, no user data passes through, no per-user dev app needed.
- Using **AppleScript for playback** — wooz tells your local Spotify desktop app to play a track directly. Same mechanism as the keyboard play/pause shortcuts.

The trade-off: macOS only for now. Linux (MPRIS) and Windows are on the roadmap.

---

## Tech stack

- **Python 3.12**, packaged with **uv**
- **Anthropic SDK** with extended-thinking enabled
- **Typer** + **Rich** for CLI + terminal UI
- **spotipy** for catalog search (`client_credentials` flow only)
- **AppleScript** via `osascript` for local playback
- **Pydantic v2** for context models
- Lint/format/typecheck: **ruff**, **mypy** strict
- semantic-release CI on every push to `main`

---

## Roadmap

- Linux + Windows playback (MPRIS, SMTC)
- Auto-advance (poll Spotify state, play next track when one ends)
- Remember vibes / taste across sessions
- More tools: `spotify_skip`, `spotify_queue` (if Spotify reopens the API)

---

## Inspiration

`wooz` started as a weekend project inspired by [@steipete](https://github.com/steipete)'s [spogo](https://github.com/openclaw/spogo) — proof that terminal-native Spotify control is still the cleanest UI.

---

## License

MIT
