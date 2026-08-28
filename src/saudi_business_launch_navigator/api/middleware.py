"""Request IDs, bounded bodies, safe logging, and response hardening."""

from __future__ import annotations

import logging
import re
from time import perf_counter
from uuid import uuid4

from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_BODY_METHODS = {"POST", "PUT", "PATCH"}
_SAFE_RESPONSE_HEADERS = (
    (b"x-content-type-options", b"nosniff"),
    (b"referrer-policy", b"no-referrer"),
    (b"cache-control", b"no-store"),
    (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
)
_HARDENED_HEADER_NAMES = {
    b"x-request-id",
    *(key for key, _ in _SAFE_RESPONSE_HEADERS),
}


class RequestContextMiddleware:
    """Apply one fail-closed HTTP boundary without buffering unbounded bodies."""

    def __init__(self, app: ASGIApp, *, maximum_request_bytes: int) -> None:
        self._app = app
        self._maximum_request_bytes = maximum_request_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        request_headers = {key.lower(): value for key, value in scope.get("headers", [])}
        supplied = request_headers.get(b"x-request-id", b"").decode("ascii", errors="ignore")
        request_id = supplied if _SAFE_REQUEST_ID.fullmatch(supplied) else uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id
        started = perf_counter()

        content_length = request_headers.get(b"content-length")
        if content_length is not None and self._request_is_too_large(content_length):
            await self._send_oversized(scope, receive, send, request_id)
            return

        bounded_receive = receive
        if scope.get("method") in _BODY_METHODS:
            messages = await self._read_bounded(receive)
            if messages is None:
                await self._send_oversized(scope, receive, send, request_id)
                return
            bounded_receive = _replay_receive(messages)

        status_code = 500

        async def hardened_send(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                message = dict(message)
                existing = [
                    (key, value)
                    for key, value in message.get("headers", [])
                    if key.lower() not in _HARDENED_HEADER_NAMES
                ]
                message["headers"] = [
                    *existing,
                    (b"x-request-id", request_id.encode("ascii")),
                    *_SAFE_RESPONSE_HEADERS,
                ]
            await send(message)

        await self._app(scope, bounded_receive, hardened_send)
        duration_ms = round((perf_counter() - started) * 1000, 2)
        logger.info(
            "API request completed",
            extra={
                "event": "api_request_completed",
                "component": "api",
                "request_id": request_id,
                "http_method": scope.get("method", "UNKNOWN"),
                "http_path": scope.get("path", ""),
                "status_code": status_code,
                "duration_ms": duration_ms,
            },
        )

    async def _read_bounded(self, receive: Receive) -> list[Message] | None:
        messages: list[Message] = []
        received_bytes = 0
        while True:
            message = await receive()
            messages.append(message)
            if message["type"] == "http.disconnect":
                return messages
            received_bytes += len(message.get("body", b""))
            if received_bytes > self._maximum_request_bytes:
                return None
            if not message.get("more_body", False):
                return messages

    def _request_is_too_large(self, value: bytes) -> bool:
        try:
            return int(value) > self._maximum_request_bytes
        except ValueError:
            return True

    @staticmethod
    async def _send_oversized(
        scope: Scope,
        receive: Receive,
        send: Send,
        request_id: str,
    ) -> None:
        response = JSONResponse(
            status_code=413,
            content={
                "error": {
                    "code": "REQUEST_TOO_LARGE",
                    "message": "The request body exceeds the configured size limit.",
                    "details": [],
                    "request_id": request_id,
                }
            },
            headers={
                "X-Request-ID": request_id,
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
                "Cache-Control": "no-store",
                "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            },
        )
        await response(scope, receive, send)


def _replay_receive(messages: list[Message]) -> Receive:
    remaining = iter(messages)

    async def receive() -> Message:
        return next(remaining, {"type": "http.disconnect"})

    return receive


__all__ = ["RequestContextMiddleware"]
