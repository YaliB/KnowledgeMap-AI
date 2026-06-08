from pydantic import BaseModel
from typing import List


class Concept(BaseModel):
    name: str
    definition: str
    importance: float
    tags: List[str]


class ExtractorOutput(BaseModel):
    document_id: int
    user_id: str
    subject: str
    filename: str
    concepts: List[Concept]
