from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery("ai_news_saas", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery_app.conf.task_routes = {
    "app.tasks.pipeline.*": {"queue": "content_pipeline"},
    "app.tasks.scheduler.*": {"queue": "content_pipeline"},
}

# 每日 09:00 / 18:00 触发抓取任务（可在 scheduler task 中继续触发总结任务）
celery_app.conf.beat_schedule = {
    "daily-fetch-9am": {
        "task": "app.tasks.scheduler.run_daily_fetch_pipeline",
        "schedule": crontab(minute=0, hour=9),
        "args": (1,),
    },
    "daily-fetch-6pm": {
        "task": "app.tasks.scheduler.run_daily_fetch_pipeline",
        "schedule": crontab(minute=0, hour=18),
        "args": (1,),
    },
}
celery_app.conf.timezone = "Asia/Shanghai"

celery_app.autodiscover_tasks(["app.tasks"])
