from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from .. import config
from ..security import auth_enabled

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)

NAV = [
    {"id": "overview", "label": "Overview", "href": "/", "icon": "grid"},
    {"id": "playground", "label": "Playground", "href": "/playground", "icon": "bolt"},
    {"id": "keys", "label": "API Keys", "href": "/keys", "icon": "key"},
    {"id": "models", "label": "Models", "href": "/models", "icon": "layers"},
    {"id": "logs", "label": "Logs", "href": "/logs", "icon": "list"},
    {"id": "settings", "label": "Settings", "href": "/settings", "icon": "cog"},
]

PAGES = {
    "overview": {
        "title": "Overview",
        "subtitle": "Traffic, tokens and key health at a glance.",
    },
    "keys": {
        "title": "API Keys",
        "subtitle": "Add keys, control rotation and monitor usage per key.",
    },
    "playground": {
        "title": "Playground",
        "subtitle": "Send a live request through the proxy.",
    },
    "models": {
        "title": "Models",
        "subtitle": "Catalog and usage by model.",
    },
    "logs": {
        "title": "Request Logs",
        "subtitle": "Every proxied call, with tokens and latency.",
    },
    "settings": {
        "title": "Settings",
        "subtitle": "Proxy configuration and maintenance.",
    },
}


def render(request: Request, page_id: str, template: str):
    return templates.TemplateResponse(
        request=request,
        name=template,
        context={
            "app_name": config.APP_NAME,
            "version": config.APP_VERSION,
            "upstream": config.UPSTREAM,
            "nav": NAV,
            "active": page_id,
            "page": PAGES[page_id],
            "auth_enabled": auth_enabled(),
        },
    )


@router.get("/")
async def overview(request: Request):
    return render(request, "overview", "pages/overview.html")


@router.get("/playground")
async def playground_page(request: Request):
    return render(request, "playground", "pages/playground.html")


@router.get("/keys")
async def keys_page(request: Request):
    return render(request, "keys", "pages/keys.html")


@router.get("/models")
async def models_page(request: Request):
    return render(request, "models", "pages/models.html")


@router.get("/logs")
async def logs_page(request: Request):
    return render(request, "logs", "pages/logs.html")


@router.get("/settings")
async def settings_page(request: Request):
    return render(request, "settings", "pages/settings.html")
