# claude-memory-ui

A local web UI for viewing and managing [Claude Code](https://claude.ai/code) data — memories, plans, project sessions, and settings — all from a single browser tab.

> **Reads and writes directly from `~/.claude/`** — no sync, no cloud, no API key required.

---

> [!WARNING]
> **100% vibe coded.** This entire project — backend, frontend, and the README you are reading right now — was generated in a single Claude Code session with zero human-written code. It works on the author's machine. It has no tests. The error handling is optimistic at best. The Markdown renderer in the frontend is a pile of regex. The slug-to-path decoder is documented as "best-effort" because it genuinely cannot do better. If something breaks, that's between you and the vibes. PRs welcome.

---

## Features

| Tab | What it does |
|---|---|
| **Plans** | View, edit, and delete Claude Code plan files (`~/.claude/plans/*.md`) with live Markdown preview |
| **Memory** | Browse every project's `MEMORY.md`, read and edit them in-place |
| **Projects** | Card grid of all projects with session counts; click into any session to inspect the message history |
| **Settings** | Pretty-print `~/.claude/settings.json` |

---

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) **or** pip
- [Claude Code](https://claude.ai/code) installed and used at least once (so `~/.claude/` exists)

---

## Installation & usage

### Quickest — run directly with `uvx`

```bash
uvx --from git+https://github.com/OpenVoiceOS/claude-memory-ui claude-memory-ui
```

### From source

```bash
git clone https://github.com/OpenVoiceOS/claude-memory-ui
cd claude-memory-ui
uv sync
uv run claude-memory-ui
```

Then open **http://127.0.0.1:7373** in your browser.

### With pip

```bash
pip install git+https://github.com/OpenVoiceOS/claude-memory-ui
claude-memory-ui
```

---

## CLI options

```
claude-memory-ui [--host HOST] [--port PORT] [--reload] [--claude-dir PATH]

  --host        Bind address (default: 127.0.0.1)
  --port        Port to listen on (default: 7373)
  --reload      Enable hot-reload for development
  --claude-dir  Override the Claude data directory (default: ~/.claude)
                Also reads the CLAUDE_DIR environment variable.
```

Examples:

```bash
# Different port
claude-memory-ui --port 8080

# Expose on LAN (use with caution — no auth)
claude-memory-ui --host 0.0.0.0

# Point at a non-default Claude directory
claude-memory-ui --claude-dir /path/to/other/.claude
```

---

## Data it reads

```
~/.claude/
├── plans/          ← *.md plan files        (read + write)
├── projects/
│   └── <slug>/
│       ├── *.jsonl             ← session message logs  (read-only)
│       └── memory/
│           └── MEMORY.md       ← per-project memory    (read + write)
└── settings.json               ← Claude settings        (read-only)
```

Project directories are named with a slug where `/` is replaced by `-`, e.g.
`/home/alice/projects/myrepo` → `-home-alice-projects-myrepo`.
The UI decodes these back to human-readable paths on a best-effort basis.

---

## Security

The server binds to `127.0.0.1` by default — it is **localhost-only** and not accessible from other machines. Do not expose it on a public interface without adding authentication, as it has full read/write access to your Claude memory and plan files.

---

## Development

```bash
git clone https://github.com/OpenVoiceOS/claude-memory-ui
cd claude-memory-ui
uv sync
uv run claude-memory-ui --reload
```

The UI is a single vanilla-JS file at `static/index.html`. The backend is a single FastAPI file at `app.py`. No build step required.

---

## License

MIT
