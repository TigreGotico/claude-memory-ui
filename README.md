# claude-memory-ui

A local web UI for viewing and managing [Claude Code](https://claude.ai/code) data: memories, plans, project sessions, and settings, all from a single browser tab.

> **Reads and writes directly from `~/.claude/`.** There is no sync, no cloud, and no API key required.

---

> [!WARNING]
> This entire project (backend, frontend, and this README) was written in a single Claude Code session, with no human-written code. It works on the author's machine. It has no tests. The error handling is optimistic. The Markdown renderer in the frontend is a set of regular expressions.
>
> The slug-to-path decoder is best-effort, because it cannot always recover the original path. If something breaks, report it. Pull requests are welcome.

---

## Features

| Tab | What it does |
|---|---|
| **Plans** | View, edit, and delete Claude Code plan files (`~/.claude/plans/*.md`) with a live Markdown preview |
| **Memory** | Browse every project's `MEMORY.md` file, and read and edit it in place |
| **Projects** | See a card grid of all projects with session counts, and open any session to inspect its message history |
| **Settings** | View `~/.claude/settings.json` in a readable format |

---

## Requirements

- Python 3.10 or newer
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- [Claude Code](https://claude.ai/code), installed and used at least once, so that `~/.claude/` exists

---

## Installation & usage

### Quickest: run directly with `uvx`

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

Then open `http://127.0.0.1:7373` in your browser.

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

# Expose on LAN (use with caution, no auth)
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

Project directories use a slug, where each `/` in the path is replaced with `-`. For example,
`/home/alice/projects/myrepo` becomes `-home-alice-projects-myrepo`.
The UI decodes these slugs back to human-readable paths on a best-effort basis.

---

## Security

The server binds to `127.0.0.1` by default, so it is reachable only from the local machine, not from other machines on the network. Do not expose it on a public interface without adding authentication. It has full read and write access to your Claude memory and plan files.

---

## Development

```bash
git clone https://github.com/OpenVoiceOS/claude-memory-ui
cd claude-memory-ui
uv sync
uv run claude-memory-ui --reload
```

The UI is a single vanilla-JS file at `static/index.html`. The backend is a single FastAPI file at `app.py`. Neither requires a build step.

---

## License

MIT
