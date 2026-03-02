from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db


def get_current_tenant_id(authorization: str = Header(default="")) -> int:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return int(payload["tenant_id"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")


def db_session(db: Session = Depends(get_db)) -> Session:
    return db
