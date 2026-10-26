import csv
import io
import json
import time
from datetime import UTC, datetime

from fastapi import APIRouter, Query
from fastapi.responses import Response

from .. import config, db
from ..services import client as client_service
from ..services import upstream

router = APIRouter(prefix="/api", tags=["usage"])

CATALOG_TTL = 60
_catalog = {"ts": 0.0, "data": None, "error": None, "fetched_at": None}


@router.get("/health")
async def health():
    return {
        "ok": True,
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
        "upstream": config.UPSTREAM,
        "active_keys": len(db.active_keys()),
        "total_keys": len(db.list_keys()),
        "proxy_token": bool(config.PROXY_TOKEN),
    }


@router.get("/stats")
async def stats(hours: int = Query(24, ge=1, le=720)):
    return db.stats(hours)


@router.get("/logs")
async def logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    model: str | None = None,
    status: str | None = None,
):
    return db.query_logs(limit=limit, offset=offset, model=model, status=status)


@router.get("/logs/export")
async def export_logs(
    format: str = Query("csv", pattern="^(csv|json)$"),
    model: str | None = None,
    status: str | None = None,
):
    items = db.query_logs(limit=1_000_000, offset=0, model=model, status=status)["items"]
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    if format == "json":
        return Response(
            json.dumps(items, ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="abusecode-logs-{stamp}.json"'
            },
        )
    fields = [
        "id", "ts", "key_name", "model", "endpoint", "method", "status",
        "latency_ms", "input_tokens", "output_tokens", "total_tokens", "stream", "error",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(items)
    return Response(
        buf.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="abusecode-logs-{stamp}.csv"'
        },
    )


@router.get("/models")
async def models():
    return db.model_breakdown()


@router.get("/endpoints")
async def endpoints():
    return db.endpoint_breakdown()


@router.get("/key-usage")
async def key_usage():
    return db.key_breakdown()


@router.get("/catalog")
async def catalog(refresh: bool = False):
    now = time.time()
    if (
        not refresh
        and _catalog["data"] is not None
        and now - _catalog["ts"] < CATALOG_TTL
    ):
        return {
            "data": _catalog["data"],
            "cached": True,
            "error": _catalog["error"],
            "fetched_at": _catalog["fetched_at"],
        }

    keys = db.active_keys(include_cooling=True)
    client = client_service.get_client()
    data, error = None, None
    if not keys:
        error = "No API keys configured."
    elif client is None:
        error = "HTTP client not ready."
    else:
        for key in keys:
            try:
                resp = await client.get(
                    f"{config.UPSTREAM}/v1/models",
                    headers=upstream.auth_headers(key["api_key"]),
                    timeout=20,
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    error = None
                    break
                error = f"HTTP {resp.status_code}: {resp.text[:200]}"
            except Exception as exc:
                error = str(exc)

    _catalog.update(
        {
            "ts": now,
            "data": data,
            "error": error,
            "fetched_at": datetime.now(UTC).isoformat(),
        }
    )
    return {
        "data": data or [],
        "cached": False,
        "error": error,
        "fetched_at": _catalog["fetched_at"],
    }


@router.delete("/logs")
async def clear_logs():
    db.clear_usage()
    return {"ok": True}
