from fastapi import APIRouter

from app.schemas.ask import AskRequest, AskResponse
from app.services.ai.llm import generate_answer_from_context
from app.services.ai.retrieval import search_similar_chunks

router = APIRouter(prefix="/ask", tags=["ask"])


@router.post("", response_model=AskResponse)
def ask_document(
    request: AskRequest,
) -> dict[str, str | list[dict[str, str | int | float | None]]]:
    matches = search_similar_chunks(
        query=request.question,
        document_id=request.document_id,
        limit=request.limit,
    )

    answer = generate_answer_from_context(
        question=request.question,
        context_chunks=matches,
    )

    citations = [
        {
            "chunk_id": match["chunk_id"],
            "document_id": match["document_id"],
            "filename": match["filename"],
            "chunk_index": match["chunk_index"],
            "score": match["score"],
            "text": match["text"],
        }
        for match in matches
    ]

    return {
        "question": request.question,
        "answer": answer,
        "citations": citations,
    }
