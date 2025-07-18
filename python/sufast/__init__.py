"""
Sufast Ultra-Optimized v2.0 - Ultra-fast Python web framework with Rust core.
Complete three-tier optimization system for maximum performance!

Performance Targets:
- Static Routes: 52,000+ RPS (Rust pre-compilation)  
- Cached Routes: 45,000+ RPS (Intelligent TTL caching)
- Dynamic Routes: 2,000+ RPS (Optimized Python processing)
"""

from .core import (
    SufastUltraOptimized, 
    Sufast, 
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
    "Sufast", 
    "RustCore",
    "Request",
    "Response",
    "create_app",
    "quick_static_app", 
    "benchmark_app",
]

# Backward compatibility aliases
App = SufastUltraOptimized
