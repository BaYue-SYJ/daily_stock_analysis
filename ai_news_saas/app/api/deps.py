from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db


@dataclass
class UserClaims:
    user_id: int
    tenant_id: int
    email: str


def get_current_user_claims(authorization: str = Header(default="")) -> UserClaims:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return UserClaims(
            user_id=int(payload["user_id"]),
            tenant_id=int(payload["tenant_id"]),
            email=str(payload.get("sub", "")),
        )
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")


def get_current_tenant_id(claims: UserClaims = Depends(get_current_user_claims)) -> int:
    return claims.tenant_id


def db_session(db: Session = Depends(get_db)) -> Session:
    return db
