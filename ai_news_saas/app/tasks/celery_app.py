from celery import Celery

from app.core.config import settings

celery_app = Celery("ai_news_saas", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery_app.conf.task_routes = {"app.tasks.pipeline.*": {"queue": "content_pipeline"}}
