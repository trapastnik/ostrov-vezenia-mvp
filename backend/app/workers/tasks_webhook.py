import json
import logging

import httpx

from app.core.security import compute_webhook_signature
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    max_retries=5,
    time_limit=30,
    soft_time_limit=25,
)
def send_webhook(self, webhook_url: str, payload: dict, api_key: str):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    signature = compute_webhook_signature(body, api_key)

    headers = {
        "Content-Type": "application/json",
        "X-Ostrov-Signature": signature,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(webhook_url, content=body, headers=headers)
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if 400 <= exc.response.status_code < 500:
            # 4xx — ошибка клиента, ретрай бесполезен
            logger.warning(
                "Webhook %s returned %s, not retrying",
                webhook_url, exc.response.status_code,
            )
            return
        # 5xx — серверная ошибка, ретраим с exponential backoff
        backoff = 60 * (2 ** self.request.retries)  # 60s, 120s, 240s, 480s, 960s
        raise self.retry(exc=exc, countdown=backoff)
    except Exception as exc:
        backoff = 60 * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=backoff)
