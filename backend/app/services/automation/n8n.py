import httpx

from app.core.config import settings
from app.models.review import ReviewItem


def send_review_item_to_n8n(item: ReviewItem) -> dict[str, bool | int | str]:
    if not settings.n8n_webhook_url:
        return {
            "sent": False,
            "reason": "N8N_WEBHOOK_URL is not configured.",
        }

    payload: dict[str, int | str | None] = {
        "review_item_id": item.id,
        "document_id": item.document_id,
        "title": item.title,
        "description": item.description,
        "severity": item.severity,
        "status": item.status,
        "citation_chunk_ids": item.citation_chunk_ids,
    }

    response = httpx.post(
        settings.n8n_webhook_url,
        json=payload,
        timeout=10,
    )

    response.raise_for_status()

    return {
        "sent": True,
        "status_code": response.status_code,
        "response": response.text,
    }
