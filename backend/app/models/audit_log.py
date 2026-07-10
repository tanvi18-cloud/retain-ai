"""Audit trail records."""

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.models.base import CreatedAtMixin, new_uuid


class AuditLog(CreatedAtMixin, SQLModel, table=True):
    """Immutable audit log entry for entity changes and actions."""

    __tablename__ = "audit_logs"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=36)
    entity_type: str = Field(max_length=64, nullable=False, index=True)
    entity_id: str = Field(max_length=64, nullable=False, index=True)
    action: str = Field(max_length=64, nullable=False)
    actor_type: str = Field(max_length=64, nullable=False)
    actor_id: str | None = Field(default=None, max_length=64, nullable=True)
    details_json: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
