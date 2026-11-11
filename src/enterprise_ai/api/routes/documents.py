"""Document management and upload endpoints."""

import uuid

from fastapi import APIRouter, Depends, File, UploadFile

from enterprise_ai.api.dependencies import get_document_service
from enterprise_ai.schemas.common import APIResponse
from enterprise_ai.schemas.document import DocumentResponse
from enterprise_ai.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=APIResponse[DocumentResponse])
async def upload_document(
    file: UploadFile = File(...),
    doc_service: DocumentService = Depends(get_document_service),
) -> APIResponse[DocumentResponse]:
    """Upload a document for parsing and vector indexing."""
    # Synthetic user_id until auth integration is active
    demo_user_id = uuid.uuid4()
    doc = await doc_service.upload_document(
        file_obj=file.file,
        filename=file.filename or "uploaded_file",
        user_id=demo_user_id,
    )
    return APIResponse(
        success=True,
        data=DocumentResponse.model_validate(doc),
        message="Document uploaded successfully",
    )


@router.get("/{document_id}", response_model=APIResponse[DocumentResponse])
async def get_document(
    document_id: uuid.UUID,
    doc_service: DocumentService = Depends(get_document_service),
) -> APIResponse[DocumentResponse]:
    """Retrieve document metadata by ID."""
    doc = await doc_service.get_document(document_id)
    return APIResponse(success=True, data=DocumentResponse.model_validate(doc))


@router.get("/", response_model=APIResponse[list[DocumentResponse]])
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    doc_service: DocumentService = Depends(get_document_service),
) -> APIResponse[list[DocumentResponse]]:
    """List documents with pagination."""
    docs = await doc_service.list_documents(skip=skip, limit=limit)
    return APIResponse(
        success=True,
        data=[DocumentResponse.model_validate(d) for d in docs],
    )

