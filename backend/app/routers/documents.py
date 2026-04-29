from app.db import get_db
from app.models import Document, DocumentChunk
from app.schemas import DocumentChunkOut, DocumentOut
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

router = APIRouter(prefix="/documents", tags=["documents"])


def chunk_text(text: str, chunk_size: int = 1000) -> list[str]:
    cleaned_text = text.strip()

    if not cleaned_text:
        return []

    chunks: list[str] = []

    for start in range(0, len(cleaned_text), chunk_size):
        chunk = cleaned_text[start : start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)

    return chunks


@router.post("/upload", response_model=DocumentOut)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.filename and not file.filename.endswith("txt"):
        raise HTTPException(
            status_code=400, detail="Only .txt files are supported today."
        )

    raw_bytes = await file.read()

    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400, detail="Could not read file as UTF-8 text."
        )

    chunks = chunk_text(text)

    if not chunks:
        raise HTTPException(
            status_code=400, detail="Uploaded file contains no readable text."
        )

    document = Document(filename=file.filename)

    db.add(document)
    db.flush()

    for index, chunk in enumerate(chunks):
        db.add(DocumentChunk(document_id=document.id, chunk_index=index, text=chunk))

    db.commit()
    db.refresh(document)

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
