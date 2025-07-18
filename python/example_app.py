"""
Simplified Sufast v2.0 Example - Testing Static and Dynamic Routes
This demonstrates basic functionality with:
- Static routes
- Dynamic routing with parameters
- Simple JSON responses
- Basic error handling
"""

from sufast import App, json_response, html_response

# Create the application
app = App(debug=True)

# ========================
# STATIC ROUTES
# ========================

@app.get('/')
def home(request):
    """Home page - static route."""
    return json_response({
        'message': '🚀 Welcome to Sufast v2.0!',
        'framework': 'Hybrid Rust+Python',
        'version': '2.0.0',
        'features': [
            'Static routes',
            'Dynamic routes with parameters',
            'High-performance Rust core',
            'Python developer experience'
        ],
        'test_routes': {
            'static': [
                'GET /',
                'GET /about',
                'GET /contact'
            ],
            'dynamic': [
                'GET /user/123',
                'GET /product/456',
                'GET /post/my-blog-post',
                'GET /category/tech/product/789'
            ]
        }
    })

@app.get('/about')
def about(request):
    """About page - static route."""
    return json_response({
        'page': 'about',
        'message': 'This is the about page',
        'framework_info': {
            'name': 'Sufast',
            'version': '2.0.0',
            'backend': 'Rust (High Performance)',
            'frontend': 'Python (Developer Friendly)'
        }
    })

@app.get('/contact')
def contact(request):
    """Contact page - static route."""
    return json_response({
        'page': 'contact',
        'message': 'Contact us!',
        'email': 'hello@sufast.dev',
        'social': {
            'github': 'https://github.com/shohan-dev/sufast',
            'twitter': '@sufast_dev'
        }
    })

# ========================
# DYNAMIC ROUTES
# ========================

users = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

@app.get('/user/{user_id}')
def get_user(request):
    """Get user by ID - dynamic route with single parameter."""
    user_id = request.path_params.get('user_id', 'unknown')
    user = next((u for u in users if u['id'] == int(user_id)), None)
    
    if user:
        return json_response("hello this is user " + user['name'])
    else:
        return json_response({'error': 'User not found'}, status=404)
    

@app.get('/product/{product_id}')
def get_product(request):
    """Get product by ID - dynamic route with single parameter."""
    product_id = request.path_params.get('product_id', 'unknown')
    return json_response({
        'route_type': 'dynamic',
        'pattern': '/product/{product_id}',
        'product_id': product_id,
        'product_name': f'Product {product_id}',
        'price': f'${int(product_id) * 10 if product_id.isdigit() else 99}',
        'message': f'Product {product_id} details retrieved',
        'path_params': request.path_params
    })

@app.get('/post/{slug}')
def get_post(request):
    """Get post by slug - dynamic route with slug parameter."""
    slug = request.path_params.get('slug', 'unknown')
    title = slug.replace('-', ' ').title()
    return json_response({
        'route_type': 'dynamic',
        'pattern': '/post/{slug}',
        'slug': slug,
        'title': title,
        'content': f'This is the content for: {title}',
        'url': f'/post/{slug}',
        'message': f'Blog post "{title}" retrieved'
    })

@app.get('/category/{category}/product/{product_id}')
def get_category_product(request):
    """Get product in category - dynamic route with multiple parameters."""
    category = request.path_params.get('category', 'unknown')
    product_id = request.path_params.get('product_id', 'unknown')
    
    return json_response({
        'route_type': 'dynamic',
        'pattern': '/category/{category}/product/{product_id}',
        'category': category,
        'product_id': product_id,
        'product_name': f'{category.title()} Product {product_id}',
        'message': f'Product {product_id} in {category} category',
        'all_path_params': request.path_params,
        'breadcrumb': [
            {'name': 'Home', 'url': '/'},
            {'name': category.title(), 'url': f'/category/{category}'},
            {'name': f'Product {product_id}', 'url': f'/category/{category}/product/{product_id}'}
        ]
    })

# ========================
# ROUTES WITH QUERY PARAMETERS
# ========================

@app.get('/search/{query}')
def search(request):
    """Search with query parameters - dynamic route + query params."""
    query = request.path_params.get('query', '')
    page = int(request.query_params.get('page', '1'))
    limit = int(request.query_params.get('limit', '10'))
    sort = request.query_params.get('sort', 'relevance')
    
    return json_response({
        'route_type': 'dynamic_with_query',
        'pattern': '/search/{query}',
        'search_query': query,
        'pagination': {
            'page': page,
            'limit': limit,
            'sort': sort
        },
        'results': [
            f'Result {i+1} for "{query}"' for i in range(min(limit, 5))
        ],
        'total_results': 25,
        'message': f'Found results for "{query}" (page {page})'
    })

# ========================
# HTTP METHODS TESTING
# ========================

@app.post('/user/{user_id}/posts')
def create_user_post(request):
    """Create post for user - POST with dynamic route."""
    user_id = request.path_params.get('user_id', 'unknown')
    return json_response({
        'action': 'create_post',
        'user_id': user_id,
        'method': request.method,
        'message': f'Creating new post for user {user_id}',
        'post_data': request.json or {'title': 'Sample Post', 'content': 'Sample content'}
    })

@app.put('/product/{product_id}')
def update_product(request):
    """Update product - PUT with dynamic route."""
    product_id = request.path_params.get('product_id', 'unknown')
    return json_response({
        'action': 'update_product',
        'product_id': product_id,
        'method': request.method,
        'message': f'Updated product {product_id}',
        'updated_data': request.json or {'name': f'Updated Product {product_id}'}
    })

@app.delete('/product/{product_id}')
def delete_product(request):
    """Delete product - DELETE with dynamic route."""
    product_id = request.path_params.get('product_id', 'unknown')
    return json_response({
        'action': 'delete_product',
        'product_id': product_id,
        'method': request.method,
        'message': f'Deleted product {product_id}',
        'success': True
    })

# ========================
# DEMO PAGE
# ========================

@app.get('/demo')
def demo_page(request):
    """Interactive demo page."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sufast v2.0 Route Testing Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; border-bottom: 3px solid #e74c3c; padding-bottom: 10px; }
            .section { margin: 20px 0; padding: 20px; background: #ecf0f1; border-radius: 5px; }
            .static { border-left: 4px solid #27ae60; }
            .dynamic { border-left: 4px solid #3498db; }
            .method { border-left: 4px solid #e67e22; }
            .test-link { display: inline-block; margin: 5px; padding: 8px 12px; background: #3498db; color: white; text-decoration: none; border-radius: 3px; font-size: 14px; }
            .test-link:hover { background: #2980b9; }
            .get { background: #27ae60; }
            .post { background: #e74c3c; }
            .put { background: #f39c12; }
            .delete { background: #c0392b; }
            code { background: #34495e; color: white; padding: 2px 6px; border-radius: 3px; }
        </style>
        <script>
            function testRoute(url, method = 'GET', data = null) {
                const options = { method };
                if (data) {
                    options.headers = { 'Content-Type': 'application/json' };
                    options.body = JSON.stringify(data);
                }
                
                fetch(url, options)
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('result').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                    })
                    .catch(error => {
                        document.getElementById('result').innerHTML = '<pre>Error: ' + error + '</pre>';
                    });
            }
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Sufast v2.0 Route Testing Demo</h1>
            <p>Test both static and dynamic routes in our hybrid Rust+Python framework!</p>
            
            <div class="section static">
                <h3>📍 Static Routes</h3>
                <p>Fixed paths that don't change:</p>
                <a href="/" class="test-link get">GET /</a>
                <a href="/about" class="test-link get">GET /about</a>
                <a href="/contact" class="test-link get">GET /contact</a>
            </div>
            
            <div class="section dynamic">
                <h3>🔗 Dynamic Routes (Single Parameter)</h3>
                <p>Routes with path parameters like <code>{user_id}</code>:</p>
                <a href="/user/123" class="test-link get">GET /user/123</a>
                <a href="/product/456" class="test-link get">GET /product/456</a>
                <a href="/post/my-awesome-blog-post" class="test-link get">GET /post/my-awesome-blog-post</a>
            </div>
            
            <div class="section dynamic">
                <h3>🔗 Dynamic Routes (Multiple Parameters)</h3>
                <p>Routes with multiple path parameters:</p>
                <a href="/category/electronics/product/789" class="test-link get">GET /category/electronics/product/789</a>
                <a href="/category/books/product/101" class="test-link get">GET /category/books/product/101</a>
            </div>
            
            <div class="section dynamic">
                <h3>🔍 Dynamic Routes with Query Parameters</h3>
                <p>Combining path and query parameters:</p>
                <a href="/search/rust?page=1&limit=5&sort=relevance" class="test-link get">GET /search/rust?page=1&limit=5</a>
                <a href="/search/python?page=2&limit=3&sort=date" class="test-link get">GET /search/python?page=2&limit=3</a>
            </div>
            
            <div class="section method">
                <h3>🛠️ HTTP Methods with Dynamic Routes</h3>
                <p>Test different HTTP methods (click to send request):</p>
                <button onclick="testRoute('/user/123/posts', 'POST', {title: 'Test Post', content: 'Test content'})" class="test-link post">POST /user/123/posts</button>
                <button onclick="testRoute('/product/456', 'PUT', {name: 'Updated Product', price: 99})" class="test-link put">PUT /product/456</button>
                <button onclick="testRoute('/product/789', 'DELETE')" class="test-link delete">DELETE /product/789</button>
            </div>
            
            <div class="section">
                <h3>📊 Response</h3>
                <div id="result" style="background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; min-height: 50px;">
                    <em>Click any link above to see the JSON response here...</em>
                </div>
            </div>
            
            <div class="section">
                <h3>✅ What's Being Tested</h3>
                <ul>
                    <li><strong>Static Routes:</strong> Fixed URLs like <code>/about</code></li>
                    <li><strong>Dynamic Parameters:</strong> Variable parts like <code>/user/{user_id}</code></li>
                    <li><strong>Multiple Parameters:</strong> <code>/category/{category}/product/{product_id}</code></li>
                    <li><strong>Query Parameters:</strong> <code>?page=1&limit=10</code></li>
                    <li><strong>HTTP Methods:</strong> GET, POST, PUT, DELETE</li>
                    <li><strong>Parameter Types:</strong> IDs, slugs, categories</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content
if __name__ == '__main__':
    print("🚀 Starting Sufast v2.0 Route Testing Server")
    print("📊 Features enabled:")
    print("  ✅ Static routes (/, /about, /contact)")
    print("  ✅ Dynamic routes with single parameters (/user/{id})")
    print("  ✅ Dynamic routes with multiple parameters (/category/{cat}/product/{id})")
    print("  ✅ Query parameter support (/search/{query}?page=1)")
    print("  ✅ Multiple HTTP methods (GET, POST, PUT, DELETE)")
    print("  ✅ Interactive demo page (/demo)")
    print("")
    print("🌐 Test Endpoints:")
    print("  📍 Static:    GET /")
    print("  📍 Static:    GET /about") 
    print("  📍 Static:    GET /contact")
    print("  🔗 Dynamic:   GET /user/123")
    print("  🔗 Dynamic:   GET /product/456")
    print("  🔗 Dynamic:   GET /post/my-blog-post")
    print("  🔗 Multi:     GET /category/tech/product/789")
    print("  🔍 Query:     GET /search/rust?page=1&limit=5")
    print("  🛠️ Methods:   POST /user/123/posts")
    print("  📄 Demo:      GET /demo")
    print("")
    print("🌐 Server starting on http://127.0.0.1:8080")
    print("📖 Visit http://127.0.0.1:8080/demo for interactive testing")
    print("🔄 Press Ctrl+C to stop")
    print("")
    
    app.run(port=8080, production=False)
