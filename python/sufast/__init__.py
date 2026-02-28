"""
Sufast - Hybrid Rust+Python Web Framework
==========================================
FastAPI-style API with optional Rust-powered performance.

Combines the ease of Python with the speed of Rust.
Works standalone in Python or with the Rust core for 10x+ throughput.

Quick Start:
    from sufast import Sufast, Request, Response

    app = Sufast(title="My API", version="1.0.0")

    @app.get("/")
    async def root():
        return {"message": "Hello World"}

    @app.get("/users/{user_id}")
    async def get_user(user_id: int):
        return {"user_id": user_id}

    @app.post("/items")
    async def create_item(request: Request):
        data = request.json
        return {"created": data}

    app.run(host="0.0.0.0", port=8000)
"""

__version__ = "3.0.0"

# Core framework
from .app import Sufast, APIRouter, create_app

# Request / Response
from .request import (
    Request, Response,
    json_response, html_response, text_response,
    redirect_response, file_response,
)

# Exceptions
from .exceptions import (
    HTTPException,
    WebSocketException,
    RequestValidationError,
)

# WebSocket
from .websocket import WebSocket, ConnectionManager

# Background tasks
from .background import BackgroundTask, BackgroundTasks

# Middleware
from .middleware import (
    CORSMiddleware,
    RateLimitMiddleware,
    AuthMiddleware,
    LoggingMiddleware,
    SecurityHeadersMiddleware,
    ValidationMiddleware,
    MiddlewareStack,
)

# Security
from .security import (
    JWTAuth,
    CSRFProtection,
    hash_password,
    verify_password,
    APIKeyManager,
    SecurityScanner,
    sign_value,
    verify_signed_value,
)

# Logging
from .logging import (
    Logger,
    get_logger,
    configure_logging,
    AccessLogger,
)

# Compression
from .compression import CompressionMiddleware

# Sessions
from .sessions import (
    SessionMiddleware,
    InMemorySessionStore,
    FileSessionStore,
)

# File uploads
from .uploads import UploadFile, FormData, parse_multipart

# Server-Sent Events
from .sse import SSEEvent, SSEResponse, EventSource

# Database
from .database import DatabaseConnection

# Socket.IO
from .socketio_support import SocketIOManager

# Test client
from .testclient import TestClient

__all__ = [
    # Framework
    "Sufast",
    "APIRouter",
    "create_app",
    # Request / Response
    "Request",
    "Response",
    "json_response",
    "html_response",
    "text_response",
    "redirect_response",
    "file_response",
    # Exceptions
    "HTTPException",
    "WebSocketException",
    "RequestValidationError",
    # WebSocket
    "WebSocket",
    "ConnectionManager",
    # Background tasks
    "BackgroundTask",
    "BackgroundTasks",
    # Middleware
    "CORSMiddleware",
    "RateLimitMiddleware",
    "AuthMiddleware",
    "LoggingMiddleware",
    "SecurityHeadersMiddleware",
    "ValidationMiddleware",
    "MiddlewareStack",
    # Security
    "JWTAuth",
    "CSRFProtection",
    "hash_password",
    "verify_password",
    "APIKeyManager",
    "SecurityScanner",
    "sign_value",
    "verify_signed_value",
    # Logging
    "Logger",
    "get_logger",
    "configure_logging",
    "AccessLogger",
    # Compression
    "CompressionMiddleware",
    # Sessions
    "SessionMiddleware",
    "InMemorySessionStore",
    "FileSessionStore",
    # File uploads
    "UploadFile",
    "FormData",
    "parse_multipart",
    # Server-Sent Events
    "SSEEvent",
    "SSEResponse",
    "EventSource",
    # Database
    "DatabaseConnection",
    # Socket.IO
    "SocketIOManager",
    # Test
    "TestClient",
]
