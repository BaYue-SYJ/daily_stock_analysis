from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_tenant_id
from app.core.security import create_access_token, verify_password
from app.models.saas_models import Article, User

router = APIRouter(prefix="/mini", tags=["mini-api"])


class MiniLoginRequest(BaseModel):
    tenant_id: int
    email: EmailStr
    password: str


class MiniLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MiniArticleItem(BaseModel):
    title: str
    summary: str | None
    full_body: str
    published_at: datetime | None


class MiniArticleListResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[MiniArticleItem]


@router.post("/login", response_model=MiniLoginResponse)
def mini_login(payload: MiniLoginRequest, db: Session = Depends(db_session)) -> MiniLoginResponse:
    user = (
        db.query(User)
        .filter(User.tenant_id == payload.tenant_id, User.email == payload.email, User.status == "active")
        .first()
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")

    token = create_access_token(subject=user.email, tenant_id=user.tenant_id)
    return MiniLoginResponse(access_token=token)


@router.get("/articles", response_model=MiniArticleListResponse)
def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(db_session),
) -> MiniArticleListResponse:
    base_q = db.query(Article).filter(Article.tenant_id == tenant_id)
    total = base_q.count()
    offset = (page - 1) * page_size

    records = (
        base_q.order_by(Article.published_at.desc().nullslast(), Article.id.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    items = [
        MiniArticleItem(
            title=row.title,
            summary=row.summary,
            full_body=row.content,
            published_at=row.published_at,
        )
        for row in records
    ]

    return MiniArticleListResponse(page=page, page_size=page_size, total=total, items=items)
