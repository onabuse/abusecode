from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import config, db
from .routers import keys, pages, proxy, usage


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    client = httpx.AsyncClient(
        timeout=httpx.Timeout(connect=30.0, read=None, write=60.0, pool=30.0),
        follow_redirects=False,
    )
    proxy.set_client(client)
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

app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")

app.include_router(pages.router)
app.include_router(keys.router)
app.include_router(usage.router)
app.include_router(proxy.router)
