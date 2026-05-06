import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.review import ReviewItem
from app.schemas.review import AnalyzeDocumentRequest, AnalyzeDocumentResponse
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
