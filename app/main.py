from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from . import config, db
from .routers import auth, keys, pages, proxy, usage
from .security import SESSION_SECRET, AuthMiddleware
from .services import client as client_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    client = httpx.AsyncClient(
        timeout=httpx.Timeout(connect=30.0, read=None, write=60.0, pool=30.0),
        follow_redirects=False,
    )
    client_service.set_client(client)
    try:
        yield
    finally:
        await client.aclose()


app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# Added before SessionMiddleware so the session is available inside AuthMiddleware.
app.add_middleware(AuthMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    max_age=config.SESSION_MAX_AGE,
    same_site="lax",
    https_only=False,
)

app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")

app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(keys.router)
app.include_router(usage.router)
app.include_router(proxy.router)
