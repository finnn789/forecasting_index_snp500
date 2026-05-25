"""
app/api/v1/routes_sentiment.py — Endpoint sentiment pipeline.
"""

import asyncio
import json
import threading

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.base import PaginatedResponse, SuccessResponse
from app.schemas.sentiment import ModelStatusResponse, PipelineStatusResponse, PreviewResponse
from app.services import sentiment_service

router = APIRouter(tags=["Sentiment Pipeline"])


@router.post(
    "/sentiment/pipeline/run",
    summary="Jalankan sentiment pipeline (Server-Sent Events)",
    response_description="Stream SSE: step, pct, msg — diakhiri event 'done' atau 'error'",
)
async def run_pipeline(
    start_date: str | None = None,
    end_date: str | None = None,
    batch_size: int = 32,
) -> StreamingResponse:
    """
    Menjalankan sentiment pipeline dan meneruskan progress secara real-time
    via Server-Sent Events (text/event-stream).

    Setiap event adalah JSON satu baris dengan format:
    ```
    data: {"step": "...", "pct": 0-100, "msg": "..."}
    ```

    Step yang mungkin: `loading_data` → `filtering` → `loading_model` →
    `model_ready` → `inference` → `aggregating` → `saving` → `done` | `error`

    Event `done` menyertakan field `result` berisi output lengkap pipeline.
    """
    async def event_stream():
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def emit(event: dict) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, event)

        def worker() -> None:
            sentiment_service.run_preprocessing_pipeline_stream(
                start_date=start_date,
                end_date=end_date,
                batch_size=batch_size,
                emit=emit,
            )
            loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel — stream selesai

        threading.Thread(target=worker, daemon=True).start()

        while True:
            event = await queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # nonaktifkan buffering Nginx jika ada
        },
    )


@router.get("/sentiment/pipeline/status", response_model=SuccessResponse[PipelineStatusResponse])
def pipeline_status() -> SuccessResponse[PipelineStatusResponse]:
    data = sentiment_service.get_pipeline_status()
    return SuccessResponse[PipelineStatusResponse](data=data, message="Status pipeline sentimen berhasil dimuat")


@router.get("/sentiment/data/preview", response_model=SuccessResponse[PreviewResponse])
def data_preview(page: int = 1, page_size: int = 20) -> SuccessResponse[PreviewResponse]:
    result = sentiment_service.get_daily_preview(page=page, page_size=page_size)
    data = PreviewResponse(
        source="sentiment",
        filename="headlines_daily_sentiment.csv",
        **result,
    )
    return SuccessResponse[PreviewResponse](data=data, message="Preview data sentimen berhasil dimuat")


@router.get("/sentiment/model/status", response_model=SuccessResponse[ModelStatusResponse])
def model_status() -> SuccessResponse[ModelStatusResponse]:
    data = sentiment_service.get_model_status()
    return SuccessResponse[ModelStatusResponse](data=data, message="Status model FinBERT berhasil dimuat")
