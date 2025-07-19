"""
Sufast - Ultimate Optimized Hybrid Python Web Framework
Combines the speed of Rust with the flexibility of Python.
Three-tier performance architecture:
- Static routes: 52K+ RPS (pre-compiled)
- Cached routes: 45K+ RPS (intelligent caching) 
- Dynamic routes: 2K+ RPS (real-time processing)
"""

from .core_ultimate import Sufast, create_app
from .database import DatabaseConnection
from .middleware import CORSMiddleware, RateLimitMiddleware, AuthMiddleware, MiddlewareStack
from .request import Request, Response, json_response, html_response

# Legacy support
from .core import SufastUltraOptimized as SufastLegacy

__version__ = "2.0.0"
__all__ = [
    "Sufast", "create_app", "DatabaseConnection", "SufastLegacy",
    "CORSMiddleware", "RateLimitMiddleware", "AuthMiddleware", "MiddlewareStack",
    "Request", "Response", "json_response", "html_response"
]

from .core import (
    SufastUltraOptimized, 
    Sufast_server, 
    RustCore, 
    Request, 
    Response,
    create_app, 
    quick_static_app, 
    benchmark_app
)

__version__ = "2.0.0"

__all__ = [
    "SufastUltraOptimized",
    "Sufast_server", 
    "RustCore",
    "Request",
    "Response",
    "create_app",
    "quick_static_app", 
    "benchmark_app",
]

# Backward compatibility aliases
App = SufastUltraOptimized
