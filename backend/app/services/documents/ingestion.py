from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk
from app.services.ai.embeddings import embed_texts
from app.services.documents.chunking import chunk_text
from app.services.documents.text_extraction import extract_text_from_upload
from app.services.vector_store.qdrant import upsert_chunk_vectors


def ingest_document(
    *,
    filename: str,
    raw_bytes: bytes,
    db: Session,
) -> Document:
    text = extract_text_from_upload(filename, raw_bytes)

    chunks = chunk_text(text)

    if not chunks:
        raise ValueError("Uploaded file contains no readable text.")

    document = Document(filename=filename)
    db.add(document)
    db.flush()

    saved_chunk_records: list[dict[str, int | str]] = []

    for index, chunk in enumerate(chunks):
        document_chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=index,
            text=chunk,
        )

        db.add(document_chunk)
        db.flush()

        saved_chunk_records.append(
            {
                "chunk_id": document_chunk.id,
                "document_id": document.id,
                "filename": document.filename,
                "chunk_index": document_chunk.chunk_index,
                "text": document_chunk.text,
            }
        )

    chunk_texts = [record["text"] for record in saved_chunk_records]
    vectors = embed_texts(chunk_texts)

    upsert_chunk_vectors(
        chunk_records=saved_chunk_records,
        vectors=vectors,
    )

    db.commit()
    db.refresh(document)

    return document
