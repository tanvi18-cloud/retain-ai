"""Application-scoped asyncio event queue for MVP async processing.

Note: asyncio.Queue is non-durable. Events remaining in the queue are lost if
the process stops. This is intentional for the MVP only.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.core.logging import get_logger

if TYPE_CHECKING:
    from app.core.config import Settings

logger = get_logger(__name__)

SENTINEL: object = object()


@dataclass
class QueueMetrics:
    """Runtime metrics for the in-memory event queue."""

    worker_count: int
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    processing_count: int = 0
    completed_count_since_startup: int = 0
    failed_count_since_startup: int = 0
    _processing_ids: set[str] = field(default_factory=set)

    @property
    def processing_event_ids(self) -> set[str]:
        return self._processing_ids

    def mark_processing(self, event_id: str) -> bool:
        """Track an event as in-flight; return False if already processing."""
        if event_id in self._processing_ids:
            return False
        self._processing_ids.add(event_id)
        self.processing_count = len(self._processing_ids)
        return True

    def mark_done(self, event_id: str, *, failed: bool = False) -> None:
        """Clear in-flight tracking and update counters."""
        self._processing_ids.discard(event_id)
        self.processing_count = len(self._processing_ids)
        if failed:
            self.failed_count_since_startup += 1
        else:
            self.completed_count_since_startup += 1


class EventQueue:
    """In-memory asyncio queue with worker lifecycle management."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._queue: asyncio.Queue[str | object] = asyncio.Queue()
        self.metrics = QueueMetrics(worker_count=settings.queue_worker_count)
        self._workers: list[asyncio.Task[None]] = []
        self._processor_factory = None

    @property
    def queue_size(self) -> int:
        return self._queue.qsize()

    def set_processor_factory(self, factory) -> None:
        """Register a callable that returns an async process function."""
        self._processor_factory = factory

    async def enqueue(self, event_id: str) -> None:
        """Add an event ID to the processing queue."""
        await self._queue.put(event_id)

    async def start_workers(self) -> None:
        """Start configured background worker tasks."""
        if self._processor_factory is None:
            msg = "Processor factory must be set before starting workers"
            raise RuntimeError(msg)
        for index in range(self.settings.queue_worker_count):
            task = asyncio.create_task(self._worker_loop(index), name=f"event-worker-{index}")
            self._workers.append(task)
        logger.info(
            "event_workers_started",
            worker_count=self.settings.queue_worker_count,
        )

    async def shutdown(self) -> None:
        """Gracefully stop workers and drain in-flight tasks."""
        for _ in self._workers:
            await self._queue.put(SENTINEL)
        if self._workers:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._workers, return_exceptions=True),
                    timeout=self.settings.event_shutdown_timeout_seconds,
                )
            except TimeoutError:
                for task in self._workers:
                    task.cancel()
                await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info("event_workers_stopped")

    async def _worker_loop(self, worker_index: int) -> None:
        """Process queued event IDs until a shutdown sentinel is received."""
        logger.info("event_worker_started", worker_index=worker_index)
        process_event = self._processor_factory()
        while True:
            item = await self._queue.get()
            try:
                if item is SENTINEL:
                    break
                event_id = str(item)
                if not self.metrics.mark_processing(event_id):
                    logger.warning("event_already_processing", event_id=event_id)
                    continue
                try:
                    await process_event(event_id)
                    self.metrics.mark_done(event_id, failed=False)
                except Exception:
                    logger.exception("event_worker_processing_error", event_id=event_id)
                    self.metrics.mark_done(event_id, failed=True)
            finally:
                self._queue.task_done()
        logger.info("event_worker_stopped", worker_index=worker_index)

    def status(self) -> dict:
        """Return queue status for system API."""
        return {
            "worker_count": self.metrics.worker_count,
            "queue_size": self.queue_size,
            "processing_count": self.metrics.processing_count,
            "completed_count_since_startup": self.metrics.completed_count_since_startup,
            "failed_count_since_startup": self.metrics.failed_count_since_startup,
            "started_at": self.metrics.started_at,
        }
