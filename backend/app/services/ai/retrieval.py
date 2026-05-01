from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.services.ai.embeddings import embed_texts
from app.services.vector_store.qdrant import COLLECTION_NAME, get_qdrant_client


def search_similar_chunks(
    *,
    query: str,
    document_id: int | None = None,
    limit: int = 5,
) -> list[dict[str, str | int | float | None]]:
    query_vector = embed_texts([query])[0]

    client = get_qdrant_client()

    search_filter = None

    if document_id is not None:
        search_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=search_filter,
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )

    matches: list[dict[str, str | int | float | None]] = []

    for point in results.points:
        payload = point.payload or {}

        matches.append(
            {
                "chunk_id": payload.get("chunk_id"),
                "document_id": payload.get("document_id"),
                "filename": payload.get("filename"),
                "chunk_index": payload.get("chunk_index"),
                "score": point.score,
                "text": payload.get("text"),
            }
        )

    return matches
