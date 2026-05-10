import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.review import ReviewItem
from app.schemas.review import AnalyzeDocumentRequest, AnalyzeDocumentResponse
from app.services.audit.logger import create_audit_log
from app.services.automation.n8n import send_review_item_to_n8n
from app.services.review.analyzer import analyze_document

router = APIRouter(prefix="/review", tags=["review"])


@router.post("/analyze", response_model=AnalyzeDocumentResponse)
def analyze_document_route(
    request: AnalyzeDocumentRequest,
    db: Session = Depends(get_db),
):
    try:
        return analyze_document(
            db=db,
            document_id=request.document_id,
            max_chunks=request.max_chunks,
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Document analysis failed: {str(e)}",
        )


@router.get("/documents/{document_id}/items")
def list_review_items(
    document_id: int,
    db: Session = Depends(get_db),
):
    items = (
        db.query(ReviewItem)
        .filter(ReviewItem.document_id == document_id)
        .order_by(ReviewItem.created_at.desc())
        .all()
    )

    response: list[dict[str, int | str | list[int]]] = []

    for item in items:
        try:
            citation_chunk_ids = json.loads(item.citation_chunk_ids or "[]")
        except json.JSONDecodeError:
            citation_chunk_ids = []

        response.append(
            {
                "id": item.id,
                "document_id": item.document_id,
                "title": item.title,
                "description": item.description,
                "severity": item.severity,
                "status": item.status,
                "citation_chunk_ids": citation_chunk_ids,
            }
        )

    return response


@router.post("/items/{item_id}/approve")
def approve_review_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> dict[str, int | str | dict[str, bool | int | str]]:
    item = db.get(ReviewItem, item_id)

    if item is None:
        raise HTTPException(status_code=404, detail="Review item not found.")

    item.status = "approved"

    webhook_result = send_review_item_to_n8n(item)

    create_audit_log(
        db=db,
        action="review_item_approved",
        entity_type="review_item",
        entity_id=item.id,
    )

    db.commit()
    db.refresh(item)

    return {
        "id": item.id,
        "document_id": item.document_id,
        "title": item.title,
        "description": item.description,
        "severity": item.severity,
        "status": item.status,
        "webhook_result": webhook_result,
    }
