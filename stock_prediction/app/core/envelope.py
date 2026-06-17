"""
app/core/envelope.py — Auto-envelope untuk response API.

EnvelopeRoute membungkus return value handler ke SuccessResponse secara
otomatis, sehingga handler cukup `return <pydantic model / dict mentah>`.
Pesan opsional didefinisikan deklaratif via openapi_extra={"x-message": "..."}.
Streaming/SSE dan response non-JSON dilewati apa adanya (tidak dibungkus).
"""

from __future__ import annotations

import json
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.routing import APIRoute

from app.schemas.base import SuccessResponse


class EnvelopeRoute(APIRoute):
    """APIRoute yang otomatis membungkus response ke SuccessResponse."""

    def get_route_handler(self) -> Callable:
        original_handler = super().get_route_handler()
        message: str = (self.openapi_extra or {}).get("x-message", "")

        async def custom_handler(request: Request) -> Response:
            response = await original_handler(request)

            # Lewati SSE / streaming — jangan dibungkus.
            if isinstance(response, StreamingResponse):
                return response

            # Lewati response non-JSON (mis. file, plain text).
            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                return response

            # body sudah hasil serialisasi response_model (inner). Bungkus.
            payload = json.loads(response.body)
            envelope = SuccessResponse(data=payload, message=message)
            return JSONResponse(
                content=jsonable_encoder(envelope),
                status_code=response.status_code,
            )

        return custom_handler
