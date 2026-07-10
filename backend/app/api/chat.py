"""RM copilot chat API routes."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.database import get_session
from app.models.enums import ChatConversationStatus
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationCloseRequest,
    ConversationDetail,
    ConversationSummary,
)
from app.schemas.common import ApiErrorResponse, PaginatedResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])

NOT_FOUND_RESPONSE = {
    404: {"model": ApiErrorResponse, "description": "Conversation or customer not found"},
}
CONFLICT_RESPONSE = {
    409: {"model": ApiErrorResponse, "description": "Conversation is closed"},
}
FORBIDDEN_RESPONSE = {
    403: {"model": ApiErrorResponse, "description": "RM cannot access conversation"},
}

SortOrder = Literal["asc", "desc"]


@router.post(
    "",
    response_model=ChatResponse,
    summary="Send RM copilot chat message",
    description=(
        "Ask portfolio or customer retention questions. Uses deterministic mock mode "
        "when MOCK_LLM_MODE=true, otherwise Qwen with safe read-only tools."
    ),
    responses={
        400: {"model": ApiErrorResponse},
        403: FORBIDDEN_RESPONSE[403],
        404: NOT_FOUND_RESPONSE[404],
        409: CONFLICT_RESPONSE[409],
        422: {"model": ApiErrorResponse},
        503: {"model": ApiErrorResponse},
    },
    openapi_extra={
        "examples": {
            "urgency": {
                "summary": "Why is C001 urgent?",
                "value": {
                    "message": "Why is C001 urgent?",
                    "rm_id": "RM-01",
                    "customer_id": "C001",
                    "include_history": True,
                },
            },
            "priority": {
                "summary": "Who should I call today?",
                "value": {
                    "message": "Who should I call today?",
                    "rm_id": "RM-01",
                    "include_history": True,
                },
            },
            "compare": {
                "summary": "Compare C001 and C008",
                "value": {
                    "message": "Compare C001 and C008.",
                    "rm_id": "RM-01",
                    "include_history": True,
                },
            },
        }
    },
)
def send_chat_message(
    body: ChatRequest,
    session: Annotated[Session, Depends(get_session)],
) -> ChatResponse:
    """Process an RM chat message."""
    service = ChatService(session)
    response = service.chat(body)
    session.commit()
    return response


@router.get(
    "/conversations",
    response_model=PaginatedResponse[ConversationSummary],
    summary="List RM chat conversations",
)
def list_conversations(
    session: Annotated[Session, Depends(get_session)],
    rm_id: Annotated[str, Query(min_length=1, description="RM identifier (required)")],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status: Annotated[ChatConversationStatus | None, Query()] = None,
    sort_order: Annotated[SortOrder, Query()] = "desc",
) -> PaginatedResponse[ConversationSummary]:
    """List conversations for an RM."""
    service = ChatService(session)
    return service.list_conversations(
        rm_id=rm_id,
        page=page,
        page_size=page_size,
        status=status,
        sort_order=sort_order,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetail,
    summary="Get conversation detail",
    responses={**NOT_FOUND_RESPONSE, **FORBIDDEN_RESPONSE},
)
def get_conversation(
    conversation_id: str,
    session: Annotated[Session, Depends(get_session)],
    rm_id: Annotated[str, Query(min_length=1, description="RM identifier (required)")],
) -> ConversationDetail:
    """Return conversation detail with limited message history."""
    service = ChatService(session)
    return service.get_conversation_detail(conversation_id, rm_id=rm_id)


@router.post(
    "/conversations/{conversation_id}/close",
    response_model=ConversationDetail,
    summary="Close a chat conversation",
    responses={**NOT_FOUND_RESPONSE, **FORBIDDEN_RESPONSE},
)
def close_conversation(
    conversation_id: str,
    body: ConversationCloseRequest,
    session: Annotated[Session, Depends(get_session)],
) -> ConversationDetail:
    """Close a conversation so it cannot receive new messages."""
    service = ChatService(session)
    detail = service.close_conversation(conversation_id, rm_id=body.rm_id)
    session.commit()
    return detail
