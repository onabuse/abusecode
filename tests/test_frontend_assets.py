import re
from pathlib import Path

from app.routers.pages import NAV

ROOT = Path(__file__).resolve().parents[1]
SW = ROOT / "static" / "sw.js"


def shell_urls():
    text = SW.read_text(encoding="utf-8")
    match = re.search(r"const SHELL = \[(.*?)\];", text, re.S)
    assert match, "SHELL array not found in sw.js"
    return re.findall(r'"([^"]+)"', match.group(1))


def test_service_worker_offline_strategy():
    text = SW.read_text(encoding="utf-8")
    assert 'const CACHE = "abusecode-v3"' in text
    assert "OFFLINE" in text
    assert 'caches.match("/")' not in text
    assert "caches.match(req, { ignoreSearch: true })" in text
    assert "caches.match(req);" in text
    assert "!res.redirected" in text


def test_service_worker_shell_files_exist():
    urls = shell_urls()
    assert urls
    for url in urls:
        assert url.startswith("/")
        if url.startswith("/static/"):
            assert (ROOT / url.lstrip("/")).is_file(), f"missing shell asset: {url}"


def test_service_worker_covers_every_route():
    assert {item["href"] for item in NAV} <= set(shell_urls())


def test_mobile_shell_is_overflow_safe():
    base = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
    assert "min-h-svh" in base
    assert "overflow-x-hidden" in base
    for template in (ROOT / "templates").rglob("*.html"):
        assert "backdrop-blur" not in template.read_text(encoding="utf-8"), template
