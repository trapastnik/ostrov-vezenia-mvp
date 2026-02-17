import json

import httpx

from app.core.security import compute_webhook_signature


async def send_webhook_request(webhook_url: str, payload: dict, api_key: str) -> bool:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    signature = compute_webhook_signature(body, api_key)

    headers = {
        "Content-Type": "application/json",
        "X-Ostrov-Signature": signature,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook_url, content=body, headers=headers)
            return resp.status_code < 400
    except Exception:
        return False
