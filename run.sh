#!/usr/bin/env bash
# abusecode.router — start the proxy + dashboard
set -e
cd "$(dirname "$0")"
exec uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}" "$@"
