from app import db


def test_keys_crud(tmp_db):
    key_id = db.add_key("primary", "oc_sk_1234567890abcdef")
    keys = db.list_keys()
    assert len(keys) == 1
    assert keys[0]["masked"] == "oc_sk_1234...cdef"
    assert keys[0]["active"] is True

    db.set_key_active(key_id, False)
    assert db.list_keys()[0]["active"] is False
    assert db.active_keys() == []

    db.delete_key(key_id)
    assert db.list_keys() == []


def test_key_cooldown_and_success(tmp_db):
    key_id = db.add_key("k", "oc_sk_abcdefghijklmnop")
    db.mark_key_failure(key_id, 429, "rate limited", 60)

    assert db.active_keys() == []
    assert len(db.active_keys(include_cooling=True)) == 1
    assert db.cooldown_remaining() > 0

    db.mark_key_success(key_id, 200)
    assert len(db.active_keys()) == 1
    key = db.list_keys()[0]
    assert key["success_count"] == 1
    assert key["fail_count"] == 0
    assert key["cooling"] is False


def test_usage_queries(tmp_db):
    db.add_key("k", "oc_sk_abcdefghijklmnop")
    db.log_usage(
        key_id=1,
        key_name="k",
        model="m",
        endpoint="responses",
        method="POST",
        status=200,
        latency_ms=42,
        input_tokens=1,
        output_tokens=2,
        total_tokens=3,
    )
    result = db.query_logs()
    assert result["total"] == 1
    assert result["items"][0]["total_tokens"] == 3

    stats = db.stats(24)
    assert stats["requests"] == 1
    assert stats["tokens"] == 3
    assert stats["success_rate"] == 100.0
    assert db.model_breakdown()[0]["model"] == "m"
    assert db.key_breakdown()[0]["name"] == "k"

    db.clear_usage()
    assert db.query_logs()["total"] == 0
