from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from apis.dependencies import get_current_user, get_document_repo, get_concept_repo
from infrastructure.repositories.abstractions.document_repo import AbstractDocumentRepo
from infrastructure.repositories.abstractions.concept_repo import AbstractConceptRepo
from services.db_service import get_graph_for_user
from agent.pipeline import run_extraction_pipeline

router = APIRouter()


@router.post("/extract", status_code=202)
async def extract(
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
    doc_repo: AbstractDocumentRepo = Depends(get_document_repo),
):
    docs = await doc_repo.get_user_documents(user_id)
    pending = [d for d in docs if d.get("status") == "pending"]
    for doc in pending:
        background_tasks.add_task(
            run_extraction_pipeline,
            document_id=doc["id"],
            user_id=user_id,
            file_path=doc["file_path"],
            subject=doc["subject"],
        )
    return {"status": "processing", "message": f"Extraction started for {len(pending)} documents"}


@router.get("/graph")
async def get_graph(user_id: str = Depends(get_current_user)):
    return await get_graph_for_user(user_id)


@router.get("/concept/{concept_id}")
async def get_concept(
    concept_id: str,
    user_id: str = Depends(get_current_user),
    concept_repo: AbstractConceptRepo = Depends(get_concept_repo),
    doc_repo: AbstractDocumentRepo = Depends(get_document_repo),
):
    concept = await concept_repo.get_concept_by_id(concept_id, user_id)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
    neighbors = await concept_repo.get_concept_neighbors(concept_id, user_id)
    sources = await doc_repo.get_document_for_concept(concept_id, user_id)
    return {"concept": concept, "neighbors": neighbors, "sources": sources}
