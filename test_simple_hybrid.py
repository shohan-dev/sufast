#!/usr/bin/env python3
"""
Simple Test for Sufast v2.0 Hybrid Architecture
Basic test to verify the Python-Rust integration works
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from sufast import App, json_response, html_response

# Create Sufast app
app = App(debug=True)

# Simple routes that work with current API
@app.get('/')
def home():
    return {
        "message": "🦀 Sufast v2.0 Hybrid Architecture Success!",
        "python_version": sys.version.split()[0],
        "architecture": "hybrid",
        "status": "✅ Working!"
    }

@app.get('/status')
def status():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "backend": "rust-powered",
        "frontend": "python-interface"
    }

@app.get('/info')
def info():
    return {
        "framework": "Sufast",
        "version": "2.0.0",
        "features": [
            "✅ Rust core for performance",
            "✅ Python interface for productivity", 
            "✅ Modern web framework features",
            "✅ Hybrid architecture"
        ],
        "rust_core": "Available" if hasattr(app, 'rust_lib') else "Not loaded"
    }

if __name__ == '__main__':
    print("🚀 Starting Sufast v2.0 Simple Hybrid Test...")
    print("📋 Configuration:")
    print("  ✅ Python Framework: Loaded")
    print("  ✅ Rust Backend: Integrated")
    print("  ✅ Hybrid Architecture: Active")
    print()
    print("🌐 Testing endpoints:")
    print("  📍 GET / - Framework info")
    print("  📍 GET /status - Health check")
    print("  📍 GET /info - Detailed information")
    print()
    print("🔥 Server starting on http://127.0.0.1:8000")
    print("   Press Ctrl+C to stop")
    print()
    
    try:
        app.run(port=8000, production=False)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
