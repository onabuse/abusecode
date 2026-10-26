from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from .. import config
from ..schemas import LoginIn
from ..security import auth_enabled, check_admin_token

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)


@router.get("/login")
async def login_page(request: Request):
    if not auth_enabled() or request.session.get("auth") is True:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "app_name": config.APP_NAME,
            "version": config.APP_VERSION,
            "upstream": config.UPSTREAM,
        },
    )


@router.post("/api/login")
async def login(request: Request, payload: LoginIn):
    if not check_admin_token(payload.token):
        raise HTTPException(status_code=401, detail="Invalid token")
    request.session["auth"] = True
    return {"ok": True}


@router.post("/api/logout")
async def logout(request: Request):
    request.session.clear()
    return {"ok": True}
