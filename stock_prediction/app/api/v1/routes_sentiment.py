"""
app/api/v1/routes_sentiment.py — Endpoint sentiment pipeline.
"""

from collections.abc import Callable

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.envelope import EnvelopeRoute
from app.helpers.sse import sse_response
from app.schemas.sentiment import ModelStatusResponse, PipelineStatusResponse, PreviewResponse
from app.services import sentiment_service

router = APIRouter(tags=["Sentiment Pipeline"], route_class=EnvelopeRoute)


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
    def work(emit: Callable[[dict], None]) -> None:
        sentiment_service.run_preprocessing_pipeline_stream(
            start_date=start_date, end_date=end_date, batch_size=batch_size, emit=emit)
    return sse_response(work)


@router.get(
    "/sentiment/pipeline/status",
    response_model=PipelineStatusResponse,
    openapi_extra={"x-message": "Status pipeline sentimen berhasil dimuat"},
)
def pipeline_status() -> PipelineStatusResponse:
    return sentiment_service.get_pipeline_status()


@router.get(
    "/sentiment/data/preview",
    response_model=PreviewResponse,
    openapi_extra={"x-message": "Preview data sentimen berhasil dimuat"},
)
def data_preview(page: int = 1, page_size: int = 20) -> PreviewResponse:
    """
    Preview berpaginasi khusus output pipeline sentimen
    (`headlines_daily_sentiment.csv`).

    Berbeda dengan `/feature-engineering/preview` yang generic untuk file
    apa saja di data/processed/ (param `source`+`file`, N baris pertama tanpa
    paginasi) — endpoint ini spesifik untuk hasil sentiment pipeline dan
    mendukung `page`/`page_size`.
    """
    return sentiment_service.get_daily_preview(page=page, page_size=page_size)


@router.get(
    "/sentiment/model/status",
    response_model=ModelStatusResponse,
    openapi_extra={"x-message": "Status model FinBERT berhasil dimuat"},
)
def model_status() -> ModelStatusResponse:
    return sentiment_service.get_model_status()
