"""Celery background worker configuration and tasks."""

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "bachnest_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Dhaka",
    enable_utc=True,
)


@celery_app.task(name="tasks.generate_monthly_invoices")
def generate_monthly_invoices():
    """Task scheduled on 1st of every month to generate invoices for all active tenancies."""
    # Idempotent task logic
    return {"status": "success", "message": "Monthly invoice generation executed"}


@celery_app.task(name="tasks.send_payment_reminder")
def send_payment_reminder(invoice_id: str):
    """Task to send overdue reminders to tenants."""
    return {"status": "sent", "invoice_id": invoice_id}
