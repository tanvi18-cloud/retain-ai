"""RM copilot chat message records."""

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.models.base import CreatedAtMixin, new_uuid
from app.models.enums import ChatMessageRole


class ChatMessage(CreatedAtMixin, SQLModel, table=True):
    """Persisted chat message without hidden reasoning."""

    __tablename__ = "chat_messages"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=36)
    conversation_id: str = Field(
        foreign_key="chat_conversations.id",
        nullable=False,
        index=True,
        max_length=36,
    )
    role: ChatMessageRole = Field(nullable=False)
    content: str = Field(max_length=4096, nullable=False)
    customer_ids_json: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    used_tools_json: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    evidence_json: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    warnings_json: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
