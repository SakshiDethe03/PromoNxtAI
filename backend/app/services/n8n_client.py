import logging
import os
import requests

from app.config.settings import settings
from app.schemas.campaign import PublishPayload

logger = logging.getLogger(__name__)


def trigger_publish(payload: PublishPayload) -> None:
    """
    Triggers publishing of a campaign via the n8n webhook.
    Sends POST request to n8n webhook URL with X-Webhook-Secret header.
    Logs payload if N8N_MOCK flag or settings.n8n_mock is set.
    """
    env_mock = os.getenv("N8N_MOCK", "").lower() in ("true", "1", "yes")
    is_mock = settings.n8n_mock or env_mock

    if is_mock:
        logger.info(f"[N8N_MOCK] Simulated publishing payload to n8n: {payload.model_dump()}")
        return

    url = settings.n8n_webhook_url
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Secret": settings.n8n_shared_secret,
    }

    try:
        response = requests.post(url, json=payload.model_dump(), headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"n8n publishing webhook request failed: {e}")
        raise RuntimeError(f"n8n publish failed: {e}") from e
