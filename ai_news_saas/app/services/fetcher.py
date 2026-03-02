from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import logging
from typing import Iterable

import feedparser
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.saas_models import Article

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RssSource:
    name: str
    url: str


DEFAULT_AI_RSS_SOURCES: tuple[RssSource, ...] = (
    RssSource("OpenAI Blog", "https://openai.com/news/rss.xml"),
    RssSource("DeepMind Blog", "https://deepmind.google/blog/rss.xml"),
    RssSource("arXiv AI", "https://rss.arxiv.org/rss/cs.AI"),
)


class AiNewsFetcher:
    """Fetches AI RSS feeds, filters duplicates, and persists to articles table."""

    def __init__(self, tenant_id: int, sources: Iterable[RssSource] | None = None):
        self.tenant_id = tenant_id
        self.sources = tuple(sources or DEFAULT_AI_RSS_SOURCES)

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join((text or "").strip().split())

    @classmethod
    def _content_fingerprint(cls, title: str, summary: str, link: str) -> str:
        normalized = f"{cls._normalize_text(title)}|{cls._normalize_text(summary)}|{link.strip()}"
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def _extract_content(entry: feedparser.FeedParserDict) -> str:
        if entry.get("content"):
            chunks = [c.get("value", "") for c in entry.get("content", [])]
            return "\n".join([c for c in chunks if c])
        return entry.get("summary", "")

    @staticmethod
    def _extract_published_at(entry: feedparser.FeedParserDict) -> datetime | None:
        # feedparser returns struct_time fields like published_parsed/updated_parsed
        for field in ("published_parsed", "updated_parsed"):
            parsed = entry.get(field)
            if parsed:
                return datetime(*parsed[:6], tzinfo=timezone.utc).replace(tzinfo=None)
        return None

    def _exists(self, db: Session, original_url: str, fingerprint: str) -> bool:
        # Duplicate rule:
        # 1) same tenant + same original_url
        # 2) same tenant + same source_url set + same normalized title/summary fingerprint
        if db.query(Article.id).filter(Article.tenant_id == self.tenant_id, Article.original_url == original_url).first():
            return True

        return (
            db.query(Article.id)
            .filter(
                Article.tenant_id == self.tenant_id,
                Article.ai_model == f"fingerprint:{fingerprint}",
            )
            .first()
            is not None
        )

    def fetch_once(self) -> dict:
        db = SessionLocal()
        created = 0
        skipped = 0
        errors = 0
        try:
            for source in self.sources:
                parsed = feedparser.parse(source.url)
                if getattr(parsed, "bozo", False):
                    logger.warning("Invalid RSS feed", extra={"source": source.name, "url": source.url})

                for entry in parsed.entries:
                    title = entry.get("title", "(untitled)")
                    original_url = entry.get("link", "").strip()
                    if not original_url:
                        skipped += 1
                        continue

                    content = self._extract_content(entry)
                    summary = entry.get("summary", "")
                    fingerprint = self._content_fingerprint(title=title, summary=summary, link=original_url)

                    if self._exists(db, original_url=original_url, fingerprint=fingerprint):
                        skipped += 1
                        continue

                    article = Article(
                        tenant_id=self.tenant_id,
                        wechat_account_id=None,
                        source_name=source.name,
                        source_url=source.url,
                        title=title,
                        original_url=original_url,
                        content=content or summary,
                        summary=summary,
                        ai_model=f"fingerprint:{fingerprint}",
                        published_to_wechat=0,
                        published_at=self._extract_published_at(entry),
                    )
                    db.add(article)
                    created += 1

            db.commit()
        except Exception:
            db.rollback()
            errors += 1
            logger.exception("Fetch failed for tenant_id=%s", self.tenant_id)
            raise
        finally:
            db.close()

        return {"created": created, "skipped": skipped, "errors": errors}


def start_fetch_scheduler(tenant_id: int, fetch_interval_minutes: int = 30) -> BackgroundScheduler:
    """Start APScheduler background job.

    - fetch_interval_minutes is configurable.
    - Calls AiNewsFetcher.fetch_once periodically.
    """
    scheduler = BackgroundScheduler(timezone="UTC")
    fetcher = AiNewsFetcher(tenant_id=tenant_id)

    scheduler.add_job(
        fetcher.fetch_once,
        trigger="interval",
        minutes=fetch_interval_minutes,
        id=f"ai_rss_fetch_{tenant_id}",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info("Started fetch scheduler for tenant_id=%s every %s minutes", tenant_id, fetch_interval_minutes)
    return scheduler
