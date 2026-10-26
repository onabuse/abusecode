#!/usr/bin/env python3
"""Auto commit + push whenever the working tree changes.

Run detached (see scripts/autosync.sh). Polls `git status --porcelain`
so .gitignore is respected. Safe to stop anytime.
"""
import os
import signal
import subprocess
import sys
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTERVAL = float(os.environ.get("AUTOSYNC_INTERVAL", "8"))
NAME = os.environ.get("AUTOSYNC_NAME", "Saifur Rahman Siam")
EMAIL = os.environ.get("AUTOSYNC_EMAIL", "onabuse@users.noreply.github.com")
_running = True


def run(*args, check=False):
    return subprocess.run(
        args, cwd=ROOT, capture_output=True, text=True, check=check
    )


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def branch():
    r = run("git", "rev-parse", "--abbrev-ref", "HEAD")
    return r.stdout.strip() or "main"


def changed_paths(status):
    paths = []
    for line in status.splitlines():
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path:
            paths.append(path)
    return paths


def commit_push():
    status = run("git", "status", "--porcelain").stdout.strip()
    if not status:
        return False

    count = len(status.splitlines())
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    paths = changed_paths(status)
    listed = ", ".join(paths[:4]) + (" …" if len(paths) > 4 else "")
    run("git", "add", "-A")
    commit = run(
        "git",
        "-c", f"user.name={NAME}",
        "-c", f"user.email={EMAIL}",
        "commit", "-m", f"chore(autosync): {count} file(s) [{listed}] @ {stamp}",
    )
    if commit.returncode != 0:
        log("commit failed: " + (commit.stderr or commit.stdout).strip()[:300])
        return False

    br = branch()
    push = run("git", "push", "origin", br)
    if push.returncode != 0:
        log("push failed, attempting rebase pull…")
        run("git", "pull", "--rebase", "--autostash", "origin", br)
        push = run("git", "push", "origin", br)
    if push.returncode != 0:
        log("push failed: " + (push.stderr or push.stdout).strip()[:300])
        return False
    log(f"pushed {count} file(s) to {br}")
    return True


def handle_stop(signum, frame):
    global _running
    _running = False


def main():
    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)
    log(f"autosync started in {ROOT} (every {INTERVAL}s) on {branch()}")
    while _running:
        try:
            commit_push()
        except Exception as exc:  # keep the watcher alive
            log("error: " + str(exc))
        for _ in range(int(INTERVAL * 10)):
            if not _running:
                break
            time.sleep(0.1)
    log("autosync stopped")


if __name__ == "__main__":
    sys.exit(main())
