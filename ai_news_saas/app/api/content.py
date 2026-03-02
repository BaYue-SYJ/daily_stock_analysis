from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_tenant_id
from app.models.entities import Article, RssSource
from app.schemas.content import ArticleResponse, RssSourceCreate
from app.tasks.pipeline import run_fetch_and_summarize

router = APIRouter(prefix="/content", tags=["content"])


@router.post("/rss")
def add_rss_source(
    payload: RssSourceCreate,
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(db_session),
):
    source = RssSource(tenant_id=tenant_id, **payload.model_dump())
    db.add(source)
    db.commit()
    return {"id": source.id}


@router.post("/sync")
def trigger_sync(
    source_id: int,
    tenant_id: int = Depends(get_current_tenant_id),
):
    task = run_fetch_and_summarize.delay(tenant_id=tenant_id, source_id=source_id)
    return {"task_id": task.id, "status": "queued"}


@router.get("/mini/articles", response_model=list[ArticleResponse], tags=["mini-program"])
def list_articles_for_miniprogram(
    limit: int = 20,
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(db_session),
):
    items = (
        db.query(Article)
        .filter(Article.tenant_id == tenant_id)
        .order_by(Article.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        ArticleResponse(
            id=i.id,
            title=i.title,
            link=i.link,
            summary=i.summary,
            published_at=i.published_at,
        )
        for i in items
    ]
