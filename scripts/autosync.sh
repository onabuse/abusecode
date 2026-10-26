#!/usr/bin/env bash
# Manage the auto commit + push watcher.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PIDFILE="$ROOT/.git/autosync.pid"
LOG="$ROOT/.git/autosync.log"

running() {
  [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE" 2>/dev/null)" 2>/dev/null
}

case "${1:-status}" in
  start)
    if running; then echo "already running (pid $(cat "$PIDFILE"))"; exit 0; fi
    python3 - "$ROOT" "$LOG" "$PIDFILE" <<'PY'
import os, subprocess, sys
root, log, pidfile = sys.argv[1:4]
fh = open(log, "a")
p = subprocess.Popen(
    [sys.executable, os.path.join(root, "scripts", "autosync.py")],
    cwd=root, stdin=subprocess.DEVNULL, stdout=fh, stderr=fh,
    start_new_session=True,
)
open(pidfile, "w").write(str(p.pid))
print(f"started (pid {p.pid}) — tail -f {log}")
PY
    ;;
  stop)
    if ! running; then echo "not running"; rm -f "$PIDFILE"; exit 0; fi
    kill "$(cat "$PIDFILE")" 2>/dev/null || true
    rm -f "$PIDFILE"
    echo "stopped"
    ;;
  restart)
    "$0" stop || true
    sleep 1
    "$0" start
    ;;
  status)
    if running; then echo "running (pid $(cat "$PIDFILE"))"; else echo "stopped"; fi
    ;;
  *)
    echo "usage: $0 {start|stop|restart|status}" >&2
    exit 1
    ;;
esac
