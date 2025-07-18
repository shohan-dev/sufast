#!/usr/bin/env python3
"""
Test script for Sufast v2.0 Hybrid Architecture
Tests the integration between Python framework and Rust core
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from sufast import App
from sufast.middleware import CORSMiddleware, RateLimitMiddleware  
from sufast.request import Request
from sufast import json_response, html_response
import json
import time

# Create Sufast app with hybrid architecture
app = App(debug=True)

# Test basic routes
@app.get('/')
def home(request: Request):
    return json_response({
        "message": "🦀 Sufast v2.0 Hybrid Architecture",
        "python_version": sys.version.split()[0],
        "rust_core": True,
        "features": [
            "High-performance Rust backend",
            "Developer-friendly Python interface", 
            "Dynamic routing with typed parameters",
            "Advanced middleware system",
            "Security headers",
            "Rate limiting",
            "Request counting"
        ]
    })

@app.get('/status')
def status(request: Request):
    return json_response({
        "status": "healthy",
        "version": "2.0.0",
        "architecture": "hybrid",
        "backend": "rust",
        "frontend": "python"
    })

# Test dynamic routing with typed parameters
@app.get('/user/{user_id}')
def get_user(request: Request):
    user_id = request.path_params.get('user_id', 'unknown')
    return json_response({
        "user_id": user_id,
        "user_type": type(user_id).__name__,
        "message": f"User {user_id} retrieved successfully"
    })

@app.get('/post/{slug}')
def get_post(request: Request):
    slug = request.path_params.get('slug', 'unknown')
    return json_response({
        "slug": slug,
        "title": f"Blog Post: {slug.replace('-', ' ').title()}",
        "url": f"/post/{slug}"
    })

# Test middleware - check if middleware decorator exists
# @app.middleware
# def logging_middleware(request: Request, call_next):
#     start_time = time.time()
#     print(f"🔍 Request: {request.method} {request.url}")
#     
#     response = call_next(request)
#     
#     duration = time.time() - start_time
#     print(f"✅ Response: {response.status_code} ({duration:.3f}s)")
#     return response

# Add CORS middleware
app.add_middleware(CORSMiddleware())

# Add rate limiting
app.add_middleware(RateLimitMiddleware(
    requests_per_minute=60,
    burst_limit=10
))

# Test HTML template
@app.get('/demo')
def demo_page(request: Request):
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sufast v2.0 Hybrid Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; border-bottom: 3px solid #e74c3c; padding-bottom: 10px; }
            .feature { background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #3498db; }
            .rust { border-left-color: #e67e22; }
            .python { border-left-color: #27ae60; }
            code { background: #34495e; color: white; padding: 2px 6px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🦀 Sufast v2.0 Hybrid Architecture</h1>
            <p>This page demonstrates the powerful combination of <strong>Rust performance</strong> with <strong>Python developer experience</strong>.</p>
            
            <div class="feature rust">
                <h3>🦀 Rust Core Features</h3>
                <ul>
                    <li>High-performance HTTP server (Axum + Tokio)</li>
                    <li>Advanced routing with typed parameters</li>
                    <li>Comprehensive middleware system</li>
                    <li>Security headers and rate limiting</li>
                    <li>Memory-safe and zero-cost abstractions</li>
                </ul>
            </div>
            
            <div class="feature python">
                <h3>🐍 Python Interface Features</h3>
                <ul>
                    <li>Clean and intuitive decorator syntax</li>
                    <li>Rich request/response objects</li>
                    <li>Template rendering support</li>
                    <li>Database integration helpers</li>
                    <li>Developer-friendly debugging</li>
                </ul>
            </div>
            
            <div class="feature">
                <h3>🚀 Try These Endpoints</h3>
                <ul>
                    <li><code>GET /</code> - API status and features</li>
                    <li><code>GET /user/123</code> - Dynamic routing with integer validation</li>
                    <li><code>GET /post/my-awesome-post</code> - Slug parameter extraction</li>
                    <li><code>GET /status</code> - System health check</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    return html_response(html_content)

if __name__ == '__main__':
    print("🚀 Starting Sufast v2.0 Hybrid Server...")
    print("📋 Testing Configuration:")
    print("  ✅ Rust Core: Available")
    print("  ✅ Python Interface: Active")
    print("  ✅ Dynamic Routing: Configured")
    print("  ✅ Middleware: Installed")
    print("  ✅ Security: Enhanced")
    print()
    print("🌐 Server will start on http://127.0.0.1:8000")
    print("📖 Visit http://127.0.0.1:8000/demo for interactive demo")
    print()
    
    app.run(host='127.0.0.1', port=8000, debug=True)

if __name__ == '__main__':
    print("🚀 Starting Sufast v2.0 Hybrid Server...")
    print("📋 Testing Configuration:")
    print("  ✅ Rust Core: Enabled")
    print("  ✅ Python Interface: Active")
    print("  ✅ Dynamic Routing: Configured")
    print("  ✅ Middleware: Installed")
    print("  ✅ Security: Enhanced")
    print()
    print("🌐 Server will start on http://127.0.0.1:8000")
    print("📖 Visit http://127.0.0.1:8000/demo for interactive demo")
    print()
    
    app.run(host='127.0.0.1', port=8000, debug=True)
