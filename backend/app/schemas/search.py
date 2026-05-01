from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    document_id: int | None = None
    limit: int = Field(default=5, ge=1, le=20)


class SearchMatch(BaseModel):
    chunk_id: int
    document_id: int
    filename: str
    chunk_index: int
    score: float
    text: str


class SearchResponse(BaseModel):
    query: str
    matches: list[SearchMatch]
