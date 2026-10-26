import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .. import config, db
from ..services import upstream

router = APIRouter(tags=["proxy"])

_client = None


def set_client(client):
    global _client
    _client = client


@router.api_route(
    "/v1/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def proxy(path: str, request: Request):
    started = time.perf_counter()
    body = await request.body()
    req_model = upstream.request_model(body)
    stream = upstream.wants_stream(request, body)
    endpoint = path.split("/")[0] if path else "root"
    url = f"{config.UPSTREAM}/v1/{path}"

    keys = db.active_keys()
    if not keys:
        return JSONResponse(
            {
                "error": {
                    "type": "no_keys",
                    "message": "No active API keys. Add one in the dashboard.",
                }
            },
            status_code=503,
        )

    resp, used, failures = await upstream.send_with_failover(
        _client, request.method, url, request, body, keys
    )

    elapsed = int((time.perf_counter() - started) * 1000)
    for failure in failures:
        db.log_usage(
            key_id=failure["key"]["id"],
            key_name=failure["key"]["name"],
            model=req_model,
            endpoint=endpoint,
            method=request.method,
            status=0,
            latency_ms=elapsed,
            stream=stream,
            error=failure["error"],
        )

    if resp is None:
        return JSONResponse(
            {
                "error": {
                    "type": "upstream_error",
                    "message": failures[-1]["error"] if failures else "All keys failed",
                }
            },
            status_code=502,
        )

    if used:
        db.touch_key(used["id"])

    media_type = resp.headers.get("content-type", "application/json")

    async def relay():
        raw = bytearray()
        try:
            async for chunk in resp.aiter_bytes():
                if len(raw) < config.MAX_CAPTURE_BYTES:
                    raw.extend(chunk)
                yield chunk
        finally:
            try:
                await resp.aclose()
            except Exception:
                pass
            try:
                usage, resp_model = upstream.parse_usage(bytes(raw))
                error = None
                if resp.status_code >= 400:
                    error = bytes(raw[:800]).decode("utf-8", "replace")
                db.log_usage(
                    key_id=used["id"] if used else None,
                    key_name=used["name"] if used else None,
                    model=req_model or resp_model,
                    endpoint=endpoint,
                    method=request.method,
                    status=resp.status_code,
                    latency_ms=int((time.perf_counter() - started) * 1000),
                    input_tokens=(usage or {}).get("input", 0),
                    output_tokens=(usage or {}).get("output", 0),
                    total_tokens=(usage or {}).get("total", 0),
                    stream=stream,
                    error=error,
                )
            except Exception:
                pass

    return StreamingResponse(
        relay(),
        status_code=resp.status_code,
        headers=upstream.response_headers(resp),
        media_type=media_type,
    )
