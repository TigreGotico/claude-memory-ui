#!/usr/bin/env bash
cd "$(dirname "$0")"
echo "Starting Claude Memory UI at http://127.0.0.1:7373"
uv run uvicorn app:app --host 127.0.0.1 --port 7373 --reload
