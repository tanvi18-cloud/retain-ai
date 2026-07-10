"""RM copilot chat API schemas."""

import re
from datetime import datetime

from pydantic import Field, field_validator

from app.models.enums import ChatConversationStatus, ChatIntent, ChatMessageRole
from app.schemas.common import APIModel
from app.schemas.llm import LLMMode

CUSTOMER_ID_PATTERN = re.compile(r"^C0\d{2}$")
VALID_CUSTOMER_IDS = frozenset(f"C{index:03d}" for index in range(1, 11))


class ChatRequest(APIModel):
    """Inbound RM chat message."""

    message: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = Field(default=None, max_length=36)
    rm_id: str = Field(min_length=1, max_length=64)
    customer_id: str | None = Field(default=None, max_length=32)
    include_history: bool = True

    @field_validator("message")
    @classmethod
    def validate_message_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message cannot be blank")
        return value.strip()

    @field_validator("customer_id")
    @classmethod
    def validate_customer_id_format(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if not CUSTOMER_ID_PATTERN.match(normalized):
            raise ValueError("Customer ID must match format C001 through C010")
        return normalized


class ChatEvidence(APIModel):
    """Evidence reference supporting a chat answer."""

    source_system: str
    source_type: str
    reference_id: str | None = None
    customer_id: str | None = None
    field: str
    value_summary: str
    timestamp: datetime | None = None


class ChatResponse(APIModel):
    """RM copilot chat response."""

    conversation_id: str
    message_id: str
    answer: str
    intent: ChatIntent
    customer_ids: list[str] = Field(default_factory=list)
    used_tools: list[str] = Field(default_factory=list)
    evidence: list[ChatEvidence] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    generated_at: datetime
    mode: LLMMode


class ConversationSummary(APIModel):
    """Compact conversation listing item."""

    conversation_id: str
    title: str | None
    active_customer_id: str | None
    last_message_preview: str | None
    message_count: int
    created_at: datetime
    updated_at: datetime
    status: ChatConversationStatus


class ChatMessageResponse(APIModel):
    """Persisted chat message for conversation detail."""

    message_id: str
    role: ChatMessageRole
    content: str
    customer_ids: list[str] = Field(default_factory=list)
    used_tools: list[str] = Field(default_factory=list)
    evidence: list[ChatEvidence] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime


class ConversationDetail(APIModel):
    """Conversation with limited message history."""

    conversation_id: str
    rm_id: str
    title: str | None
    active_customer_id: str | None
    status: ChatConversationStatus
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None
    messages: list[ChatMessageResponse] = Field(default_factory=list)


class ConversationCloseRequest(APIModel):
    """Request to close a chat conversation."""

    rm_id: str = Field(min_length=1, max_length=64)


class IntentDetectionResult(APIModel):
    """Deterministic intent detection output."""

    intent: ChatIntent
    confidence: float
    customer_ids: list[str] = Field(default_factory=list)
    trigger_type: str | None = None
    requested_limit: int | None = None
    extracted_terms: list[str] = Field(default_factory=list)
    requires_customer_context: bool = False
    unsupported_reason: str | None = None


class ChatContext(APIModel):
    """Resolved conversation and customer context."""

    conversation_id: str
    active_customer_id: str | None = None
    customer_ids: list[str] = Field(default_factory=list)
    recent_messages: list[ChatMessageResponse] = Field(default_factory=list)
    context_warnings: list[str] = Field(default_factory=list)
    ambiguous: bool = False
    clarification_question: str | None = None


class ChatValidationResult(APIModel):
    """Chat answer safety validation result."""

    valid: bool
    corrected: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    corrected_answer: str | None = None
    validated_at: datetime


class RMChatAgentOutput(APIModel):
    """Structured output from the RM chat agent."""

    answer: str
    intent: ChatIntent
    customer_ids: list[str] = Field(default_factory=list)
    used_tools: list[str] = Field(default_factory=list)
    evidence: list[ChatEvidence] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
