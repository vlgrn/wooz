```
██╗    ██╗ ██████╗  ██████╗ ███████╗
██║    ██║██╔═══██╗██╔═══██╗╚══███╔╝
██║ █╗ ██║██║   ██║██║   ██║  ███╔╝
██║███╗██║██║   ██║██║   ██║ ███╔╝
╚███╔███╔╝╚██████╔╝╚██████╔╝███████╗
 ╚══╝╚══╝  ╚═════╝  ╚═════╝ ╚══════╝
```

**AI DJ for your terminal.**

wooz looks at what you're working on (your project + your recent Claude Code session), picks a track that matches the vibe, and plays it in Spotify. Then it stays open as a chat — type what you want and it picks again.

---

## Install

```bash
uv tool install git+https://github.com/vlgrn/wooz
```

Requires:
- macOS
- Spotify desktop app (free or Premium)
- An [Anthropic API key](https://console.anthropic.com/settings/keys) (wooz asks on first run, saves it to `~/.wooz/.env`)

---

## Use

```bash
cd <your-project>
wooz
```

That's the whole flow. wooz reads context, picks a track, plays it, then drops you into a prompt with a live progress bar.

In the prompt, type anything:

```
❯ more upbeat
❯ play Tame Impala
❯ something with vocals
❯ pick a deep cut from the 70s
```

Or use a slash command:

| Command | What it does |
|---|---|
| `/next` | Play a different track |
| `/pause` | Pause |
| `/play` | Resume |
| `/vibe` | Show the current vibe |
| `/help` | Show commands |
| `/exit` | Quit (also `/quit`, `/q`, Ctrl+D) |
