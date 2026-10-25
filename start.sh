#!/usr/bin/env bash
set -o errexit

PORT="${PORT:-8000}"
echo "==> Starting AI LifePilot on port ${PORT}..."
exec python -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port "${PORT}"
