from typing import TypedDict, Optional, Any

from schemas.concept import ConceptExtracted


class ExtractorState(TypedDict):
    document_id: str
    user_id: str
    subject: str
    filename: str
    file_path: str
    raw_chunks: list[str]
    concepts: list[ConceptExtracted]
    error: Optional[str]
    # injected dependencies — passed in at graph.invoke() time
    concept_repo: Any   # AbstractConceptRepo
    document_repo: Any  # AbstractDocumentRepo
    pdf_service: Any    # AbstractPDFService
