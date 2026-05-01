from fastapi import APIRouter

from app.schemas.search import SearchRequest, SearchResponse
from app.services.ai.retrieval import search_similar_chunks

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search_documents(
    request: SearchRequest,
) -> dict[str, str | list[dict[str, str | float | None]]]:
    matches = search_similar_chunks(
        query=request.query,
        document_id=request.document_id,
        limit=request.limit,
    )

    return {
        "query": request.query,
        "matches": matches,
    }
