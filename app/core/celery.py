"""
Celery configuration for SRM Guide Bot
"""

import logging
from celery import Celery
from app.core.config import settings

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "srm_guide_bot",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
)


def init_celery():
    """Initialize Celery"""
    try:
        logger.info("Celery initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing Celery: {str(e)}")


@celery_app.task(bind=True)
def example_task(self, x, y):
    """Example background task"""
    try:
        result = x + y
        logger.info(f"Task {self.request.id} completed: {x} + {y} = {result}")
        return result
    except Exception as e:
        logger.error(f"Task {self.request.id} failed: {str(e)}")
        raise


@celery_app.task(bind=True)
def scrape_srm_website_task(self):
    """Background task to scrape SRM website"""
    try:
        from app.services.scraping_service import scraping_service
        import asyncio
        
        # Run scraping in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(scraping_service.scrape_srm_main_website())
        loop.close()
        
        logger.info(f"Scraping task {self.request.id} completed successfully")
        return {"status": "success", "data_count": len(result)}
        
    except Exception as e:
        logger.error(f"Scraping task {self.request.id} failed: {str(e)}")
        raise


@celery_app.task(bind=True)
def send_email_task(self, to_email: str, subject: str, content: str):
    """Background task to send email"""
    try:
        # Implement email sending logic here
        logger.info(f"Email task {self.request.id}: Sending email to {to_email}")
        
        # Placeholder for email sending
        # await email_service.send_email(to_email, subject, content)
        
        return {"status": "success", "email": to_email}
        
    except Exception as e:
        logger.error(f"Email task {self.request.id} failed: {str(e)}")
        raise


@celery_app.task(bind=True)
def cleanup_old_data_task(self):
    """Background task to cleanup old data"""
    try:
        from app.core.database import get_db
        from app.models.database import Session as UserSession
        from datetime import datetime, timedelta
        
        # Clean up old sessions
        db = next(get_db())
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        old_sessions = db.query(UserSession).filter(
            UserSession.created_at < cutoff_date
        ).delete()
        
        db.commit()
        db.close()
        
        logger.info(f"Cleanup task {self.request.id}: Removed {old_sessions} old sessions")
        return {"status": "success", "sessions_removed": old_sessions}
        
    except Exception as e:
        logger.error(f"Cleanup task {self.request.id} failed: {str(e)}")
        raise
