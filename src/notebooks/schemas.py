from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

class NotebookSchema(BaseModel):
    id: int
    user_id: int
    title: str

    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SourceSchema(BaseModel):
    id: int
    notebook_id: int
    file_path: str
    filename: str

    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1)
    source_ids: Optional[list[int]] = Field(None)
    mode: str = Field("mmr")