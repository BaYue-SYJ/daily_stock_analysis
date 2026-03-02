from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import UserClaims, db_session, get_current_user_claims
from app.models.entities import Article, User

router = APIRouter(prefix="/users", tags=["users"])


class UserProfileResponse(BaseModel):
    id: int
    tenant_id: int
    email: str
    role: str


class UserArticleItem(BaseModel):
    title: str
    summary: str
    full_body: str
    published_at: datetime | None


class UserArticleListResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[UserArticleItem]


@router.get("/me", response_model=UserProfileResponse)
def me(
    claims: UserClaims = Depends(get_current_user_claims),
    db: Session = Depends(db_session),
) -> UserProfileResponse:
    user = (
        db.query(User)
        .filter(User.id == claims.user_id, User.tenant_id == claims.tenant_id, User.is_active.is_(True))
        .first()
    )
    # get_current_user_claims already validated token; if user missing, return token principal view
    if not user:
        return UserProfileResponse(id=claims.user_id, tenant_id=claims.tenant_id, email=claims.email, role="unknown")
    return UserProfileResponse(id=user.id, tenant_id=user.tenant_id, email=user.email, role=user.role)


@router.get("/articles", response_model=UserArticleListResponse)
def my_org_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    claims: UserClaims = Depends(get_current_user_claims),
    db: Session = Depends(db_session),
) -> UserArticleListResponse:
    # Tenant isolation: users can only read data under their own tenant/org.
    q = db.query(Article).filter(Article.tenant_id == claims.tenant_id)
    total = q.count()
    rows = (
        q.order_by(Article.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return UserArticleListResponse(
        page=page,
        page_size=page_size,
        total=total,
        items=[
            UserArticleItem(
                title=r.title,
                summary=r.summary,
                full_body=r.content,
                published_at=r.published_at,
            )
            for r in rows
        ],
    )
