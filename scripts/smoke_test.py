#!/usr/bin/env python3
"""HTTP smoke test for a running RetainAI backend (local or Docker)."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

SECRET_MARKERS = (
    "QWEN_API_KEY",
    "SMTP_PASSWORD",
    "super-secret",
    "sqlite:///",
    "Traceback (most recent call last)",
    "chain-of-thought",
    "hidden prompt",
)


@dataclass
class StepResult:
    name: str
    passed: bool
    detail: str
    duration_ms: float


def _request(
    method: str,
    url: str,
    *,
    body: dict | None = None,
    timeout: float = 30.0,
) -> tuple[int, str]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, response.read().decode("utf-8")


def _assert_no_secrets(text: str) -> None:
    lowered = text.lower()
    for marker in SECRET_MARKERS:
        if marker.lower() in lowered:
            raise AssertionError(f"forbidden marker found: {marker}")


def _run_step(name: str, fn) -> StepResult:
    start = time.perf_counter()
    try:
        detail = fn()
        elapsed = (time.perf_counter() - start) * 1000
        return StepResult(name=name, passed=True, detail=detail, duration_ms=elapsed)
    except Exception as exc:  # noqa: BLE001 - smoke test reports all failures
        elapsed = (time.perf_counter() - start) * 1000
        return StepResult(name=name, passed=False, detail=str(exc), duration_ms=elapsed)


def main() -> int:
    parser = argparse.ArgumentParser(description="RetainAI backend smoke test")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8001",
        help="Backend base URL without trailing slash",
    )
    parser.add_argument(
        "--poll-timeout",
        type=float,
        default=30.0,
        help="Seconds to wait for event completion",
    )
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    api = f"{base}/api/v1"
    results: list[StepResult] = []
    event_id: str | None = None
    execution_id: str | None = None

    def health() -> str:
        status, text = _request("GET", f"{base}/health")
        _assert_no_secrets(text)
        assert status == 200
        return "ok"

    def customers() -> str:
        status, text = _request("GET", f"{api}/customers?page_size=20")
        _assert_no_secrets(text)
        payload = json.loads(text)
        assert payload["total"] == 10
        return f"total={payload['total']}"

    def portfolio() -> str:
        status, text = _request("GET", f"{api}/portfolio/summary")
        _assert_no_secrets(text)
        assert status == 200
        payload = json.loads(text)
        return f"customers={payload['total_customers']}"

    def customer_360() -> str:
        status, text = _request("GET", f"{api}/customers/C001/360")
        _assert_no_secrets(text)
        assert status == 200
        return "C001 loaded"

    def rules_only() -> str:
        status, text = _request("POST", f"{api}/analysis/C001/rules-only")
        _assert_no_secrets(text)
        assert status == 200
        payload = json.loads(text)
        return f"decision={payload['priority_result']['decision']}"

    def create_event() -> str:
        nonlocal event_id
        status, text = _request(
            "POST",
            f"{api}/events",
            body={
                "customer_id": "C001",
                "event_type": "MANUAL_REANALYSIS",
                "source_system": "CRM",
                "payload": {"reason": "smoke test"},
                "notifications_enabled": False,
            },
        )
        _assert_no_secrets(text)
        assert status == 202
        payload = json.loads(text)
        event_id = payload["event_id"]
        return f"event_id={event_id}"

    def event_complete() -> str:
        assert event_id is not None
        deadline = time.monotonic() + args.poll_timeout
        last_status = "UNKNOWN"
        while time.monotonic() < deadline:
            status, text = _request("GET", f"{api}/events/{event_id}")
            _assert_no_secrets(text)
            payload = json.loads(text)
            last_status = payload["status"]
            if last_status in {"COMPLETED", "FAILED"}:
                break
            time.sleep(0.2)
        assert last_status == "COMPLETED", f"event status={last_status}"
        return last_status

    def recommendation_created() -> str:
        assert event_id is not None
        status, text = _request("GET", f"{api}/events/{event_id}")
        payload = json.loads(text)
        rec_id = (payload.get("analysis_result_json") or {}).get("recommendation_id")
        assert rec_id, "recommendation_id missing from event snapshot"
        return f"recommendation_id={rec_id}"

    def alerts() -> str:
        status, text = _request("GET", f"{api}/alerts?page_size=5")
        _assert_no_secrets(text)
        assert status == 200
        payload = json.loads(text)
        return f"total={payload['total']}"

    def chat() -> str:
        status, text = _request(
            "POST",
            f"{api}/chat",
            body={
                "message": "Why is C001 urgent?",
                "rm_id": "RM-01",
                "customer_id": "C001",
            },
        )
        _assert_no_secrets(text)
        assert status == 200
        payload = json.loads(text)
        assert "C001" in payload["answer"]
        assert payload.get("evidence")
        return f"intent={payload.get('intent')}"

    def system_status() -> str:
        status, text = _request("GET", f"{api}/system/llm-status")
        _assert_no_secrets(text)
        assert status == 200
        payload = json.loads(text)
        return f"mode={payload.get('mode')}"

    def secrets_scan() -> str:
        endpoints = [
            f"{base}/health",
            f"{api}/health",
            f"{api}/system/llm-status",
            f"{api}/system/notification-status",
            f"{api}/portfolio/summary",
        ]
        for endpoint in endpoints:
            _, text = _request("GET", endpoint)
            _assert_no_secrets(text)
        return f"scanned {len(endpoints)} endpoints"

    steps = [
        ("Health endpoint", health),
        ("Customer list (10 customers)", customers),
        ("Portfolio summary", portfolio),
        ("Customer 360 (C001)", customer_360),
        ("Rules-only analysis (C001)", rules_only),
        ("Event creation (202)", create_event),
        ("Event completion", event_complete),
        ("Recommendation created", recommendation_created),
        ("Alerts endpoint", alerts),
        ("RM chat (mock mode)", chat),
        ("System status", system_status),
        ("No secrets in responses", secrets_scan),
    ]

    print(f"RetainAI smoke test — base URL: {base}\n")
    total_start = time.perf_counter()

    for name, fn in steps:
        result = _run_step(name, fn)
        results.append(result)
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name} ({result.duration_ms:.0f} ms) — {result.detail}")

    total_ms = (time.perf_counter() - total_start) * 1000
    failed = [r for r in results if not r.passed]
    print(f"\nTotal duration: {total_ms:.0f} ms")
    print(f"Result: {'PASS' if not failed else 'FAIL'} ({len(results) - len(failed)}/{len(results)})")

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
