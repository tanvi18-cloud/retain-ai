"""Customer API endpoint tests."""

from fastapi.testclient import TestClient

from app.models.enums import CustomerSegment


def test_list_customers_returns_ten_seeded_customers(seeded_client: TestClient) -> None:
    """GET /api/v1/customers returns all 10 seeded customers."""
    response = seeded_client.get("/api/v1/customers", params={"page_size": 100})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 10
    assert len(payload["items"]) == 10


def test_customer_list_pagination(seeded_client: TestClient) -> None:
    """Customer list supports pagination."""
    response = seeded_client.get("/api/v1/customers", params={"page": 1, "page_size": 4})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 10
    assert payload["page"] == 1
    assert payload["page_size"] == 4
    assert len(payload["items"]) == 4
    assert payload["pages"] == 3


def test_customer_search_by_id(seeded_client: TestClient) -> None:
    """Customer search matches customer ID."""
    response = seeded_client.get("/api/v1/customers", params={"search": "C003"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["customer_id"] == "C003"


def test_customer_search_by_full_name(seeded_client: TestClient) -> None:
    """Customer search matches full name."""
    response = seeded_client.get("/api/v1/customers", params={"search": "Ananya"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["full_name"] == "Ananya Deshmukh"


def test_customer_segment_filter(seeded_client: TestClient) -> None:
    """Customer list filters by segment."""
    response = seeded_client.get(
        "/api/v1/customers",
        params={"segment": CustomerSegment.PRIORITY.value, "page_size": 100},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert all(item["segment"] == CustomerSegment.PRIORITY.value for item in payload["items"])


def test_customer_sort_descending_by_value(seeded_client: TestClient) -> None:
    """Customer list supports descending sort by estimated annual value."""
    response = seeded_client.get(
        "/api/v1/customers",
        params={
            "sort_by": "estimated_annual_value",
            "sort_order": "desc",
            "page_size": 100,
        },
    )

    assert response.status_code == 200
    values = [item["estimated_annual_value"] for item in response.json()["items"]]
    assert values == sorted(values, reverse=True)


def test_customer_sort_ascending_by_name(seeded_client: TestClient) -> None:
    """Customer list supports ascending sort by full name."""
    response = seeded_client.get(
        "/api/v1/customers",
        params={"sort_by": "full_name", "sort_order": "asc", "page_size": 100},
    )

    assert response.status_code == 200
    names = [item["full_name"] for item in response.json()["items"]]
    assert names == sorted(names)


def test_get_customer_detail(seeded_client: TestClient) -> None:
    """GET /api/v1/customers/{customer_id} returns customer detail."""
    response = seeded_client.get("/api/v1/customers/C001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["customer_id"] == "C001"
    assert payload["full_name"] == "Ananya Deshmukh"
    assert payload["segment"] == CustomerSegment.PRIORITY.value


def test_get_customer_360_c001(seeded_client: TestClient) -> None:
    """GET /api/v1/customers/{customer_id}/360 returns Customer 360 payload."""
    response = seeded_client.get("/api/v1/customers/C001/360")

    assert response.status_code == 200
    payload = response.json()
    assert payload["customer"]["customer_id"] == "C001"
    assert payload["accounts"]
    assert payload["credit_profile"] is not None
    assert payload["transaction_features"] is not None
    assert "data_freshness" in payload
    assert isinstance(payload["data_warnings"], list)


def test_customer_360_c001_home_loan_trigger(seeded_client: TestClient) -> None:
    """C001 Customer 360 includes a home-loan bureau trigger."""
    response = seeded_client.get("/api/v1/customers/C001/360")
    triggers = response.json()["bureau_triggers"]

    assert any(
        trigger["product_type"] == "HOME_LOAN" and trigger["severity"] in {"HIGH", "CRITICAL"}
        for trigger in triggers
    )


def test_customer_360_c004_dpd(seeded_client: TestClient) -> None:
    """C004 Customer 360 includes 60 DPD."""
    response = seeded_client.get("/api/v1/customers/C004/360")

    assert response.json()["credit_profile"]["max_dpd_12m"] == 60


def test_customer_360_c008_fd_maturity(seeded_client: TestClient) -> None:
    """C008 Customer 360 includes fixed-deposit maturity."""
    response = seeded_client.get("/api/v1/customers/C008/360")
    accounts = response.json()["accounts"]

    assert any(account["fixed_deposit_maturity_date"] is not None for account in accounts)


def test_customer_360_c010_no_bureau_triggers(seeded_client: TestClient) -> None:
    """C010 Customer 360 has no bureau triggers."""
    response = seeded_client.get("/api/v1/customers/C010/360")
    payload = response.json()

    assert payload["bureau_triggers"] == []
    assert "no recent bureau trigger" in payload["data_warnings"]


def test_missing_customer_returns_404(seeded_client: TestClient) -> None:
    """Missing customers return the standard error envelope."""
    detail_response = seeded_client.get("/api/v1/customers/C999")
    view360_response = seeded_client.get("/api/v1/customers/C999/360")

    assert detail_response.status_code == 404
    assert detail_response.json()["error"]["code"] == "CUSTOMER_NOT_FOUND"
    assert view360_response.status_code == 404
    assert view360_response.json()["error"]["code"] == "CUSTOMER_NOT_FOUND"
