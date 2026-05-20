```
██╗    ██╗ ██████╗  ██████╗ ███████╗
██║    ██║██╔═══██╗██╔═══██╗╚══███╔╝
██║ █╗ ██║██║   ██║██║   ██║  ███╔╝
██║███╗██║██║   ██║██║   ██║ ███╔╝
╚███╔███╔╝╚██████╔╝╚██████╔╝███████╗
 ╚══╝╚══╝  ╚═════╝  ╚═════╝ ╚══════╝
```

**AI DJ for your terminal — reads what you are working on, plays the right music.**

`wooz` is a one-shot CLI agent. You run it in a project directory, it reads your code + recent Claude Code session, decides a vibe, finds tracks on Spotify, and starts playing on whatever device you have open. Powered by Claude (tool-use loop) and the Spotify Web API.

---

## What it actually does

```
$ wooz
✓ anthropic key found
✓ spotify authed as valentin

▶ read_project_context
  ⎿ project=wooz · branch=main
    files: .py(11), .md(2), .yml(2)
    latest commit: feat: switch to confidential OAuth and add spotify_play_tracks
▶ read_claude_session  (limit=20)
  ⎿ 20 messages
    latest [assistant]: All green. Smoke-tested end-to-end...
▶ spotify_search  (query='minimal hypnotic electronic for deep focus')
  ⎿ 10 tracks
    ♪ Modularity — Cignol
    ♪ Says — Nils Frahm
    ...
▶ spotify_play_tracks
  ⎿ playing 18 tracks on MacBook Air

Hypnotic, low-friction electronics for focused building.
```

It launches Spotify if it isn't already open. Music starts. You go back to coding.

---

## Quick start

### 1. Install

```bash
uv tool install git+https://github.com/valentingarnier/wooz
```

(Or clone and `uv sync` for development.)

### 2. Get an Anthropic API key

Sign in at https://console.anthropic.com → Settings → API Keys → Create new key.

### 3. Create a Spotify dev app

Spotify locked down their API in Feb 2026, so each user needs their own dev app.

1. Go to https://developer.spotify.com/dashboard → log in (you need **Spotify Premium**)
2. Click **Create app**
   - **Name**: anything (e.g. `wooz`)
   - **Description**: anything
   - **Redirect URI**: `http://127.0.0.1:8765/callback` (exact match, no trailing slash)
   - **APIs**: tick **Web API**
3. Open the app → **Settings** → copy the **Client ID** and **Client Secret**
4. Open the app → **User Management** → add yourself
   - **Name**: your Spotify display name
   - **Email**: your Spotify account email (the one you use to log in)

### 4. Set environment variables

Create a `.env` in your working directory (or export globally):

```env
ANTHROPIC_API_KEY=sk-ant-...
WOOZ_SPOTIFY_CLIENT_ID=your-client-id
WOOZ_SPOTIFY_CLIENT_SECRET=your-client-secret
```

### 5. Run it

```bash
cd <any-project>
wooz
```

First run opens a browser for Spotify OAuth approval. Subsequent runs reuse the cached token at `~/.wooz/spotify.json`.

---

## Usage

```bash
wooz                           # read context, pick a vibe, play
wooz --mood energetic          # override the inferred vibe
wooz --duration 30             # target ~30 minutes of music
wooz --verbose                 # show Claude's full thinking inline
wooz version
```

`wooz` works best when run from inside a project directory you're actively working on — that's where the project signal (file extensions, recent commits) and the Claude Code session signal both live.

---

## How it works

```
┌────────────────────────────────────────────────────────────┐
│  wooz CLI                                                  │
│                                                            │
│   ┌─────────────┐    ┌─────────┐    ┌──────────────────┐   │
│   │   Claude    │───▶│  tools  │───▶│ Spotify Web API  │   │
│   │ tool-use    │◀───│         │◀───│ (search + play)  │   │
│   │   loop      │    │         │    └──────────────────┘   │
│   └─────────────┘    │         │    ┌──────────────────┐   │
│                      │         │───▶│ project context  │   │
│                      │         │    │  (cwd, git, fs)  │   │
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
| `read_project_context` | cwd, project name, git branch, last 5 commits, file extension counts, README excerpt |
| `read_claude_session` | recent user/assistant messages from `~/.claude/projects/<encoded-cwd>/<session>.jsonl` |
| `spotify_search` | Spotify track search, returns URIs |
| `spotify_play_tracks` | starts playback on the best available Spotify Connect device; auto-launches the Spotify app on macOS/Linux if no device is found |

The agent loop is strict (Claude is constrained to a 5-step workflow) so each run is fast and predictable — typically two search calls and a `play_tracks`.

---

## Tech stack

- **Python 3.12**, packaged with **uv**
- **Typer** + **Rich** for CLI + terminal UI
- **Anthropic SDK** with extended-thinking enabled (1024-token budget)
- **spotipy** for confidential OAuth + Web API calls
- **Pydantic v2** for the context models
- Lint/format/typecheck: **ruff**, **mypy** (strict on data models)
- Semantic-release CI on every push to `main`

---

## Notes and limits

- **You need Spotify Premium.** Playback control via Spotify Connect is Premium-only.
- **Dev mode limit: 5 users per Spotify app.** That's a Spotify policy. Each user runs their own dev app — no shared Client ID. Fine for personal use.
- **No playlist creation.** Spotify removed playlist-write endpoints from dev-mode apps in Feb 2026. `wooz` queues tracks for playback instead of creating a saved playlist.
- **macOS / Linux only for auto-launch.** Windows is on the roadmap.
- **Anthropic API costs apply.** Each run uses extended thinking + 5-6 tool turns — typically ~5-10k input tokens, ~1k output tokens.

---

## Inspiration

`wooz` started as a quick weekend project, inspired by [@steipete](https://github.com/steipete)'s [spogo](https://github.com/openclaw/spogo) — a terminal-native Spotify client that proved CLIs are still the best UI for tools you live inside of.

---

## License

MIT
