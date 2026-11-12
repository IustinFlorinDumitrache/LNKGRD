from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import guard
from app.db import get_db
from app.models import ApiKey
from app.schemas import ApiKeyCreate, ApiKeyOut, BlockIpRequest, KillSwitchRequest
from app.security import generate_api_key, hash_key, require_admin

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.post("/keys", response_model=ApiKeyOut, status_code=status.HTTP_201_CREATED)
def create_api_key(payload: ApiKeyCreate, db: Session = Depends(get_db)):
    plain = generate_api_key()
    key = ApiKey(owner=payload.owner, key_hash=hash_key(plain), key_prefix=plain[:7])
    db.add(key)
    db.commit()
    return ApiKeyOut(id=key.id, owner=key.owner, key_prefix=key.key_prefix, api_key=plain)

@router.post("/blocklist")
def block_ip(payload: BlockIpRequest):
    ttl = guard.block_ip(payload.ip, payload.ttl_seconds, payload.reason)
    return {"blocked": payload.ip, "ttl_seconds": ttl}


@router.delete("/blocklist/{ip}")
def unblock_ip(ip: str):
    if not guard.unblock_ip(ip):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "IP not in blocklist")
    return {"unblocked": ip}


@router.get("/blocklist")
def list_blocked():
    return guard.list_blocked()


@router.post("/kill-switch")
def kill_switch(payload: KillSwitchRequest):
    guard.set_kill_switch(payload.enabled)
    return {"kill_switch": payload.enabled}


@router.get("/kill-switch")
def kill_switch_status():
    return {"kill_switch": guard.kill_switch_on()}