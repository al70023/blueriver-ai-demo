from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from qdrant_client.models import FieldCondition, Filter, MatchValue
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Document, DocumentChunk
from app.schemas.document import DocumentChunkOut, DocumentOut
from app.services.documents.ingestion import ingest_document
from app.services.vector_store.qdrant import (
    COLLECTION_NAME,
    get_qdrant_client,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid file name.",
        )

    if not file.filename.lower().endswith((".txt", ".pdf")):
        raise HTTPException(
            status_code=400,
            detail="Only .txt and .pdf files are supported today.",
        )

    raw_bytes = await file.read()

    try:
        document = ingest_document(
            filename=file.filename,
            raw_bytes=raw_bytes,
            db=db,
        )
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Could not read file as UTF-8 text.",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Could not extract text from file: {str(e)}",
        )

    return document


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    return db.query(Document).order_by(Document.created_at.desc()).all()


@router.get("/{document_id}/chunks", response_model=list[DocumentChunkOut])
def list_document_chunks(document_id: int, db: Session = Depends(get_db)):
    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    return (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )


@router.get("/{document_id}/vector-status")
def get_document_vector_status(
    document_id: int,
    db: Session = Depends(get_db),
) -> dict[str, int | str | bool]:
    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    postgres_chunk_count = (
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).count()
    )

    client = get_qdrant_client()

    try:
        scroll_result = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            ),
            limit=1000,
            with_payload=True,
            with_vectors=False,
        )

        qdrant_points = scroll_result[0]
        qdrant_vectror_count = len(qdrant_points)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not check Qdrant vector status: {str(e)}",
        )

    return {
        "document_id": document_id,
        "filename": document.filename,
        "postgres_chunk_count": postgres_chunk_count,
        "qdrant_vector_count": qdrant_vectror_count,
        "in_sync": postgres_chunk_count == qdrant_vectror_count,
    }
