from celery import Celery
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)

celery_app = Celery(
    "molecule_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["src.molecules.tasks"],
)

celery_app.conf.update(
    task_track_started=True,
    broker_connection_retry_on_startup=True,
)

logger.info(f"Celery app configured with broker: {settings.CELERY_BROKER_URL}")
