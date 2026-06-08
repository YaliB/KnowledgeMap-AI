from pydantic import BaseModel, Field
from typing import List


class ConceptExtracted(BaseModel):
    name: str = Field(..., max_length=60, description="Title case, max 60 chars")
    definition: str = Field(..., description="1-2 sentences, plain English")
    importance: float = Field(..., ge=1.0, le=10.0, description="GPT-4o scoring 1-10")
    tags: List[str] = Field(..., min_length=2, max_length=5, description="2-5 lowercase keywords")


class ConceptList(BaseModel):
    concepts: List[ConceptExtracted]


class Agent1Output(BaseModel):
    document_id: str
    user_id: str
    subject: str
    filename: str
    concepts: List[ConceptExtracted]
