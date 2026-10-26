from fastapi import APIRouter, Query

from .. import config, db

router = APIRouter(prefix="/api", tags=["usage"])


@router.get("/health")
async def health():
    return {
        "ok": True,
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
        "upstream": config.UPSTREAM,
        "active_keys": len(db.active_keys()),
    }


@router.get("/stats")
async def stats(hours: int = Query(24, ge=1, le=168)):
    return db.stats(hours)


@router.get("/logs")
async def logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    model: str | None = None,
    status: str | None = None,
):
    return db.query_logs(limit=limit, offset=offset, model=model, status=status)


@router.get("/models")
async def models():
    return db.model_breakdown()


@router.get("/endpoints")
async def endpoints():
    return db.endpoint_breakdown()


@router.get("/key-usage")
async def key_usage():
    return db.key_breakdown()


@router.delete("/logs")
async def clear_logs():
    db.clear_usage()
    return {"ok": True}
