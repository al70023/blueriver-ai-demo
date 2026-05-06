from pydantic import BaseModel, Field


class AnalyzeDocumentRequest(BaseModel):
    document_id: int
    max_chunks: int = Field(default=12, ge=3, le=30)


class ReviewRisk(BaseModel):
    title: str
    description: str
    severity: str = Field(description="low, medium, or high")
    citation_chunk_ids: list[int]


class SuggestedActionOut(BaseModel):
    id: int
    title: str
    description: str
    severity: str
    status: str
    citation_chunk_ids: list[int]


class AnalyzeDocumentResponse(BaseModel):
    document_id: int
    summary: str
    risks: list[ReviewRisk]
    suggested_actions: list[SuggestedActionOut]


class ReviewItemOut(BaseModel):
    id: int
    document_id: int
    title: str
    description: str
    severity: str
    status: str
    citation_chunk_ids: list[int]
