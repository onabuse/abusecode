import json

from app.services import upstream


def test_parse_plain_json_usage():
    body = json.dumps(
        {"model": "m", "usage": {"input_tokens": 3, "output_tokens": 5, "total_tokens": 8}}
    ).encode()
    usage, model = upstream.parse_usage(body)
    assert usage == {"input": 3, "output": 5, "total": 8}
    assert model == "m"


def test_parse_sse_usage():
    body = (
        b'data: {"type":"response.output_text.delta","delta":"hi"}\n\n'
        b'data: {"type":"response.completed","response":{"model":"m2",'
        b'"usage":{"input_tokens":10,"output_tokens":4,"total_tokens":14}}}\n\n'
        b"data: [DONE]\n\n"
    )
    usage, model = upstream.parse_usage(body)
    assert usage == {"input": 10, "output": 4, "total": 14}
    assert model == "m2"


def test_parse_chat_usage_fallback():
    usage, _ = upstream.parse_usage(
        json.dumps({"usage": {"prompt_tokens": 2, "completion_tokens": 3}}).encode()
    )
    assert usage == {"input": 2, "output": 3, "total": 5}


def test_cooldown_mapping():
    assert upstream.cooldown_for(429) == 60
    assert upstream.cooldown_for(401) == 300
    assert upstream.cooldown_for(503) == 30
    assert upstream.cooldown_for(429, "120") == 120
    assert upstream.cooldown_for(0) == 15


def test_request_model():
    assert upstream.request_model(b'{"model":"x"}') == "x"
    assert upstream.request_model(b"not json") is None


class _FakeRequest:
    def __init__(self, headers):
        from starlette.datastructures import Headers

        self.headers = Headers(headers)


def test_build_headers_strips_local_secrets():
    headers = upstream.build_headers(
        _FakeRequest(
            {
                "cookie": "session=secret",
                "origin": "http://localhost:8000",
                "referer": "http://localhost:8000/keys",
                "sec-fetch-site": "same-origin",
                "x-forwarded-for": "1.2.3.4",
                "x-proxy-token": "ptok",
                "x-custom": "keep",
                "accept": "application/json",
            }
        ),
        "oc_sk_test",
    )
    lowered = {k.lower() for k in headers}
    for blocked in ("cookie", "origin", "referer", "sec-fetch-site", "x-forwarded-for", "x-proxy-token"):
        assert blocked not in lowered
    assert headers["Authorization"] == "Bearer oc_sk_test"
    assert headers["x-custom"] == "keep"
