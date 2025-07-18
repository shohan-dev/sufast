"""
Sufast - Ultra-fast Python web framework with Rust core.
Now with complete modern web framework features!
"""

from .core import App
from .request import Request, Response, json_response, html_response, text_response, redirect_response, file_response
from .middleware import (
    Middleware, MiddlewareStack, CORSMiddleware, AuthMiddleware, 
    RateLimitMiddleware, LoggingMiddleware, SecurityHeadersMiddleware, 
    ValidationMiddleware
)
from .routing import Router, RouteGroup, Route, route, get, post, put, delete, patch
from .templates import TemplateEngine, JinjaTemplateEngine, StaticFileHandler
from .database import Database, Model, SQLiteConnection, Migration, MigrationManager

__version__ = "2.0.0"
__all__ = [
    # Core
    "App",
    
    # Request/Response
    "Request", "Response", "json_response", "html_response", 
    "text_response", "redirect_response", "file_response",
    
    # Middleware
    "Middleware", "MiddlewareStack", "CORSMiddleware", "AuthMiddleware",
    "RateLimitMiddleware", "LoggingMiddleware", "SecurityHeadersMiddleware",
    "ValidationMiddleware",
    
    # Routing
    "Router", "RouteGroup", "Route", "route", "get", "post", "put", "delete", "patch",
    
    # Templates
    "TemplateEngine", "JinjaTemplateEngine", "StaticFileHandler",
    
    # Database
    "Database", "Model", "SQLiteConnection", "Migration", "MigrationManager"
]
