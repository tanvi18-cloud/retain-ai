"""Repository layer tests."""

from datetime import UTC, datetime

import pytest
from sqlmodel import Session

from app.core.exceptions import InvalidPaginationError, ResourceNotFoundError
from app.models.enums import CustomerSegment, RecommendationDecision, RecommendationStatus
from app.models.recommendation import Recommendation
from app.services.alert_repository import AlertRepository
from app.services.customer_repository import CustomerRepository
from app.services.event_repository import EventRepository
from app.services.interaction_repository import InteractionRepository
from app.services.offer_repository import OfferRepository
from app.services.recommendation_repository import RecommendationRepository


def test_customer_get_and_list(seeded_session: Session) -> None:
    """CustomerRepository returns detail and paginated summaries."""
    repository = CustomerRepository(seeded_session)

    detail = repository.get_by_id("C001")
    listing = repository.list_customers(page=1, page_size=2)

    assert detail.customer_id == "C001"
    assert detail.full_name == "Alex Synthetic"
    assert listing.total == 3
    assert listing.page == 1
    assert listing.page_size == 2
    assert len(listing.items) == 2


def test_customer_search_by_id_or_name(seeded_session: Session) -> None:
    """CustomerRepository search matches customer ID or full name."""
    repository = CustomerRepository(seeded_session)

    by_id = repository.list_customers(search="C003")
    by_name = repository.list_customers(search="Priority")

    assert by_id.total == 1
    assert by_id.items[0].customer_id == "C003"
    assert by_name.total == 1
    assert by_name.items[0].full_name == "Casey Priority"


def test_customer_segment_filter(seeded_session: Session) -> None:
    """CustomerRepository filters customers by segment."""
    repository = CustomerRepository(seeded_session)

    result = repository.list_customers(segment=CustomerSegment.STANDARD)

    assert result.total == 1
    assert result.items[0].customer_id == "C002"


def test_customer_count_customers(seeded_session: Session) -> None:
    """CustomerRepository count reflects applied filters."""
    repository = CustomerRepository(seeded_session)

    assert repository.count_customers() == 3
    assert repository.count_customers(segment=CustomerSegment.PRIORITY) == 1


def test_customer_missing_resource_error(seeded_session: Session) -> None:
    """CustomerRepository raises ResourceNotFoundError for unknown IDs."""
    repository = CustomerRepository(seeded_session)

    with pytest.raises(ResourceNotFoundError) as exc_info:
        repository.get_by_id("C999")

    assert exc_info.value.code == "CUSTOMER_NOT_FOUND"
    assert "C999" in exc_info.value.message


def test_active_offer_filtering(seeded_session: Session) -> None:
    """OfferRepository list_active_offers returns only active offers."""
    repository = OfferRepository(seeded_session)

    active = repository.list_active_offers()
    all_offers = repository.list_all_offers()

    assert active.total == 1
    assert active.items[0].offer_id == "OFFER-ACTIVE"
    assert all_offers.total == 2


def test_offer_missing_resource_error(seeded_session: Session) -> None:
    """OfferRepository raises ResourceNotFoundError for unknown offers."""
    repository = OfferRepository(seeded_session)

    with pytest.raises(ResourceNotFoundError) as exc_info:
        repository.get_by_id("OFFER-MISSING")

    assert exc_info.value.code == "OFFER_NOT_FOUND"


def test_latest_customer_recommendation(seeded_session: Session) -> None:
    """RecommendationRepository returns the newest recommendation for a customer."""
    repository = RecommendationRepository(seeded_session)

    latest = repository.get_latest_by_customer("C001")
    listing = repository.list_by_customer("C001")

    assert latest.summary == "Latest retention recommendation"
    assert listing.total == 2
    assert listing.items[0].recommendation_id == latest.recommendation_id


def test_list_recommendations_with_filters(seeded_session: Session) -> None:
    """RecommendationRepository filters by status and decision."""
    repository = RecommendationRepository(seeded_session)

    by_status = repository.list_recommendations(status=RecommendationStatus.NEW)
    by_decision = repository.list_recommendations(decision=RecommendationDecision.MONITOR)

    assert by_status.total == 1
    assert by_decision.total == 1


def test_recommendation_missing_resource_errors(seeded_session: Session) -> None:
    """RecommendationRepository raises when records are missing."""
    repository = RecommendationRepository(seeded_session)

    with pytest.raises(ResourceNotFoundError):
        repository.get_by_id("missing-id")

    with pytest.raises(ResourceNotFoundError) as exc_info:
        repository.get_latest_by_customer("C999")

    assert exc_info.value.code == "RECOMMENDATION_NOT_FOUND"


def test_unacknowledged_alerts(seeded_session: Session) -> None:
    """AlertRepository list_unacknowledged excludes acknowledged alerts."""
    repository = AlertRepository(seeded_session)

    unacknowledged = repository.list_unacknowledged()
    all_alerts = repository.list_alerts()

    assert unacknowledged.total == 1
    assert unacknowledged.items[0].acknowledged is False
    assert all_alerts.total == 2


def test_alert_missing_resource_error(seeded_session: Session) -> None:
    """AlertRepository raises ResourceNotFoundError for unknown alerts."""
    repository = AlertRepository(seeded_session)

    with pytest.raises(ResourceNotFoundError) as exc_info:
        repository.get_by_id("missing-alert")

    assert exc_info.value.code == "ALERT_NOT_FOUND"


def test_customer_event_listing(seeded_session: Session) -> None:
    """EventRepository lists events globally and by customer."""
    repository = EventRepository(seeded_session)

    all_events = repository.list_events()
    customer_events = repository.list_by_customer("C001")

    assert all_events.total == 2
    assert customer_events.total == 2
    assert all(event.customer_id == "C001" for event in customer_events.items)


def test_event_missing_resource_error(seeded_session: Session) -> None:
    """EventRepository raises ResourceNotFoundError for unknown events."""
    repository = EventRepository(seeded_session)

    with pytest.raises(ResourceNotFoundError) as exc_info:
        repository.get_by_id("missing-event")

    assert exc_info.value.code == "EVENT_NOT_FOUND"


def test_customer_interaction_listing(seeded_session: Session) -> None:
    """InteractionRepository lists interactions for a customer."""
    repository = InteractionRepository(seeded_session)

    interactions = repository.list_by_customer("C001")

    assert interactions.total == 2
    assert interactions.items[0].customer_id == "C001"


def test_invalid_pagination_in_repository(seeded_session: Session) -> None:
    """Repositories reject invalid pagination parameters."""
    repository = CustomerRepository(seeded_session)

    with pytest.raises(InvalidPaginationError):
        repository.list_customers(page=0, page_size=10)


def test_recommendation_repository_orders_latest_first(seeded_session: Session) -> None:
    """RecommendationRepository inserts an extra older record after seed data."""
    older = Recommendation(
        customer_id="C002",
        churn_score=40.0,
        value_score=30.0,
        priority_score=35.0,
        decision=RecommendationDecision.NO_ACTION,
        revenue_at_risk=500.0,
        expected_net_benefit=100.0,
        confidence=0.55,
        summary="Older C002 recommendation",
        status=RecommendationStatus.CLOSED,
        created_at=datetime(2025, 12, 1, tzinfo=UTC),
        updated_at=datetime(2025, 12, 1, tzinfo=UTC),
    )
    newer = Recommendation(
        customer_id="C002",
        churn_score=55.0,
        value_score=45.0,
        priority_score=50.0,
        decision=RecommendationDecision.REVIEW,
        revenue_at_risk=900.0,
        expected_net_benefit=250.0,
        confidence=0.68,
        summary="Newer C002 recommendation",
        status=RecommendationStatus.NEW,
        created_at=datetime(2026, 3, 1, tzinfo=UTC),
        updated_at=datetime(2026, 3, 1, tzinfo=UTC),
    )
    seeded_session.add(older)
    seeded_session.add(newer)
    seeded_session.commit()

    repository = RecommendationRepository(seeded_session)
    latest = repository.get_latest_by_customer("C002")

    assert latest.summary == "Newer C002 recommendation"
