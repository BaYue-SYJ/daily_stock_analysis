from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.saas_models import Article
from app.services.fetcher import AiNewsFetcher
from app.services.summarizer import ArticleSummarizer
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.scheduler.run_daily_fetch_pipeline")
def run_daily_fetch_pipeline(tenant_id: int = 1) -> dict:
    """Daily scheduled pipeline: fetch first, then trigger summarization task."""
    fetch_result = AiNewsFetcher(tenant_id=tenant_id).fetch_once()
    summarize_task = summarize_new_articles.delay(tenant_id=tenant_id)
    return {
        "tenant_id": tenant_id,
        "fetch_result": fetch_result,
        "summarize_task_id": summarize_task.id,
    }


@celery_app.task(name="app.tasks.scheduler.summarize_new_articles")
def summarize_new_articles(tenant_id: int = 1, limit: int = 30) -> dict:
    """Summarize newly fetched articles (or those not processed by GPT yet)."""
    db: Session = SessionLocal()
    summarizer = ArticleSummarizer()
    updated = 0
    try:
        rows = (
            db.query(Article)
            .filter(
                Article.tenant_id == tenant_id,
                (Article.ai_model.is_(None)) | (~Article.ai_model.like("gpt:%")),
            )
            .order_by(Article.id.desc())
            .limit(limit)
            .all()
        )

        for row in rows:
            try:
                result = summarizer.summarize(article_title=row.title, article_link=row.original_url)
                row.content = result.summarized_body or row.content
                row.summary = result.abstract or row.summary
                row.ai_model = f"gpt:{summarizer.model}"
                updated += 1
            except Exception:
                logger.exception("summarize failed", extra={"article_id": row.id, "tenant_id": tenant_id})

        db.commit()
        return {"tenant_id": tenant_id, "updated": updated}
    finally:
        db.close()
