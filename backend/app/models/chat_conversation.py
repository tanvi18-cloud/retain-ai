"""RM copilot chat conversation records."""

from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.base import TimestampMixin, new_uuid
from app.models.enums import ChatConversationStatus


class ChatConversation(TimestampMixin, SQLModel, table=True):
    """Persisted RM chat conversation."""

    __tablename__ = "chat_conversations"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=36)
    rm_id: str = Field(nullable=False, index=True, max_length=64)
    title: str | None = Field(default=None, max_length=256, nullable=True)
    active_customer_id: str | None = Field(default=None, max_length=32, nullable=True)
    status: ChatConversationStatus = Field(
        default=ChatConversationStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    expires_at: datetime | None = Field(default=None, nullable=True)
