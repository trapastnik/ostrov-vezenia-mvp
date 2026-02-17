import json

import httpx

from app.core.security import compute_webhook_signature
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=5, default_retry_delay=60)
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
    except Exception as exc:
        raise self.retry(exc=exc)
