"""Upstream helpers: request inspection, header injection, usage parsing, failover."""
from __future__ import annotations

import json
import uuid

import httpx

from .. import config

# ---------------- usage parsing ----------------

def usage_from_obj(obj):
    if not isinstance(obj, dict):
        return None, None
    model = obj.get("model")
    candidates = [obj]
    for nested in ("response", "data", "message"):
        if isinstance(obj.get(nested), dict):
            candidates.append(obj[nested])
    for c in candidates:
        u = c.get("usage")
        if isinstance(u, dict):
            inp = u.get("input_tokens", u.get("prompt_tokens"))
            out = u.get("output_tokens", u.get("completion_tokens"))
            tot = u.get("total_tokens")
            if tot is None and (inp is not None or out is not None):
                tot = (inp or 0) + (out or 0)
            if inp is not None or out is not None or tot is not None:
                return (
                    {"input": int(inp or 0), "output": int(out or 0), "total": int(tot or 0)},
                    c.get("model") or model,
                )
    return None, model


def parse_usage(raw: bytes):
    """Parse usage from plain JSON or an SSE stream (Responses / Chat APIs)."""
    text = raw.decode("utf-8", "replace").strip()
    if not text:
        return None, None
    try:
        return usage_from_obj(json.loads(text))
    except Exception:
        pass
    usage, model = None, None
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if not data or data == "[DONE]":
            continue
        try:
            obj = json.loads(data)
        except Exception:
            continue
        u, m = usage_from_obj(obj)
        if u:
            usage = u
        if m:
            model = m
    return usage, model


# ---------------- request inspection ----------------

def request_model(body: bytes):
    if not body:
        return None
    try:
        obj = json.loads(body)
        if isinstance(obj, dict):
            return obj.get("model")
    except Exception:
        return None
    return None


def wants_stream(request, body: bytes):
    if "text/event-stream" in (request.headers.get("accept") or ""):
        return True
    try:
        obj = json.loads(body) if body else {}
        return bool(obj.get("stream"))
    except Exception:
        return False


def build_headers(request, api_key: str):
    headers = {}
    for k, v in request.headers.items():
        if k.lower() in (
            "host", "content-length", "authorization", "connection",
            "accept-encoding", "transfer-encoding",
        ):
            continue
        headers[k] = v
    headers["Authorization"] = f"Bearer {api_key}"
    headers.setdefault("Content-Type", "application/json")

    session = (
        request.headers.get("x-opencode-session")
        or config.DEFAULT_SESSION
        or "ses_" + uuid.uuid4().hex
    )
    headers["x-opencode-session"] = session
    headers["x-opencode-session-id"] = request.headers.get("x-opencode-session-id") or session
    headers["x-opencode-client"] = request.headers.get("x-opencode-client") or "cli"
    headers["x-opencode-project"] = request.headers.get("x-opencode-project") or "global"
    headers["x-opencode-request"] = (
        request.headers.get("x-opencode-request") or "msg_" + uuid.uuid4().hex[:16]
    )
    headers["User-Agent"] = config.USER_AGENT
    headers.setdefault("Accept", "text/event-stream")
    return headers


PASSTHROUGH_RESPONSE_HEADERS = (
    "x-request-id",
    "cache-control",
    "x-ratelimit-limit",
    "x-ratelimit-remaining",
    "x-ratelimit-reset",
    "retry-after",
)


def response_headers(resp: httpx.Response):
    return {h: resp.headers[h] for h in PASSTHROUGH_RESPONSE_HEADERS if h in resp.headers}


def auth_headers(api_key, session=None):
    """Headers for simple upstream calls that have no incoming Request."""
    session = session or config.DEFAULT_SESSION or "ses_" + uuid.uuid4().hex
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "x-opencode-client": "cli",
        "x-opencode-project": "global",
        "x-opencode-request": "msg_" + uuid.uuid4().hex[:16],
        "x-opencode-session": session,
        "x-opencode-session-id": session,
        "User-Agent": config.USER_AGENT,
    }


def cooldown_for(status, retry_after=None):
    """Cooldown seconds for a failed key, honoring upstream Retry-After."""
    if retry_after:
        try:
            return max(1, min(int(float(retry_after)), 3600))
        except Exception:
            pass
    if status == 429:
        return 60
    if status in (401, 403):
        return 300
    if status >= 500:
        return 30
    return 15


# ---------------- failover ----------------

async def send_with_failover(client, method, url, request, body, keys):
    """Try each key (LRU order) until a non-failover response is returned.

    Returns (response|None, used_key|None, failures). Each failure is
    {"key", "status", "error", "retry_after"}.
    """
    failures = []
    for i, key in enumerate(keys):
        try:
            req = client.build_request(
                method, url, headers=build_headers(request, key["api_key"]), content=body
            )
            resp = await client.send(req, stream=True)
        except httpx.RequestError as exc:
            failures.append(
                {"key": key, "status": 0, "error": str(exc), "retry_after": None}
            )
            continue

        if resp.status_code in config.FAILOVER_STATUS and i < len(keys) - 1:
            failures.append(
                {
                    "key": key,
                    "status": resp.status_code,
                    "error": f"HTTP {resp.status_code}",
                    "retry_after": resp.headers.get("retry-after"),
                }
            )
            await resp.aclose()
            continue

        return resp, key, failures

    return None, None, failures
