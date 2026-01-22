from pydantic import BaseModel, Field

class Citiation(BaseModel):
    source_id: int
    page: int 
    quote: str

class AskQuestionResponse(BaseModel):
    answer: str
    citations: list[Citiation] = Field(default_factory=list)