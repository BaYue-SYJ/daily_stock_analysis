from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.entities import Article, RssSource
from app.services.ai_service import summarize_article
from app.services.rss_service import crawl_rss
from app.tasks.celery_app import celery_app


@celery_app.task
def run_fetch_and_summarize(tenant_id: int, source_id: int) -> dict:
    db: Session = SessionLocal()
    try:
        source = (
            db.query(RssSource)
            .filter(RssSource.id == source_id, RssSource.tenant_id == tenant_id, RssSource.is_enabled.is_(True))
            .first()
        )
        if not source:
            return {"status": "source_not_found"}

        created = 0
        for item in crawl_rss(source.url):
            exists = db.query(Article).filter(Article.link == item["link"]).first()
            if exists:
                continue
            summary = summarize_article(item["content"])
            article = Article(
                tenant_id=tenant_id,
                source_id=source.id,
                title=item["title"],
                link=item["link"],
                content=item["content"],
                summary=summary,
            )
            db.add(article)
            created += 1
        db.commit()
        return {"status": "ok", "created": created}
    finally:
        db.close()
