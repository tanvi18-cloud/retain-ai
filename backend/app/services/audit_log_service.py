"""Audit log write helpers."""

from __future__ import annotations

from typing import Any

from sqlmodel import Session

from app.models.audit_log import AuditLog


def write_audit_log(
    session: Session,
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    actor_type: str,
    actor_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> AuditLog:
    """Persist an immutable audit log entry."""
    entry = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_type=actor_type,
        actor_id=actor_id,
        details_json=details or {},
    )
    session.add(entry)
    return entry
