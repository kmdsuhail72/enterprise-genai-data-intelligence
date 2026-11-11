"""Natural language RAG chat endpoints."""

import uuid

from fastapi import APIRouter, Depends

from enterprise_ai.api.dependencies import get_chat_service
from enterprise_ai.schemas.chat import ChatRequest, ChatResponse
from enterprise_ai.schemas.common import APIResponse
from enterprise_ai.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/query", response_model=APIResponse[ChatResponse])
async def execute_chat_query(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
) -> APIResponse[ChatResponse]:
    """Ask a natural-language question against ingested enterprise documents."""
    demo_user_id = uuid.uuid4()
    result = await chat_service.execute_query(
        question=request.question,
        user_id=demo_user_id,
        document_ids=request.document_ids,
    )
    chat_res = ChatResponse(
        query_id=uuid.UUID(result["query_id"]),
        question=result["question"],
        answer=result["answer"],
        citations=[],
        latency_ms=result["latency_ms"],
        llm_provider=request.llm_provider or "ollama",
        llm_model="default",
    )
    return APIResponse(success=True, data=chat_res)

