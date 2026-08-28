"""Production request-size controls that do not trust Content-Length."""

import json

from starlette.types import Message, Receive, Scope, Send

from saudi_business_launch_navigator.api.middleware import RequestContextMiddleware


def _scope() -> Scope:
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/v1/checklist",
        "raw_path": b"/api/v1/checklist",
        "query_string": b"",
        "root_path": "",
        "headers": [(b"content-type", b"application/json")],
        "client": ("127.0.0.1", 1234),
        "server": ("testserver", 80),
        "state": {},
    }


def _receive(messages: list[Message]) -> Receive:
    remaining = iter(messages)

    async def receive() -> Message:
        return next(remaining, {"type": "http.disconnect"})

    return receive


async def test_streamed_body_without_content_length_is_rejected() -> None:
    downstream_called = False

    async def downstream(scope: Scope, receive: Receive, send: Send) -> None:
        nonlocal downstream_called
        downstream_called = True

    sent: list[Message] = []

    async def send(message: Message) -> None:
        sent.append(message)

    middleware = RequestContextMiddleware(downstream, maximum_request_bytes=1024)
    await middleware(
        _scope(),
        _receive(
            [
                {"type": "http.request", "body": b"a" * 600, "more_body": True},
                {"type": "http.request", "body": b"b" * 600, "more_body": False},
            ]
        ),
        send,
    )

    assert downstream_called is False
    assert sent[0]["type"] == "http.response.start"
    assert sent[0]["status"] == 413
    payload = json.loads(sent[1]["body"])
    assert payload["error"]["code"] == "REQUEST_TOO_LARGE"
    assert payload["error"]["request_id"]


async def test_streamed_body_below_limit_is_replayed_exactly() -> None:
    observed = bytearray()

    async def downstream(scope: Scope, receive: Receive, send: Send) -> None:
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                break
            observed.extend(message.get("body", b""))
            if not message.get("more_body", False):
                break
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    sent: list[Message] = []

    async def send(message: Message) -> None:
        sent.append(message)

    middleware = RequestContextMiddleware(downstream, maximum_request_bytes=1024)
    await middleware(
        _scope(),
        _receive(
            [
                {"type": "http.request", "body": b"first", "more_body": True},
                {"type": "http.request", "body": b"-second", "more_body": False},
            ]
        ),
        send,
    )

    assert bytes(observed) == b"first-second"
    assert sent[0]["status"] == 204
    response_headers = dict(sent[0]["headers"])
    assert response_headers[b"x-content-type-options"] == b"nosniff"
    assert response_headers[b"x-request-id"]
