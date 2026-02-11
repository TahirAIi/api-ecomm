from celery import Celery
from app.core.config import settings

celery = Celery(
    "app", broker=settings.CELERY_BROKER_URL, include=["app.tasks.embedding_tasks"]
)
