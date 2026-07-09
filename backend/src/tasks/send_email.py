import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def send_confirmation_email(to_email: str, token: str) -> None:
    confirmation_url = f":url/auth/register_confirm?token={token}"
    logger.info(f"SEND Message to {to_email}: {confirmation_url}")
