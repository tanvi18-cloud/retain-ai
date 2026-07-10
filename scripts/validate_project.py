#!/usr/bin/env python3
"""Validate RetainAI deterministic business outcomes without a live LLM."""

from __future__ import annotations

from validation_common import (
    analyze_customer_flow,
    bootstrap_backend_path,
    print_validation_table,
    reset_and_seed,
    row_from_recommendation,
    validate_customer_outcome,
    validation_settings,
)


def main() -> int:
    """Reset seed data, analyze demo customers, and verify expected outcomes."""
    settings = validation_settings()
    summary = reset_and_seed(settings)

    bootstrap_backend_path()
    from sqlmodel import Session, select

    from app.core.database import configure_engine, get_engine
    from app.models.customer import Customer
    from app.models.offer import Offer
    from app.seed.seed_database import EXPECTED_CUSTOMER_IDS, EXPECTED_OFFER_IDS

    configure_engine(settings.database_url)
    failures: list[str] = []
    rows = []

    with Session(get_engine()) as session:
        customer_count = len(session.exec(select(Customer)).all())
        offer_count = len(session.exec(select(Offer)).all())
        if customer_count != 10:
            failures.append(f"expected 10 customers, found {customer_count}")
        if offer_count != 8:
            failures.append(f"expected 8 offers, found {offer_count}")
        seeded_ids = {customer.customer_id for customer in session.exec(select(Customer)).all()}
        if set(EXPECTED_CUSTOMER_IDS) != seeded_ids:
            failures.append("customer IDs do not match expected catalog")
        offer_ids = {offer.offer_id for offer in session.exec(select(Offer)).all()}
        if set(EXPECTED_OFFER_IDS) != offer_ids:
            failures.append("offer IDs do not match expected catalog")

        print(f"Seed summary: customers={summary.customers_inserted}, offers={summary.offers_inserted}")
        print(f"MOCK_LLM_MODE={settings.mock_llm_mode}")

        for customer_id in ("C001", "C004", "C008", "C010"):
            _flow, recommendation = analyze_customer_flow(session, settings, customer_id)
            fields = row_from_recommendation(customer_id, recommendation)
            row = validate_customer_outcome(customer_id, **fields)
            rows.append(row)
            if row.validation_status == "FAIL":
                failures.extend(row.details)

    print_validation_table(rows)

    if failures:
        print("\nValidation FAILED:", file=sys.stderr)
        for item in failures:
            print(f"  - {item}", file=sys.stderr)
        return 1

    print("\nValidation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
