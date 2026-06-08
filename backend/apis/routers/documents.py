from fastapi import APIRouter, Depends, File, Form, UploadFile

from apis.dependencies import get_current_user, get_document_service
from services.document_service import AbstractDocumentService

router = APIRouter()


@router.post("/upload")
async def upload(
    files: list[UploadFile] = File(...),
    subjects: list[str] = Form(...),
    user_id: str = Depends(get_current_user),
    document_service: AbstractDocumentService = Depends(get_document_service),
):
    return await document_service.upload(files, subjects, user_id)


@router.get("/documents")
async def get_documents(
    user_id: str = Depends(get_current_user),
    document_service: AbstractDocumentService = Depends(get_document_service),
):
    docs = await document_service.get_documents(user_id)
    return {"documents": docs}


@router.delete("/document/{doc_id}")
async def delete_document(
    doc_id: str,
    user_id: str = Depends(get_current_user),
    document_service: AbstractDocumentService = Depends(get_document_service),
):
    await document_service.delete_document(doc_id, user_id)
    return {"message": "deleted"}
