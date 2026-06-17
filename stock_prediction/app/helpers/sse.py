"""Server-Sent Events (SSE) streaming helpers for async/blocking worker coordination."""

from __future__ import annotations

import asyncio
import json
import threading
from collections.abc import Callable

from fastapi.responses import StreamingResponse


def sse_response(work: Callable[[Callable[[dict], None]], None]) -> StreamingResponse:
    """
    Wrap a blocking worker function to stream its progress as Server-Sent Events.

    Args:
        work: A callable that accepts an `emit(event: dict)` callback.
              The function runs blocking operations and calls emit() for each progress event.

    Returns:
        A StreamingResponse configured for text/event-stream with proper SSE headers.
    """

    async def event_stream():
        """Async generator that converts queue events to SSE format."""
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def emit(event: dict) -> None:
            """Thread-safe callback to put events into the async queue."""
            loop.call_soon_threadsafe(queue.put_nowait, event)

        def worker() -> None:
            """Run the blocking work and signal completion with sentinel."""
            work(emit)
            loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

        threading.Thread(target=worker, daemon=True).start()

        while True:
            event = await queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
