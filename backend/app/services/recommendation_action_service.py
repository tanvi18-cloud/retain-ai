"""Recommendation workflow action service."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Session, select

from app.core.exceptions import InvalidStatusTransitionError, ResourceNotFoundError
from app.core.policy_rules import ELIGIBILITY_DISCLAIMER
from app.models.enums import RecommendationStatus
from app.models.interaction import Interaction
from app.models.recommendation import Recommendation
from app.schemas.recommendation_actions import RecommendationActionResponse
from app.services.audit_log_service import write_audit_log

ALLOWED_TRANSITIONS: dict[RecommendationStatus, set[RecommendationStatus]] = {
    RecommendationStatus.NEW: {
        RecommendationStatus.REVIEWED,
        RecommendationStatus.APPROVED,
        RecommendationStatus.REJECTED,
    },
    RecommendationStatus.REVIEWED: {
        RecommendationStatus.APPROVED,
        RecommendationStatus.REJECTED,
        RecommendationStatus.CONTACTED,
    },
    RecommendationStatus.APPROVED: {
        RecommendationStatus.CONTACTED,
        RecommendationStatus.CLOSED,
    },
    RecommendationStatus.REJECTED: {RecommendationStatus.CLOSED},
    RecommendationStatus.CONTACTED: {RecommendationStatus.CLOSED},
    RecommendationStatus.CLOSED: set(),
}

APPROVAL_DISCLAIMER = (
    "RM approval indicates authorization to discuss the recommendation; "
    "it does not represent credit, product, or pricing approval."
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class RecommendationActionService:
    """Handle RM workflow actions on recommendations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def review(
        self,
        recommendation_id: str,
        *,
        rm_id: str,
        notes: str | None = None,
        idempotency_key: str | None = None,
    ) -> RecommendationActionResponse:
        return self._transition(
            recommendation_id,
            target=RecommendationStatus.REVIEWED,
            rm_id=rm_id,
            notes=notes,
            action_type="RECOMMENDATION_REVIEWED",
            idempotency_key=idempotency_key,
        )

    def approve(
        self,
        recommendation_id: str,
        *,
        rm_id: str,
        notes: str | None = None,
        idempotency_key: str | None = None,
    ) -> RecommendationActionResponse:
        note_text = notes or APPROVAL_DISCLAIMER
        return self._transition(
            recommendation_id,
            target=RecommendationStatus.APPROVED,
            rm_id=rm_id,
            notes=note_text,
            action_type="RECOMMENDATION_APPROVED",
            idempotency_key=idempotency_key,
        )

    def reject(
        self,
        recommendation_id: str,
        *,
        rm_id: str,
        rejection_reason: str,
        notes: str | None = None,
        idempotency_key: str | None = None,
    ) -> RecommendationActionResponse:
        combined = rejection_reason if notes is None else f"{rejection_reason}. {notes}"
        return self._transition(
            recommendation_id,
            target=RecommendationStatus.REJECTED,
            rm_id=rm_id,
            notes=combined,
            action_type="RECOMMENDATION_REJECTED",
            idempotency_key=idempotency_key,
        )

    def contacted(
        self,
        recommendation_id: str,
        *,
        rm_id: str,
        notes: str | None = None,
        offer_presented: bool = False,
        customer_response: str | None = None,
        contact_channel: str | None = None,
        follow_up_date=None,
        idempotency_key: str | None = None,
    ) -> RecommendationActionResponse:
        return self._transition(
            recommendation_id,
            target=RecommendationStatus.CONTACTED,
            rm_id=rm_id,
            notes=notes,
            action_type="RECOMMENDATION_CONTACTED",
            idempotency_key=idempotency_key,
            offer_presented=offer_presented,
            customer_response=customer_response,
            contact_channel=contact_channel,
            follow_up_date=follow_up_date,
        )

    def close(
        self,
        recommendation_id: str,
        *,
        rm_id: str,
        closing_note: str,
        idempotency_key: str | None = None,
    ) -> RecommendationActionResponse:
        return self._transition(
            recommendation_id,
            target=RecommendationStatus.CLOSED,
            rm_id=rm_id,
            notes=closing_note,
            action_type="RECOMMENDATION_CLOSED",
            idempotency_key=idempotency_key,
        )

    def _transition(
        self,
        recommendation_id: str,
        *,
        target: RecommendationStatus,
        rm_id: str,
        notes: str | None,
        action_type: str,
        idempotency_key: str | None = None,
        **interaction_fields,
    ) -> RecommendationActionResponse:
        if idempotency_key:
            existing = self.session.exec(
                select(Interaction).where(Interaction.idempotency_key == idempotency_key)
            ).first()
            if existing is not None:
                recommendation = self.session.get(Recommendation, existing.recommendation_id)
                if recommendation is None:
                    raise ResourceNotFoundError(
                        code="RECOMMENDATION_NOT_FOUND",
                        message=f"Recommendation {recommendation_id} was not found",
                    )
                return RecommendationActionResponse(
                    recommendation_id=recommendation.id,
                    status=recommendation.status.value,
                    interaction_id=existing.id,
                    message="Idempotent action already recorded",
                )

        recommendation = self.session.get(Recommendation, recommendation_id)
        if recommendation is None:
            raise ResourceNotFoundError(
                code="RECOMMENDATION_NOT_FOUND",
                message=f"Recommendation {recommendation_id} was not found",
            )

        allowed = ALLOWED_TRANSITIONS.get(recommendation.status, set())
        if recommendation.status == target:
            interaction = self._find_latest_interaction(recommendation_id, action_type)
            if interaction:
                return RecommendationActionResponse(
                    recommendation_id=recommendation.id,
                    status=recommendation.status.value,
                    interaction_id=interaction.id,
                    message="Action already applied",
                )
        elif target not in allowed:
            raise InvalidStatusTransitionError(
                message=f"Cannot transition from {recommendation.status.value} to {target.value}",
                details={
                    "current_status": recommendation.status.value,
                    "requested_status": target.value,
                },
            )

        recommendation.status = target
        recommendation.updated_at = _utc_now()
        self.session.add(recommendation)

        interaction = Interaction(
            customer_id=recommendation.customer_id,
            recommendation_id=recommendation.id,
            rm_id=rm_id,
            action_type=action_type,
            notes=notes,
            idempotency_key=idempotency_key,
            **interaction_fields,
        )
        self.session.add(interaction)
        self.session.flush()

        write_audit_log(
            self.session,
            entity_type="recommendations",
            entity_id=recommendation.id,
            action=action_type,
            actor_type="RM",
            actor_id=rm_id,
            details={"notes": notes, "disclaimer": ELIGIBILITY_DISCLAIMER},
        )

        return RecommendationActionResponse(
            recommendation_id=recommendation.id,
            status=recommendation.status.value,
            interaction_id=interaction.id,
            message=f"Recommendation marked {target.value}",
        )

    @staticmethod
    def _find_latest_interaction(recommendation_id: str, action_type: str) -> Interaction | None:
        return None
