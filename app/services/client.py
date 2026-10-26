"""Shared outbound HTTP client (set during app lifespan)."""
import httpx

_client: httpx.AsyncClient | None = None


def set_client(client: httpx.AsyncClient):
    global _client
    _client = client


def get_client() -> httpx.AsyncClient | None:
    return _client
