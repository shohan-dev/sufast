#!/usr/bin/env python3
"""
Test script for Dynamic Routing in Sufast v2.0
Tests routes like /product/{product_id} with Rust+Python hybrid architecture
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from sufast import App, json_response, html_response

# Create Sufast app with dynamic routing
app = App(debug=True)

# Static routes
@app.get('/')
def home():
    return {
        "message": "🦀 Sufast v2.0 Dynamic Routing Test",
        "framework": "Hybrid Rust+Python",
        "features": ["Dynamic routes", "Path parameters", "Type validation"],
        "test_endpoints": [
            "GET /product/123",
            "GET /user/456", 
            "GET /post/my-awesome-post",
            "GET /category/electronics/product/789"
        ]
    }

# Test 1: Simple dynamic route
@app.get('/product/{product_id}')
def get_product(request):
    product_id = request.path_params.get('product_id', 'unknown')
    return {
        "product_id": product_id,
        "product_type": type(product_id).__name__,
        "message": f"Product {product_id} details",
        "path": request.path,
        "method": request.method
    }

# Test 2: User dynamic route
@app.get('/user/{user_id}')
def get_user(request):
    user_id = request.path_params.get('user_id', 'unknown')
    return {
        "user_id": user_id,
        "user_type": type(user_id).__name__,
        "message": f"User {user_id} profile",
        "path_params": request.path_params,
        "query_params": request.query_params
    }

# Test 3: POST with dynamic route
@app.post('/user/{user_id}/posts')
def create_user_post(request):
    user_id = request.path_params.get('user_id', 'unknown')
    return {
        "user_id": user_id,
        "action": "create_post",
        "message": f"Creating post for user {user_id}",
        "body_data": request.json or "No JSON data"
    }

# Test 4: Multiple parameters
@app.get('/category/{category}/product/{product_id}')
def get_category_product(request):
    category = request.path_params.get('category', 'unknown')
    product_id = request.path_params.get('product_id', 'unknown')
    return {
        "category": category,
        "product_id": product_id,
        "message": f"Product {product_id} in category {category}",
        "all_params": request.path_params
    }

# Test 5: Slug parameter
@app.get('/post/{slug}')
def get_post(request):
    slug = request.path_params.get('slug', 'unknown')
    return {
        "slug": slug,
        "title": f"Blog Post: {slug.replace('-', ' ').title()}",
        "url": f"/post/{slug}",
        "message": "Dynamic slug routing working!"
    }

# Test 6: Route with query parameters
@app.get('/search/{query}')
def search(request):
    query = request.path_params.get('query', '')
    page = request.query_params.get('page', '1')
    limit = request.query_params.get('limit', '10')
    
    return {
        "search_query": query,
        "page": int(page),
        "limit": int(limit),
        "message": f"Searching for '{query}' - page {page}",
        "results": [f"Result {i+1} for {query}" for i in range(3)]
    }

# HTML demo page
@app.get('/demo')
def demo_page(request):
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sufast Dynamic Routing Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f0f0f0; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            h1 { color: #2c3e50; }
            .test-link { display: block; margin: 10px 0; padding: 10px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }
            .test-link:hover { background: #2980b9; }
            code { background: #ecf0f1; padding: 2px 6px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🦀 Sufast v2.0 Dynamic Routing Test</h1>
            <p>Test the dynamic routing capabilities of our hybrid Rust+Python framework!</p>
            
            <h3>🧪 Test Endpoints:</h3>
            <a href="/product/123" class="test-link">GET /product/123 - Product by ID</a>
            <a href="/user/456" class="test-link">GET /user/456 - User by ID</a>
            <a href="/post/my-awesome-blog-post" class="test-link">GET /post/my-awesome-blog-post - Post by slug</a>
            <a href="/category/electronics/product/789" class="test-link">GET /category/electronics/product/789 - Nested params</a>
            <a href="/search/rust?page=2&limit=5" class="test-link">GET /search/rust?page=2&limit=5 - With query params</a>
            
            <h3>📊 Features Tested:</h3>
            <ul>
                <li>✅ Dynamic path parameters like <code>{product_id}</code></li>
                <li>✅ Multiple parameters in one route</li>
                <li>✅ Slug parameters with dashes</li>
                <li>✅ Query parameter parsing</li>
                <li>✅ Path + query parameter combination</li>
                <li>✅ POST requests with dynamic routes</li>
            </ul>
        </div>
    </body>
    </html>
    """
    return html_content

if __name__ == '__main__':
    print("🚀 Starting Sufast v2.0 Dynamic Routing Test...")
    print("📋 Configuration:")
    print("  🦀 Rust Core: Enhanced with dynamic routing")
    print("  🐍 Python Interface: Dynamic request handlers")
    print("  🔗 Route Matching: Pattern-based with parameters")
    print("  📊 Parameter Extraction: Automatic type handling")
    print()
    print("🌐 Test Server starting on http://127.0.0.1:8000")
    print("📖 Visit http://127.0.0.1:8000/demo for interactive testing")
    print()
    
    try:
        app.run(port=8000, production=False)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        import traceback
        traceback.print_exc()
