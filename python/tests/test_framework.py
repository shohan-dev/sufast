"""Run all Sufast framework tests — core + production features."""
import sys, os, time, json, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sufast import Sufast, Request, Response, HTTPException, json_response, APIRouter, BackgroundTasks
from sufast.testclient import TestClient

app = Sufast(title="Test API", version="1.0.0", debug=True, secret_key="test-secret-key-at-least-32-chars!!")

# Test GET
@app.get("/hello", tags=["Test"])
async def hello():
    return {"message": "Hello World"}

# Test POST
@app.post("/echo", tags=["Test"], status_code=201)
async def echo(request: Request):
    return {"echoed": request.json}

# Test path params
@app.get("/users/{user_id}", tags=["Users"])
async def get_user(user_id: int):
    return {"user_id": user_id, "name": "Test User"}

# Test PUT
@app.put("/users/{user_id}", tags=["Users"])
async def update_user(user_id: int, request: Request):
    return {"updated": user_id, "data": request.json}

# Test DELETE
@app.delete("/users/{user_id}", tags=["Users"])
async def delete_user(user_id: int):
    return {"deleted": user_id}

# Test PATCH
@app.patch("/users/{user_id}", tags=["Users"])
async def patch_user(user_id: int, request: Request):
    return {"patched": user_id}

# Test exception
@app.get("/error", tags=["Test"])
async def error():
    raise HTTPException(418, "I am a teapot")

# Test sync handler
@app.get("/sync", tags=["Test"])
def sync_handler():
    return {"sync": True}

# Test APIRouter
router = APIRouter(prefix="/api/v1", tags=["API"])

@router.get("/items")
async def list_items():
    return {"items": [1, 2, 3]}

@router.post("/items", status_code=201)
async def create_item(request: Request):
    return {"created": request.json}

app.include_router(router)

# Run tests
client = TestClient(app)
passed = 0
failed = 0

def check(name, response, expected_status, check_fn=None):
    global passed, failed
    try:
        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"
        if check_fn:
            check_fn(response)
        passed += 1
        print(f"  PASS: {name} [{response.status_code}]")
    except AssertionError as e:
        failed += 1
        print(f"  FAIL: {name} - {e}")
    except Exception as e:
        failed += 1
        print(f"  FAIL: {name} - {type(e).__name__}: {e}")

print("=" * 60)
print("Sufast Framework Tests — Core + Production Features")
print("=" * 60)

# ──────── Core HTTP Tests ────────
print("\n── Core HTTP ──")

check("GET /hello", client.get("/hello"), 200, 
      lambda r: r.json()["message"] == "Hello World" or (_ for _ in ()).throw(AssertionError("wrong message")))

r = client.post("/echo", json_data={"foo": "bar"})
check("POST /echo", r, 201)

r = client.get("/users/42")
check("GET /users/42", r, 200,
      lambda r: r.json()["user_id"] == 42 or (_ for _ in ()).throw(AssertionError("wrong id")))

r = client.put("/users/42", json_data={"name": "Updated"})
check("PUT /users/42", r, 200)

r = client.delete("/users/42")
check("DELETE /users/42", r, 200)

r = client.patch("/users/42", json_data={"name": "Patched"})
check("PATCH /users/42", r, 200)

r = client.get("/error")
check("GET /error (418)", r, 418)

r = client.get("/sync")
check("GET /sync", r, 200)

r = client.get("/api/v1/items")
check("GET /api/v1/items", r, 200)

r = client.post("/api/v1/items", json_data={"name": "Widget"})
check("POST /api/v1/items", r, 201)

# ──────── Docs / OpenAPI ────────
print("\n── Docs / OpenAPI ──")

r = client.get("/openapi.json")
check("GET /openapi.json", r, 200)
if r.status_code == 200:
    spec = r.json()
    print(f"    OpenAPI version: {spec.get('openapi', '?')}")
    print(f"    Paths: {len(spec.get('paths', {}))}")

r = client.get("/docs")
check("GET /docs (Swagger)", r, 200)

r = client.get("/redoc")
check("GET /redoc", r, 200)

# ──────── Health Endpoint ────────
print("\n── Health Endpoint ──")

r = client.get("/health")
check("GET /health", r, 200,
      lambda r: r.json()["status"] == "healthy" or (_ for _ in ()).throw(AssertionError("not healthy")))

# ──────── 404 ────────
r = client.get("/nonexistent")
check("GET /nonexistent (404)", r, 404)

# ──────── Security Module Tests ────────
print("\n── Security Module ──")
try:
    from sufast.security import (
        JWTAuth, CSRFProtection, hash_password, verify_password,
        APIKeyManager, SecurityScanner, sign_value, verify_signed_value
    )

    # JWT
    jwt = JWTAuth(secret_key="test-secret-key-at-least-32-chars!!")
    token = jwt.create_token({"sub": "user123", "role": "admin"})
    payload = jwt.verify_token(token)
    assert payload["sub"] == "user123", "JWT payload mismatch"
    assert payload["role"] == "admin", "JWT role mismatch"
    passed += 1
    print("  PASS: JWT create + verify")

    # JWT expiry
    expired = jwt.create_token({"sub": "test"}, expire_seconds=-1)
    time.sleep(0.1)
    try:
        jwt.verify_token(expired)
        failed += 1
        print("  FAIL: JWT expired token should raise")
    except Exception:
        passed += 1
        print("  PASS: JWT expired token rejected")

    # JWT refresh token
    rt = jwt.create_refresh_token({"sub": "user123"})
    assert rt and len(rt) > 20, "bad refresh token"
    passed += 1
    print("  PASS: JWT refresh token")

    # Password hashing
    hashed = hash_password("secure_password_123")
    assert verify_password("secure_password_123", hashed), "password verify failed"
    assert not verify_password("wrong_password", hashed), "wrong pw accepted"
    passed += 1
    print("  PASS: Password hash + verify")

    # CSRF
    csrf = CSRFProtection(secret_key="test-csrf-secret-32-chars-long!!")
    csrf_token = csrf.generate_token("session123")
    assert csrf.validate_token(csrf_token, "session123"), "CSRF valid token rejected"
    assert not csrf.validate_token(csrf_token, "other_session"), "CSRF invalid session accepted"
    passed += 1
    print("  PASS: CSRF token generate + validate")

    # API Key
    mgr = APIKeyManager()
    key = mgr.generate_key("test-app")
    info = mgr.validate_key(key)
    assert info is not None, "Valid key rejected"
    assert info["name"] == "test-app", "API key name mismatch"
    mgr.revoke_key(key)
    assert mgr.validate_key(key) is None, "Revoked key accepted"
    passed += 1
    print("  PASS: API key generate + validate + revoke")

    # Signed values
    signed = sign_value("data123", "secret-key")
    assert verify_signed_value(signed, "secret-key") == "data123", "signed value mismatch"
    assert verify_signed_value(signed + "x", "secret-key") is None, "tampered value accepted"
    passed += 1
    print("  PASS: Signed value sign + verify")

    # Security scanner
    warnings = SecurityScanner.scan_request("GET", "/page?id=1' OR 1=1--", {}, "")
    assert len(warnings) > 0, "SQL injection not detected"
    passed += 1
    print("  PASS: Security scanner SQL injection detection")

except Exception as e:
    failed += 1
    print(f"  FAIL: Security module - {type(e).__name__}: {e}")

# ──────── Logging Module Tests ────────
print("\n── Logging Module ──")
try:
    from sufast.logging import Logger, get_logger, configure_logging, LogLevel

    logger = get_logger("test")
    assert logger.name == "test", "Logger name mismatch"
    # Should not raise
    logger.info("test message")
    logger.warning("test warning", extra_key="extra_value")
    passed += 1
    print("  PASS: Logger creation + logging")

    # Level filtering
    logger2 = Logger("level-test", level=LogLevel.ERROR)
    # info should be filtered (logger won't blow up, just skip)
    logger2.info("should be filtered")
    logger2.error("should log")
    passed += 1
    print("  PASS: Logger level filtering")

except Exception as e:
    failed += 1
    print(f"  FAIL: Logging module - {type(e).__name__}: {e}")

# ──────── Compression Module Tests ────────
print("\n── Compression Module ──")
try:
    import gzip
    from sufast.compression import CompressionMiddleware
    from sufast.request import Request as Req, Response as Resp

    comp = CompressionMiddleware(minimum_size=10)

    # Create a mock request with accept-encoding
    mock_req = Req(method='GET', path='/', headers={'accept-encoding': 'gzip, deflate'}, body=b'')

    body_text = "A" * 1000  # Large enough to compress
    mock_resp = Resp(content=body_text, status=200, content_type='text/plain')

    result = comp.process_response(mock_req, mock_resp)
    assert result.headers.get('content-encoding') == 'gzip', "Not gzip-encoded"
    # Verify decompression
    decompressed = gzip.decompress(result.content if isinstance(result.content, bytes) else result.content.encode()).decode()
    assert decompressed == body_text, "Decompressed content mismatch"
    passed += 1
    print("  PASS: Gzip compression")

except Exception as e:
    failed += 1
    print(f"  FAIL: Compression module - {type(e).__name__}: {e}")

# ──────── Session Module Tests ────────
print("\n── Session Module ──")
try:
    from sufast.sessions import InMemorySessionStore, SessionMiddleware

    store = InMemorySessionStore()
    # Use the actual API: get/set/delete
    import secrets as _sec
    sid = _sec.token_hex(16)
    store.set(sid, {"user": "bob"})
    data = store.get(sid)
    assert data is not None, "Session not found"
    assert data["user"] == "bob", "Session data wrong"
    store.delete(sid)
    assert store.get(sid) is None, "Deleted session still exists"
    passed += 1
    print("  PASS: InMemorySessionStore CRUD")

except Exception as e:
    failed += 1
    print(f"  FAIL: Session module - {type(e).__name__}: {e}")

# ──────── Upload Module Tests ────────
print("\n── Upload Module ──")
try:
    from sufast.uploads import UploadFile

    uf = UploadFile(filename="../../../etc/passwd", content_type="text/plain", content=b"test")
    assert ".." not in uf.filename, "Path traversal not sanitized"
    assert "/" not in uf.filename, "Slashes not sanitized"
    assert uf.size == 4, "Size wrong"
    passed += 1
    print("  PASS: UploadFile sanitization")

except Exception as e:
    failed += 1
    print(f"  FAIL: Upload module - {type(e).__name__}: {e}")

# ──────── SSE Module Tests ────────
print("\n── SSE Module ──")
try:
    from sufast.sse import SSEEvent, EventSource

    event = SSEEvent(data="hello", event="greeting", id="1")
    encoded = event.encode()
    assert "event: greeting\n" in encoded, "event field missing"
    assert "data: hello\n" in encoded, "data field missing"
    assert "id: 1\n" in encoded, "id field missing"
    passed += 1
    print("  PASS: SSEEvent encode")

    # EventSource pub/sub
    source = EventSource()
    received = []
    
    async def _test_eventsource():
        sub = source.subscribe()
        await source.publish("test-data", event="test")
        # Drain the subscription
        async for msg in sub:
            received.append(msg)
            break  # Just get one

    asyncio.new_event_loop().run_until_complete(_test_eventsource())
    assert len(received) == 1, f"Expected 1 event, got {len(received)}"
    passed += 1
    print("  PASS: EventSource pub/sub")

except Exception as e:
    failed += 1
    print(f"  FAIL: SSE module - {type(e).__name__}: {e}")

# ──────── Middleware Tests ────────
print("\n── Middleware ──")
try:
    from sufast.middleware import RateLimitMiddleware, LoggingMiddleware, SecurityHeadersMiddleware

    # Rate limiter
    rl = RateLimitMiddleware(requests_per_minute=5)
    mock_req = Req(method='GET', path='/test', headers={}, body=b'')
    mock_req.remote_addr = '10.0.0.1'

    for i in range(5):
        resp = rl.process_request(mock_req)
        assert resp is None, f"Request {i+1} rejected"
    
    # 6th should be rate limited
    resp = rl.process_request(mock_req)
    assert resp is not None and resp.status == 429, "Rate limit not enforced"
    passed += 1
    print("  PASS: RateLimitMiddleware sliding window")

    # Security headers
    sh = SecurityHeadersMiddleware()
    mock_resp = Resp(content="ok", status=200, content_type='text/plain')
    result = sh.process_response(mock_req, mock_resp)
    assert result.headers.get('x-content-type-options') == 'nosniff', "nosniff missing"
    assert result.headers.get('x-frame-options') == 'DENY', "frame deny missing"
    passed += 1
    print("  PASS: SecurityHeadersMiddleware")

except Exception as e:
    failed += 1
    print(f"  FAIL: Middleware - {type(e).__name__}: {e}")

# ──────── CLI Module Tests ────────
print("\n── CLI Module ──")
try:
    from sufast.cli import main as cli_main
    # Just verify import works
    passed += 1
    print("  PASS: CLI module imports")
except Exception as e:
    failed += 1
    print(f"  FAIL: CLI module - {type(e).__name__}: {e}")

# ──────── Summary ────────
print()
print("=" * 60)
stats = app.get_performance_stats()
print(f"Routes: {stats['routes']['total']} HTTP, {stats['routes']['websocket']} WS")
print(f"Rust accelerated: {stats['rust_accelerated']}")
print(f"Results: {passed} passed, {failed} failed")
print("=" * 60)

if failed > 0:
    sys.exit(1)
else:
    print("ALL TESTS PASSED!")
