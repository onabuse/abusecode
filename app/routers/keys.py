from fastapi import APIRouter, HTTPException

from .. import db
from ..schemas import KeyIn, KeyPatch

router = APIRouter(prefix="/api/keys", tags=["keys"])


@router.get("")
async def list_keys():
    return db.list_keys()


@router.post("")
async def add_key(payload: KeyIn):
    api_key = payload.api_key.strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="api_key required")
    key_id = db.add_key(payload.name, api_key)
    return {"ok": True, "id": key_id}


@router.patch("/{key_id}")
async def patch_key(key_id: int, payload: KeyPatch):
    db.set_key_active(key_id, payload.active)
    return {"ok": True}


@router.delete("/{key_id}")
async def remove_key(key_id: int):
    db.delete_key(key_id)
    return {"ok": True}
