import json
from typing import TypedDict

from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document, DocumentChunk
from app.models.review import ReviewItem


class ReviewRiskDict(TypedDict):
    title: str
    description: str
    severity: str
    citation_chunk_ids: list[int]


class SuggestedActionDict(TypedDict):
    title: str
    description: str
    severity: str
    citation_chunk_ids: list[int]


class StructuredReviewDict(TypedDict):
    summary: str
    risks: list[ReviewRiskDict]
    suggested_actions: list[SuggestedActionDict]


class SuggestedActionOutDict(TypedDict):
    id: int
    title: str
    description: str
    severity: str
    status: str
    citation_chunk_ids: list[int]


class AnalyzedDocumentDict(TypedDict):
    document_id: int
    summary: str
    risks: list[ReviewRiskDict]
    suggested_actions: list[SuggestedActionOutDict]


def get_document_context_chunks(
    *,
    db: Session,
    document_id: int,
    max_chunks: int,
) -> list[dict[str, int | str]]:
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
        .limit(max_chunks)
        .all()
    )

    return [
        {
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
            "text": chunk.text,
        }
        for chunk in chunks
    ]


def format_review_context(chunks: list[dict[str, int | str]]) -> str:
    formatted: list[str] = []

    for chunk in chunks:
        formatted.append(
            f"[chunk_id={chunk['chunk_id']}, chunk_index={chunk['chunk_index']}]\n"
            f"{chunk['text']}"
        )

    return "\n\n---\n\n".join(formatted)


def generate_structured_review(
    *,
    chunks: list[dict[str, int | str]],
) -> StructuredReviewDict:
    if not chunks:
        raise ValueError("No chunks available for review.")

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not configured.")

    client = OpenAI(api_key=settings.openai_api_key)

    context = format_review_context(chunks)

    prompt = f"""
    You are an AI document review assistant.

    Review the provided document context and produce a structured review.

    Use only the provided context. Do not invent facts.

    Return valid JSON only. Do not include markdown fences.

    The JSON must have this exact shape:

    {{
    "summary": "Brief summary of the document context.",
    "risks": [
        {{
        "title": "Short risk title",
        "description": "Why this may need human review.",
        "severity": "low | medium | high",
        "citation_chunk_ids": [1, 2]
        }}
    ],
    "suggested_actions": [
        {{
        "title": "Short action title",
        "description": "Specific suggested next action for the reviewer.",
        "severity": "low | medium | high",
        "citation_chunk_ids": [1, 2]
        }}
    ]
    }}

    Rules:
    - Use only chunk IDs that appear in the provided context.
    - If there are no clear risks, return an empty risks list.
    - If there are no clear actions, return an empty suggested_actions list.
    - Keep titles concise.
    - Make actions practical and review-oriented.
    - Every risk and action should cite at least one chunk_id.

    Document context:
    {context}
    """

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": "You produce structured JSON document reviews using only provided context.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content or ""

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON: {str(e)}")


def save_review_items(
    *,
    db: Session,
    document_id: int,
    suggested_actions: list[SuggestedActionDict],
) -> list[ReviewItem]:
    saved_items: list[ReviewItem] = []

    for action in suggested_actions:
        item = ReviewItem(
            document_id=document_id,
            title=action.get("title", "Suggested action"),
            description=action.get("description", ""),
            severity=action.get("severity", "medium"),
            status="open",
            citation_chunk_ids=json.dumps(action.get("citation_chunk_ids", [])),
        )

        db.add(item)
        db.flush()
        saved_items.append(item)

    return saved_items


def analyze_document(
    *,
    db: Session,
    document_id: int,
    max_chunks: int,
) -> AnalyzedDocumentDict:
    document = db.get(Document, document_id)

    if document is None:
        raise ValueError("Document not found.")

    chunks = get_document_context_chunks(
        db=db,
        document_id=document_id,
        max_chunks=max_chunks,
    )

    if not chunks:
        raise ValueError("Document has no chunks to analyze.")

    review = generate_structured_review(chunks=chunks)

    db.query(ReviewItem).filter(ReviewItem.document_id == document_id).delete()
    db.flush()

    saved_items = save_review_items(
        db=db,
        document_id=document_id,
        suggested_actions=review["suggested_actions"],
    )

    db.commit()

    suggested_actions_out: list[SuggestedActionOutDict] = []

    for item in saved_items:
        try:
            citation_chunk_ids = json.loads(item.citation_chunk_ids or "[]")
        except json.JSONDecodeError:
            citation_chunk_ids = []

        suggested_actions_out.append(
            {
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "severity": item.severity,
                "status": item.status,
                "citation_chunk_ids": citation_chunk_ids,
            }
        )

    return {
        "document_id": document_id,
        "summary": review.get("summary", ""),
        "risks": review.get("risks", []),
        "suggested_actions": suggested_actions_out,
    }
