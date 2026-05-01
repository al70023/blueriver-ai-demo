from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    document_id: int | None = None
    limit: int = Field(default=5, ge=1, le=10)


class Citation(BaseModel):
    chunk_id: int
    document_id: int
    filename: str
    chunk_index: int
    score: float
    text: str


class AskResponse(BaseModel):
    question: str
    answer: str
    citations: list[Citation]
