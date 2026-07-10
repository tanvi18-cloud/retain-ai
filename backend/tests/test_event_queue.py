"""Async event queue tests."""

import asyncio

import pytest

from app.core.config import Settings
from app.services.event_processor import create_async_processor
from app.services.event_queue import SENTINEL, EventQueue


@pytest.fixture
def queue_settings() -> Settings:
    return Settings(
        app_name="RetainAI",
        app_env="development",
        queue_worker_count=1,
        event_shutdown_timeout_seconds=2,
    )


@pytest.mark.asyncio
async def test_queue_created_once(queue_settings: Settings):
    queue = EventQueue(queue_settings)
    assert queue.metrics.worker_count == 1
    assert queue.queue_size == 0


@pytest.mark.asyncio
async def test_worker_processes_event(queue_settings: Settings):
    processed: list[str] = []

    def fake_processor():
        async def process(event_id: str) -> None:
            processed.append(event_id)

        return process

    queue = EventQueue(queue_settings)
    queue.set_processor_factory(fake_processor)
    await queue.start_workers()
    await queue.enqueue("event-1")
    await asyncio.sleep(0.2)
    await queue.shutdown()
    assert "event-1" in processed


@pytest.mark.asyncio
async def test_graceful_shutdown(queue_settings: Settings):
    queue = EventQueue(queue_settings)
    queue.set_processor_factory(lambda: create_async_processor(queue_settings))
    await queue.start_workers()
    await queue.shutdown()
    assert queue._workers == []


@pytest.mark.asyncio
async def test_worker_error_does_not_crash_queue(queue_settings: Settings):
    calls = {"count": 0}

    def failing_processor():
        async def process(_event_id: str) -> None:
            calls["count"] += 1
            if calls["count"] == 1:
                raise RuntimeError("boom")

        return process

    queue = EventQueue(queue_settings)
    queue.set_processor_factory(failing_processor)
    await queue.start_workers()
    await queue.enqueue("event-1")
    await queue.enqueue("event-2")
    await asyncio.sleep(0.3)
    await queue.shutdown()
    assert calls["count"] >= 1


@pytest.mark.asyncio
async def test_sentinel_stops_worker(queue_settings: Settings):
    queue = EventQueue(queue_settings)
    queue.set_processor_factory(lambda: create_async_processor(queue_settings))
    await queue.start_workers()
    await queue._queue.put(SENTINEL)
    await asyncio.sleep(0.1)
    await queue.shutdown()
