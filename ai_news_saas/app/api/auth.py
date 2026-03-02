from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.core.security import create_access_token, hash_password, verify_password
from app.models.entities import Tenant, User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(db_session)) -> TokenResponse:
    tenant = db.query(Tenant).filter(Tenant.name == payload.tenant_name).first()
    if not tenant:
        tenant = Tenant(name=payload.tenant_name)
        db.add(tenant)
        db.flush()

    exists = db.query(User).filter(User.tenant_id == tenant.id, User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already exists in tenant")

    user = User(
        tenant_id=tenant.id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="owner",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(subject=user.email, tenant_id=tenant.id, user_id=user.id)
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(db_session)) -> TokenResponse:
    tenant = db.query(Tenant).filter(Tenant.name == payload.tenant_name).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tenant not found")

    user = (
        db.query(User)
        .filter(User.tenant_id == tenant.id, User.email == payload.email, User.is_active.is_(True))
        .first()
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")

    return TokenResponse(
        access_token=create_access_token(subject=user.email, tenant_id=tenant.id, user_id=user.id)
    )
