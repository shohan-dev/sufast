"""Framework-level pytest coverage across core modules."""

import asyncio
import gzip

from sufast import APIRouter, HTTPException, Request, Response, Sufast
from sufast.compression import CompressionMiddleware
from sufast.logging import LogLevel, Logger, get_logger
from sufast.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from sufast.security import (
    APIKeyManager,
    CSRFProtection,
    JWTAuth,
    SecurityScanner,
    hash_password,
    sign_value,
    verify_password,
    verify_signed_value,
)
from sufast.sessions import InMemorySessionStore
from sufast.sse import EventSource, SSEEvent
from sufast.testclient import TestClient
from sufast.uploads import UploadFile


def test_http_routes_and_docs_work():
    app = Sufast(
        title="Test API",
        version="1.0.0",
        debug=True,
        secret_key="test-secret-key-at-least-32-chars!!",
    )

    @app.get("/hello")
    async def hello():
        return {"message": "Hello World"}

    @app.post("/echo", status_code=201)
    async def echo(request: Request):
        return {"echoed": request.json}

    @app.get("/error")
    async def error():
        raise HTTPException(418, "I am a teapot")

    router = APIRouter(prefix="/api/v1")

    @router.get("/items")
    async def list_items():
        return {"items": [1, 2, 3]}

    app.include_router(router)

    with TestClient(app) as client:
        assert client.get("/hello").status_code == 200
        assert client.post("/echo", json_data={"foo": "bar"}).status_code == 201
        assert client.get("/error").status_code == 418
        assert client.get("/api/v1/items").status_code == 200
        assert client.get("/openapi.json").status_code == 200
        assert client.get("/docs").status_code == 200
        assert client.get("/redoc").status_code == 200
        assert client.get("/health").status_code == 200


def test_security_helpers():
    jwt = JWTAuth(secret_key="test-secret-key-at-least-32-chars!!")
    token = jwt.create_token({"sub": "user123"})
    payload = jwt.verify_token(token)
    assert payload["sub"] == "user123"

    hashed = hash_password("secure_password_123")
    assert verify_password("secure_password_123", hashed)
    assert not verify_password("wrong_password", hashed)

    csrf = CSRFProtection(secret_key="test-csrf-secret-32-chars-long!!")
    csrf_token = csrf.generate_token("session123")
    assert csrf.validate_token(csrf_token, "session123")
    assert not csrf.validate_token(csrf_token, "other_session")

    key_manager = APIKeyManager()
    key = key_manager.generate_key("test-app")
    assert key_manager.validate_key(key)["name"] == "test-app"
    key_manager.revoke_key(key)
    assert key_manager.validate_key(key) is None

    signed = sign_value("data123", "secret-key")
    assert verify_signed_value(signed, "secret-key") == "data123"
    assert verify_signed_value(signed + "x", "secret-key") is None

    warnings = SecurityScanner.scan_request("GET", "/page?id=1' OR 1=1--", {}, "")
    assert warnings


def test_logging_and_compression_modules():
    logger = get_logger("test")
    logger.info("test message")

    logger2 = Logger("level-test", level=LogLevel.ERROR)
    logger2.info("should be filtered")
    logger2.error("should log")

    comp = CompressionMiddleware(minimum_size=10)
    req = Request(method="GET", path="/", headers={"accept-encoding": "gzip"}, body=b"")
    body_text = "A" * 1000
    resp = Response(content=body_text, status=200, content_type="text/plain")
    compressed = comp.process_response(req, resp)

    assert compressed.headers.get("content-encoding") == "gzip"
    decompressed = gzip.decompress(compressed.content).decode()
    assert decompressed == body_text


def test_sessions_uploads_sse_and_middleware_helpers():
    store = InMemorySessionStore()
    sid = "test-session-id"
    store.set(sid, {"user": "bob"})
    assert store.get(sid)["user"] == "bob"
    store.delete(sid)
    assert store.get(sid) is None

    upload = UploadFile(
        filename="../../../etc/passwd", content_type="text/plain", content=b"test"
    )
    assert ".." not in upload.filename
    assert "/" not in upload.filename
    assert upload.size == 4

    event = SSEEvent(data="hello", event="greeting", id="1")
    encoded = event.encode()
    assert "event: greeting" in encoded
    assert "data: hello" in encoded
    assert "id: 1" in encoded

    async def run_event_source_test():
        source = EventSource()
        stream = source.subscribe()
        try:
            next_event = asyncio.create_task(stream.__anext__())
            await asyncio.sleep(0)
            await source.publish("test-data", event="test")
            return await asyncio.wait_for(next_event, timeout=1)
        finally:
            await stream.aclose()

    item = asyncio.run(run_event_source_test())
    assert item["event"] == "test"
    assert item["data"] == "test-data"

    limiter = RateLimitMiddleware(requests_per_minute=2)
    rl_req = Request(method="GET", path="/test", headers={}, body=b"")
    rl_req.remote_addr = "10.0.0.1"
    assert limiter.process_request(rl_req) is None
    assert limiter.process_request(rl_req) is None
    assert limiter.process_request(rl_req).status == 429

    sec_headers = SecurityHeadersMiddleware()
    sec_resp = sec_headers.process_response(
        rl_req, Response(content="ok", status=200, content_type="text/plain")
    )
    assert sec_resp.headers.get("x-content-type-options") == "nosniff"
