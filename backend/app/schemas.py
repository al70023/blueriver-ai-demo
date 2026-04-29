from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: int
    filename: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentChunkOut(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    text: str
    created_at: datetime

    class Config:
        from_attributes = True
