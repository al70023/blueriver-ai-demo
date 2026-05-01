from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings

COLLECTION_NAME = "document_chunks"
VECTOR_SIZE = 384


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url)


def ensure_document_chunks_collection() -> None:
    client = get_qdrant_client()

    collections = client.get_collections().collections
    existing_collection_names = {collection.name for collection in collections}

    if COLLECTION_NAME in existing_collection_names:
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )


def upsert_chunk_vectors(
    chunk_records: list[dict[str, int | str]], vectors: list[list[float]]
) -> None:
    if len(chunk_records) != len(vectors):
        raise ValueError("chunk_records and vectors must have the same length.")

    ensure_document_chunks_collection()

    client = get_qdrant_client()

    points: list[PointStruct] = []

    for chunk_record, vector in zip(chunk_records, vectors):
        points.append(
            PointStruct(
                id=chunk_record["chunk_id"],
                vector=vector,
                payload={
                    "chunk_id": chunk_record["chunk_id"],
                    "document_id": chunk_record["document_id"],
                    "filename": chunk_record["filename"],
                    "chunk_index": chunk_record["chunk_index"],
                    "text": chunk_record["text"],
                },
            )
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)
