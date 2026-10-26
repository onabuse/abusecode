import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from . import config


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def conn():
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    c = sqlite3.connect(config.DB_PATH, timeout=30)
    c.row_factory = sqlite3.Row
    try:
        c.execute("PRAGMA journal_mode=WAL")
        yield c
        c.commit()
    finally:
        c.close()


def init_db():
    with conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS keys (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT NOT NULL,
                api_key      TEXT NOT NULL,
                active       INTEGER NOT NULL DEFAULT 1,
                created_at   TEXT NOT NULL,
                last_used_at TEXT
            );

            CREATE TABLE IF NOT EXISTS usage (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                ts            TEXT NOT NULL,
                key_id        INTEGER,
                key_name      TEXT,
                model         TEXT,
                endpoint      TEXT,
                method        TEXT,
                status        INTEGER,
                latency_ms    INTEGER,
                input_tokens  INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                total_tokens  INTEGER DEFAULT 0,
                stream        INTEGER DEFAULT 0,
                error         TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_usage_ts ON usage(ts);
            """
        )


def mask(api_key):
    if not api_key:
        return ""
    if len(api_key) <= 14:
        return api_key[:4] + "..." + api_key[-2:]
    return api_key[:10] + "..." + api_key[-4:]


# ---------------- keys ----------------

def add_key(name, api_key):
    with conn() as c:
        cur = c.execute(
            "INSERT INTO keys(name, api_key, active, created_at) VALUES(?,?,1,?)",
            (name.strip() or "key", api_key.strip(), now()),
        )
        return cur.lastrowid


def list_keys():
    with conn() as c:
        rows = c.execute("SELECT * FROM keys ORDER BY id DESC").fetchall()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "masked": mask(r["api_key"]),
            "active": bool(r["active"]),
            "created_at": r["created_at"],
            "last_used_at": r["last_used_at"],
        }
        for r in rows
    ]


def set_key_active(key_id, active):
    with conn() as c:
        c.execute("UPDATE keys SET active=? WHERE id=?", (1 if active else 0, key_id))


def delete_key(key_id):
    with conn() as c:
        c.execute("DELETE FROM keys WHERE id=?", (key_id,))


def active_keys():
    """Least-recently-used first, for simple rotation + failover."""
    with conn() as c:
        rows = c.execute(
            "SELECT id, name, api_key FROM keys "
            "WHERE active=1 ORDER BY COALESCE(last_used_at,'') ASC, id ASC"
        ).fetchall()
    return [dict(r) for r in rows]


def touch_key(key_id):
    with conn() as c:
        c.execute("UPDATE keys SET last_used_at=? WHERE id=?", (now(), key_id))


# ---------------- usage ----------------

def log_usage(
    key_id=None,
    key_name=None,
    model=None,
    endpoint=None,
    method=None,
    status=0,
    latency_ms=0,
    input_tokens=0,
    output_tokens=0,
    total_tokens=0,
    stream=False,
    error=None,
):
    with conn() as c:
        c.execute(
            "INSERT INTO usage(ts,key_id,key_name,model,endpoint,method,status,"
            "latency_ms,input_tokens,output_tokens,total_tokens,stream,error) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                now(),
                key_id,
                key_name,
                model,
                endpoint,
                method,
                status,
                int(latency_ms),
                int(input_tokens or 0),
                int(output_tokens or 0),
                int(total_tokens or 0),
                1 if stream else 0,
                error,
            ),
        )


def stats(hours=24):
    with conn() as c:
        totals = c.execute(
            "SELECT COUNT(*) n, COALESCE(SUM(total_tokens),0) tok, "
            "COALESCE(SUM(CASE WHEN status>=200 AND status<400 THEN 1 ELSE 0 END),0) ok, "
            "COALESCE(AVG(latency_ms),0) lat, "
            "COALESCE(SUM(CASE WHEN status>=400 OR status=0 THEN 1 ELSE 0 END),0) err "
            "FROM usage"
        ).fetchone()
        active = c.execute("SELECT COUNT(*) n FROM keys WHERE active=1").fetchone()["n"]
        by_model = c.execute(
            "SELECT COALESCE(model,'unknown') model, COUNT(*) n, "
            "COALESCE(SUM(total_tokens),0) tok FROM usage "
            "GROUP BY model ORDER BY n DESC LIMIT 8"
        ).fetchall()
        by_endpoint = c.execute(
            "SELECT COALESCE(endpoint,'?') endpoint, COUNT(*) n, "
            "COALESCE(SUM(total_tokens),0) tok FROM usage "
            "GROUP BY endpoint ORDER BY n DESC LIMIT 8"
        ).fetchall()
        by_key = c.execute(
            "SELECT COALESCE(key_name,'—') name, COUNT(*) n, "
            "COALESCE(SUM(total_tokens),0) tok FROM usage "
            "GROUP BY key_name ORDER BY n DESC LIMIT 8"
        ).fetchall()
        recent = c.execute("SELECT * FROM usage ORDER BY id DESC LIMIT 40").fetchall()

        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours - 1)).replace(
            minute=0, second=0, microsecond=0
        )
        rows = c.execute(
            "SELECT ts, status FROM usage WHERE ts >= ?", (cutoff.isoformat(),)
        ).fetchall()

    buckets = {}
    for r in rows:
        buckets.setdefault(r["ts"][:13], [0, 0])[0] += 1
        if r["status"] >= 400 or r["status"] == 0:
            buckets[r["ts"][:13]][1] += 1

    series = []
    for i in range(hours):
        start = cutoff + timedelta(hours=i)
        key = start.strftime("%Y-%m-%dT%H")
        n, e = buckets.get(key, (0, 0))
        series.append({"t": key + ":00:00+00:00", "count": n, "errors": e})

    n = totals["n"] or 0
    return {
        "requests": n,
        "tokens": totals["tok"],
        "success": totals["ok"],
        "errors": totals["err"],
        "success_rate": (totals["ok"] / n * 100) if n else 100.0,
        "avg_latency": round(totals["lat"] or 0),
        "active_keys": active,
        "by_model": [dict(r) for r in by_model],
        "by_endpoint": [dict(r) for r in by_endpoint],
        "by_key": [dict(r) for r in by_key],
        "recent": [dict(r) for r in recent],
        "series": series,
    }


def query_logs(limit=50, offset=0, model=None, status=None):
    where, params = [], []
    if model:
        where.append("model = ?")
        params.append(model)
    if status == "ok":
        where.append("status >= 200 AND status < 400")
    elif status == "error":
        where.append("(status >= 400 OR status = 0)")
    elif status and str(status).isdigit():
        where.append("status = ?")
        params.append(int(status))
    clause = ("WHERE " + " AND ".join(where)) if where else ""
    with conn() as c:
        total = c.execute(f"SELECT COUNT(*) n FROM usage {clause}", params).fetchone()["n"]
        rows = c.execute(
            f"SELECT * FROM usage {clause} ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [int(limit), int(offset)],
        ).fetchall()
    return {"items": [dict(r) for r in rows], "total": total}


def model_breakdown():
    with conn() as c:
        rows = c.execute(
            "SELECT COALESCE(model,'unknown') model, COUNT(*) n, "
            "COALESCE(SUM(input_tokens),0) inp, COALESCE(SUM(output_tokens),0) outp, "
            "COALESCE(SUM(total_tokens),0) tok, COALESCE(AVG(latency_ms),0) lat, "
            "COALESCE(SUM(CASE WHEN status>=400 OR status=0 THEN 1 ELSE 0 END),0) err "
            "FROM usage GROUP BY model ORDER BY n DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def endpoint_breakdown():
    with conn() as c:
        rows = c.execute(
            "SELECT COALESCE(endpoint,'?') endpoint, COUNT(*) n, "
            "COALESCE(SUM(total_tokens),0) tok FROM usage "
            "GROUP BY endpoint ORDER BY n DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def key_breakdown():
    with conn() as c:
        rows = c.execute(
            "SELECT COALESCE(key_name,'—') name, COUNT(*) n, "
            "COALESCE(SUM(total_tokens),0) tok, "
            "COALESCE(SUM(CASE WHEN status>=400 OR status=0 THEN 1 ELSE 0 END),0) err "
            "FROM usage GROUP BY key_name ORDER BY n DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def clear_usage():
    with conn() as c:
        c.execute("DELETE FROM usage")
