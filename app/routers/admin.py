from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ApiKey
from app.schemas import ApiKeyCreate, ApiKeyOut
from app.security import generate_api_key, hash_key, require_admin

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.post("/keys", response_model=ApiKeyOut, status_code=status.HTTP_201_CREATED)
def create_api_key(payload: ApiKeyCreate, db: Session = Depends(get_db)):
    plain = generate_api_key()
    key = ApiKey(owner=payload.owner, key_hash=hash_key(plain), key_prefix=plain[:7])
    db.add(key)
    db.commit()
    return ApiKeyOut(id=key.id, owner=key.owner, key_prefix=key.key_prefix, api_key=plain)