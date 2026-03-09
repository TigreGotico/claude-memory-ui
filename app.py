"""
claude-memory-ui — Web UI for Claude Code memories, plans, and project sessions.

Reads from (and writes to) ~/.claude/ by default.
Override with --claude-dir or the CLAUDE_DIR env variable.
"""

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ── configuration ─────────────────────────────────────────────────────────────

def _resolve_claude_dir() -> Path:
    env = os.environ.get("CLAUDE_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return Path.home() / ".claude"


CLAUDE_DIR = _resolve_claude_dir()
PLANS_DIR = CLAUDE_DIR / "plans"
PROJECTS_DIR = CLAUDE_DIR / "projects"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"

STATIC_DIR = Path(__file__).parent / "static"

# ── app ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Claude Memory UI",
    description="Browser UI for viewing and editing Claude Code memories, plans, and sessions.",
    version="0.1.0",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ── helpers ───────────────────────────────────────────────────────────────────

def slug_to_human_path(slug: str) -> str:
    """
    Claude stores project dirs as slugified absolute paths, e.g.
      -home-alice-projects-myrepo  →  /home/alice/projects/myrepo

    The slug is produced by replacing every '/' with '-', which means
    dashes inside directory names are indistinguishable from path separators.
    We cannot reconstruct the exact path, so we return the best-effort
    human-readable form and let the UI display it verbatim.
    """
    return "/" + slug.lstrip("-").replace("-", "/")


def safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        return f"[Error reading file: {exc}]"


def count_lines(path: Path) -> int:
    try:
        return sum(1 for _ in path.open("rb"))
    except Exception:
        return 0


# ── routes — plans ────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/plans")
async def list_plans():
    plans = []
    if PLANS_DIR.exists():
        for f in sorted(PLANS_DIR.glob("*.md")):
            content = safe_read(f)
            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else f.stem
            stat = f.stat()
            plans.append({
                "id": f.stem,
                "filename": f.name,
                "title": title,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
    return plans


@app.get("/api/plans/{plan_id}")
async def get_plan(plan_id: str):
    path = PLANS_DIR / f"{plan_id}.md"
    if not path.exists():
        raise HTTPException(404, "Plan not found")
    return {"id": plan_id, "content": safe_read(path)}


class SaveBody(BaseModel):
    content: str


@app.put("/api/plans/{plan_id}")
async def save_plan(plan_id: str, body: SaveBody):
    path = PLANS_DIR / f"{plan_id}.md"
    if not path.exists():
        raise HTTPException(404, "Plan not found")
    path.write_text(body.content, encoding="utf-8")
    return {"ok": True}


@app.delete("/api/plans/{plan_id}")
async def delete_plan(plan_id: str):
    path = PLANS_DIR / f"{plan_id}.md"
    if not path.exists():
        raise HTTPException(404, "Plan not found")
    path.unlink()
    return {"ok": True}


# ── routes — projects & memory ────────────────────────────────────────────────

@app.get("/api/projects")
async def list_projects():
    projects = []
    if not PROJECTS_DIR.exists():
        return projects

    for entry in sorted(PROJECTS_DIR.iterdir()):
        if not entry.is_dir():
            continue

        sessions = sorted(
            (f for f in entry.glob("*.jsonl") if f.is_file()),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        memory_file = entry / "memory" / "MEMORY.md"

        projects.append({
            "slug": entry.name,
            "path": slug_to_human_path(entry.name),
            "sessions": [
                {
                    "id": s.stem,
                    "messages": count_lines(s),
                    "modified": datetime.fromtimestamp(s.stat().st_mtime).isoformat(),
                    "size": s.stat().st_size,
                }
                for s in sessions
            ],
            "session_count": len(sessions),
            "has_memory": memory_file.exists(),
            "memory_preview": safe_read(memory_file)[:300] if memory_file.exists() else None,
        })

    return projects


@app.get("/api/projects/{slug}/memory")
async def get_memory(slug: str):
    path = PROJECTS_DIR / slug / "memory" / "MEMORY.md"
    if not path.exists():
        raise HTTPException(404, "No memory file for this project")
    return {"slug": slug, "content": safe_read(path)}


@app.put("/api/projects/{slug}/memory")
async def save_memory(slug: str, body: SaveBody):
    path = PROJECTS_DIR / slug / "memory" / "MEMORY.md"
    if not path.exists():
        raise HTTPException(404, "No memory file for this project")
    path.write_text(body.content, encoding="utf-8")
    return {"ok": True}


@app.get("/api/projects/{slug}/sessions/{session_id}")
async def get_session(slug: str, session_id: str):
    path = PROJECTS_DIR / slug / f"{session_id}.jsonl"
    if not path.exists():
        raise HTTPException(404, "Session not found")

    messages = []
    try:
        with path.open(encoding="utf-8") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                inner = obj.get("message") if isinstance(obj.get("message"), dict) else {}
                role = inner.get("role")
                content = inner.get("content")

                text = ""
                if isinstance(content, str):
                    text = content[:500]
                elif isinstance(content, list):
                    parts = []
                    for block in content:
                        if not isinstance(block, dict):
                            continue
                        btype = block.get("type")
                        if btype == "text":
                            parts.append(block.get("text", "")[:300])
                        elif btype == "tool_use":
                            parts.append(f"[tool: {block.get('name')}]")
                        elif btype == "tool_result":
                            parts.append("[tool_result]")
                    text = " ".join(parts)[:500]

                messages.append({
                    "type": obj.get("type"),
                    "role": role,
                    "text": text,
                })
    except Exception as exc:
        raise HTTPException(500, str(exc))

    return {"session_id": session_id, "messages": messages}


# ── routes — settings ─────────────────────────────────────────────────────────

@app.get("/api/settings")
async def get_settings():
    if not SETTINGS_FILE.exists():
        return {}
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Claude Memory UI")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=7373, help="Port to listen on (default: 7373)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (dev mode)")
    parser.add_argument(
        "--claude-dir",
        default=None,
        help="Path to Claude data directory (default: ~/.claude). Also reads CLAUDE_DIR env var.",
    )
    args = parser.parse_args()

    if args.claude_dir:
        # override the module-level paths at startup
        import app as self_module
        base = Path(args.claude_dir).expanduser().resolve()
        self_module.CLAUDE_DIR = base
        self_module.PLANS_DIR = base / "plans"
        self_module.PROJECTS_DIR = base / "projects"
        self_module.SETTINGS_FILE = base / "settings.json"

    print(f"Claude Memory UI  →  http://{args.host}:{args.port}")
    print(f"Reading from: {CLAUDE_DIR}")
    uvicorn.run("app:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
