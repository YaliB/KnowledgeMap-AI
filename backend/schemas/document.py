from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    filename: str
    subject: str
    status: str
    page_count: int
    created_at: str


class UploadResponse(BaseModel):
    documents: list[DocumentResponse]
