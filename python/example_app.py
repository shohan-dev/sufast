"""
Ultra-Optimized Sufast v2.0 Example - Testing Static and Dynamic Routes
This demonstrates the three-tier optimization system:
- Static routes (52K+ RPS)
- Cached routes (45K+ RPS) 
- Dynamic routing with parameters (2K+ RPS)
- Simple JSON responses
- Basic error handling
"""

from sufast import SufastUltraOptimized, create_app

# Create the ultra-optimized application
app = SufastUltraOptimized()

# Dummy data for testing
USERS_DB = {
    1: {"id": 1, "name": "Alice Johnson", "email": "alice@example.com", "role": "admin"},
    2: {"id": 2, "name": "Bob Smith", "email": "bob@example.com", "role": "user"},
    3: {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com", "role": "user"},
    4: {"id": 4, "name": "Diana Prince", "email": "diana@example.com", "role": "moderator"},
    5: {"id": 5, "name": "Eve Wilson", "email": "eve@example.com", "role": "user"}
}

PRODUCTS_DB = {
    1: {"id": 1, "name": "Laptop Pro", "price": 1299.99, "category": "electronics", "stock": 15},
    2: {"id": 2, "name": "Wireless Mouse", "price": 29.99, "category": "electronics", "stock": 100},
    3: {"id": 3, "name": "Python Programming Book", "price": 49.99, "category": "books", "stock": 25},
    4: {"id": 4, "name": "Gaming Chair", "price": 299.99, "category": "furniture", "stock": 8},
    5: {"id": 5, "name": "Coffee Mug", "price": 12.99, "category": "kitchen", "stock": 50}
}

POSTS_DB = {
    "getting-started-with-rust": {
        "slug": "getting-started-with-rust",
        "title": "Getting Started with Rust",
        "content": "Rust is a systems programming language that runs blazingly fast...",
        "author": "Alice Johnson",
        "published": "2025-01-15",
        "tags": ["rust", "programming", "tutorial"]
    },
    "python-web-frameworks": {
        "slug": "python-web-frameworks", 
        "title": "Python Web Frameworks Comparison",
        "content": "A comprehensive comparison of modern Python web frameworks...",
        "author": "Bob Smith",
        "published": "2025-01-10", 
        "tags": ["python", "web", "frameworks"]
    },
    "sufast-performance-guide": {
        "slug": "sufast-performance-guide",
        "title": "Sufast Performance Optimization Guide", 
        "content": "Learn how to optimize your Sufast applications for maximum performance...",
        "author": "Diana Prince",
        "published": "2025-01-20",
        "tags": ["sufast", "performance", "optimization"]
    }
}

CATEGORIES_DB = {
    "electronics": {"name": "Electronics", "description": "Electronic devices and accessories"},
    "books": {"name": "Books", "description": "Programming and technical books"},
    "furniture": {"name": "Furniture", "description": "Office and home furniture"},
    "kitchen": {"name": "Kitchen", "description": "Kitchen appliances and accessories"}
}

# Helper functions for responses
def json_response(data, status=200):
    """Helper function to create JSON responses"""
    import json
    if isinstance(data, str):
        return {"body": data, "status": status, "headers": {"Content-Type": "text/plain"}}
    return {"body": json.dumps(data), "status": status, "headers": {"Content-Type": "application/json"}}

def html_response(html_content, status=200):
    """Helper function to create HTML responses"""
    return {"body": html_content, "status": status, "headers": {"Content-Type": "text/html"}}

# ========================
# STATIC ROUTES (52K+ RPS)
# ========================

@app.route('/')
def home():
    """Home page - ultra-fast static route (52K+ RPS)."""
    return json_response({
        'message': '🚀 Welcome to Sufast Ultra-Optimized v2.0!',
        'framework': 'Hybrid Rust+Python',
        'version': '2.0.0',
        'performance': {
            'static_routes': '52,000+ RPS',
            'cached_routes': '45,000+ RPS', 
            'dynamic_routes': '2,000+ RPS'
        },
        'features': [
            'Three-tier optimization system',
            'Ultra-fast static routes',
            'Intelligent response caching',
            'Dynamic routes with parameters',
            'High-performance Rust core',
            'Python developer experience'
        ],
        'test_routes': {
            'static': [
                'GET /',
                'GET /about',
                'GET /contact',
                'GET /health'
            ],
            'dynamic': [
                'GET /user/{id}',
                'GET /product/{id}',
                'GET /post/{slug}',
                'GET /category/{cat}/product/{id}'
            ]
        },
        'dummy_data': {
            'users': len(USERS_DB),
            'products': len(PRODUCTS_DB),
            'posts': len(POSTS_DB),
            'categories': len(CATEGORIES_DB)
        }
    })

@app.route('/about')
def about():
    """About page - ultra-fast static route (52K+ RPS)."""
    return json_response({
        'page': 'about',
        'message': 'About Sufast Ultra-Optimized Framework',
        'framework_info': {
            'name': 'Sufast',
            'version': '2.0.0',
            'architecture': 'Three-Tier Optimization',
            'backend': 'Rust (Ultra Performance)',
            'frontend': 'Python (Developer Friendly)',
            'performance_tiers': {
                'tier_1': 'Static Routes - 52,000+ RPS',
                'tier_2': 'Cached Routes - 45,000+ RPS',
                'tier_3': 'Dynamic Routes - 2,000+ RPS'
            }
        },
        'advantages': [
            'Blazing fast static content delivery',
            'Intelligent response caching',
            'Memory-efficient route handling',
            'Automatic performance optimization',
            'Python-friendly development experience'
        ]
    })

@app.route('/contact')
def contact():
    """Contact page - ultra-fast static route (52K+ RPS)."""
    return json_response({
        'page': 'contact',
        'message': 'Contact the Sufast Team',
        'contact_info': {
            'email': 'hello@sufast.dev',
            'github': 'https://github.com/shohan-dev/sufast',
            'twitter': '@sufast_dev',
            'discord': 'discord.gg/sufast'
        },
        'support': {
            'documentation': 'https://docs.sufast.dev',
            'issues': 'https://github.com/shohan-dev/sufast/issues',
            'discussions': 'https://github.com/shohan-dev/sufast/discussions'
        }
    })

@app.route('/health')
def health():
    """Health check endpoint - ultra-fast static route (52K+ RPS)."""
    return json_response({
        'status': 'healthy',
        'service': 'Sufast Ultra-Optimized',
        'version': '2.0.0',
        'timestamp': '2025-07-18T12:00:00Z',
        'performance_tier': 'static (52K+ RPS)',
        'uptime': '99.9%'
    })

# ========================
# DYNAMIC ROUTES (2K+ RPS)
# ========================

@app.route('/user/{user_id}')
def get_user(user_id):
    """Get user by ID - dynamic route with single parameter (2K+ RPS)."""
    try:
        user_id = int(user_id)
        user = USERS_DB.get(user_id)

        print(f"User lookup: {user_id} -> {user}")

        if user:
            return json_response({
                'route_type': 'dynamic',
                'performance_tier': '2,000+ RPS',
                'pattern': '/user/{user_id}',
                'user': user,
                'message': f'Hello, this is user {user["name"]}!',
                'profile_url': f'/user/{user_id}/profile'
            })
        else:
            return json_response({
                'error': 'User not found',
                'available_users': list(USERS_DB.keys()),
                'message': f'User {user_id} does not exist'
            }, status=404)
    except ValueError:
        return json_response({
            'error': 'Invalid user ID',
            'message': 'User ID must be a number',
            'available_users': list(USERS_DB.keys())
        }, status=400)

@app.route('/product/{product_id}')
def get_product(product_id):
    """Get product by ID - dynamic route with single parameter (2K+ RPS)."""
    try:
        product_id = int(product_id)
        product = PRODUCTS_DB.get(product_id)
        
        if product:
            return json_response({
                'route_type': 'dynamic',
                'performance_tier': '2,000+ RPS',
                'pattern': '/product/{product_id}',
                'product': product,
                'stock_status': 'In Stock' if product['stock'] > 0 else 'Out of Stock',
                'category_url': f'/category/{product["category"]}',
                'message': f'Product {product["name"]} details retrieved'
            })
        else:
            return json_response({
                'error': 'Product not found',
                'available_products': list(PRODUCTS_DB.keys()),
                'message': f'Product {product_id} does not exist'
            }, status=404)
    except ValueError:
        return json_response({
            'error': 'Invalid product ID',
            'message': 'Product ID must be a number',
            'available_products': list(PRODUCTS_DB.keys())
        }, status=400)

@app.route('/post/{slug}')
def get_post(slug):
    """Get post by slug - dynamic route with slug parameter (2K+ RPS)."""
    post = POSTS_DB.get(slug)
    
    if post:
        return json_response({
            'route_type': 'dynamic',
            'performance_tier': '2,000+ RPS',
            'pattern': '/post/{slug}',
            'post': post,
            'word_count': len(post['content'].split()),
            'read_time': f'{len(post["content"].split()) // 200 + 1} min',
            'author_url': f'/author/{post["author"].lower().replace(" ", "-")}',
            'message': f'Blog post "{post["title"]}" retrieved'
        })
    else:
        return json_response({
            'error': 'Post not found',
            'available_posts': list(POSTS_DB.keys()),
            'message': f'Post "{slug}" does not exist'
        }, status=404)

@app.route('/category/{category}/product/{product_id}')
def get_category_product(category, product_id):
    """Get product in category - dynamic route with multiple parameters (2K+ RPS)."""
    try:
        product_id = int(product_id)
        product = PRODUCTS_DB.get(product_id)
        category_info = CATEGORIES_DB.get(category)
        
        if not category_info:
            return json_response({
                'error': 'Category not found',
                'available_categories': list(CATEGORIES_DB.keys()),
                'message': f'Category "{category}" does not exist'
            }, status=404)
        
        if not product:
            return json_response({
                'error': 'Product not found',
                'available_products': list(PRODUCTS_DB.keys()),
                'message': f'Product {product_id} does not exist'
            }, status=404)
        
        if product['category'] != category:
            return json_response({
                'error': 'Product not in category',
                'product_category': product['category'],
                'requested_category': category,
                'message': f'Product {product_id} is not in {category} category'
            }, status=400)
        
        return json_response({
            'route_type': 'dynamic',
            'performance_tier': '2,000+ RPS',
            'pattern': '/category/{category}/product/{product_id}',
            'category': category_info,
            'product': product,
            'breadcrumb': [
                {'name': 'Home', 'url': '/'},
                {'name': category_info['name'], 'url': f'/category/{category}'},
                {'name': product['name'], 'url': f'/category/{category}/product/{product_id}'}
            ],
            'related_products': [
                {'id': pid, 'name': p['name']} 
                for pid, p in PRODUCTS_DB.items() 
                if p['category'] == category and pid != product_id
            ][:3],
            'message': f'Product {product["name"]} in {category_info["name"]} category'
        })
    except ValueError:
        return json_response({
            'error': 'Invalid product ID',
            'message': 'Product ID must be a number'
        }, status=400)

# ========================
# ROUTES WITH QUERY PARAMETERS
# ========================

@app.route('/search/{query}')
def search(query):
    """Search with query parameters - dynamic route + query params (2K+ RPS)."""
    # Simulate search across all data
    results = []
    
    # Search users
    for user in USERS_DB.values():
        if query.lower() in user['name'].lower() or query.lower() in user['email'].lower():
            results.append({
                'type': 'user',
                'id': user['id'],
                'title': user['name'],
                'description': f"{user['role']} - {user['email']}",
                'url': f'/user/{user["id"]}'
            })
    
    # Search products
    for product in PRODUCTS_DB.values():
        if query.lower() in product['name'].lower() or query.lower() in product['category'].lower():
            results.append({
                'type': 'product',
                'id': product['id'],
                'title': product['name'],
                'description': f"${product['price']} - {product['category']}",
                'url': f'/product/{product["id"]}'
            })
    
    # Search posts
    for post in POSTS_DB.values():
        if (query.lower() in post['title'].lower() or 
            query.lower() in post['content'].lower() or
            any(query.lower() in tag.lower() for tag in post['tags'])):
            results.append({
                'type': 'post',
                'id': post['slug'],
                'title': post['title'],
                'description': f"By {post['author']} - {post['published']}",
                'url': f'/post/{post["slug"]}'
            })
    
    return json_response({
        'route_type': 'dynamic_with_search',
        'performance_tier': '2,000+ RPS',
        'pattern': '/search/{query}',
        'search_query': query,
        'results': results,
        'total_results': len(results),
        'search_stats': {
            'users_found': len([r for r in results if r['type'] == 'user']),
            'products_found': len([r for r in results if r['type'] == 'product']),
            'posts_found': len([r for r in results if r['type'] == 'post'])
        },
        'message': f'Found {len(results)} results for "{query}"'
    })

# ========================
# CATEGORY LISTING ROUTES  
# ========================

@app.route('/category/{category}')
def get_category(category):
    """Get category with products - dynamic route (2K+ RPS)."""
    category_info = CATEGORIES_DB.get(category)
    
    if not category_info:
        return json_response({
            'error': 'Category not found',
            'available_categories': list(CATEGORIES_DB.keys()),
            'message': f'Category "{category}" does not exist'
        }, status=404)
    
    # Get all products in this category
    products = [
        product for product in PRODUCTS_DB.values() 
        if product['category'] == category
    ]
    
    return json_response({
        'route_type': 'dynamic',
        'performance_tier': '2,000+ RPS',
        'pattern': '/category/{category}',
        'category': category_info,
        'products': products,
        'product_count': len(products),
        'total_stock': sum(p['stock'] for p in products),
        'price_range': {
            'min': min((p['price'] for p in products), default=0),
            'max': max((p['price'] for p in products), default=0)
        },
        'message': f'{category_info["name"]} category with {len(products)} products'
    })

@app.route('/categories')
def list_categories():
    """List all categories - cached route (45K+ RPS)."""
    return json_response({
        'route_type': 'cached',
        'performance_tier': '45,000+ RPS',
        'categories': CATEGORIES_DB,
        'category_stats': {
            category: len([p for p in PRODUCTS_DB.values() if p['category'] == category])
            for category in CATEGORIES_DB.keys()
        },
        'total_categories': len(CATEGORIES_DB),
        'message': 'All categories listed'
    })

# ========================
# DEMO AND INFO ROUTES
# ========================

@app.route('/demo')
def demo_page():
    """Interactive demo page - cached route (45K+ RPS)."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sufast Ultra-Optimized v2.0 Demo</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #333; }
            .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
            .header { text-align: center; margin-bottom: 30px; }
            h1 { color: #2c3e50; border-bottom: 3px solid #e74c3c; padding-bottom: 10px; margin-bottom: 5px; }
            .performance-badge { background: linear-gradient(45deg, #ff6b6b, #feca57); color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; display: inline-block; margin: 10px 0; }
            .section { margin: 25px 0; padding: 20px; background: #f8f9fa; border-radius: 10px; border-left: 5px solid #3498db; }
            .static { border-left-color: #27ae60; }
            .cached { border-left-color: #f39c12; }
            .dynamic { border-left-color: #3498db; }
            .test-link { display: inline-block; margin: 5px; padding: 10px 15px; background: #3498db; color: white; text-decoration: none; border-radius: 8px; font-size: 14px; transition: all 0.3s; }
            .test-link:hover { background: #2980b9; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
            .static-link { background: #27ae60; }
            .static-link:hover { background: #219a52; }
            .cached-link { background: #f39c12; }
            .cached-link:hover { background: #e67e22; }
            .dynamic-link { background: #3498db; }
            .dynamic-link:hover { background: #2980b9; }
            .performance-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
            .stat-card { background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .stat-number { font-size: 24px; font-weight: bold; color: #e74c3c; }
            .stat-label { color: #7f8c8d; font-size: 14px; }
            code { background: #34495e; color: #ecf0f1; padding: 3px 8px; border-radius: 4px; font-family: 'Courier New', monospace; }
            .data-preview { background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 8px; margin: 10px 0; max-height: 200px; overflow-y: auto; }
            #result { background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 8px; min-height: 100px; white-space: pre-wrap; font-family: 'Courier New', monospace; font-size: 12px; }
        </style>
        <script>
            function testRoute(url) {
                fetch(url)
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('result').textContent = JSON.stringify(data, null, 2);
                    })
                    .catch(error => {
                        document.getElementById('result').textContent = 'Error: ' + error;
                    });
            }
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Sufast Ultra-Optimized v2.0</h1>
                <div class="performance-badge">Three-Tier Performance Architecture</div>
                <p>Test the ultra-optimized three-tier routing system with real dummy data!</p>
            </div>
            
            <div class="performance-stats">
                <div class="stat-card">
                    <div class="stat-number">52K+</div>
                    <div class="stat-label">Static Route RPS</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">45K+</div>
                    <div class="stat-label">Cached Route RPS</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">2K+</div>
                    <div class="stat-label">Dynamic Route RPS</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">🦀</div>
                    <div class="stat-label">Rust Core</div>
                </div>
            </div>
            
            <div class="section static">
                <h3>⚡ Static Routes (52,000+ RPS)</h3>
                <p>Ultra-fast pre-compiled responses with maximum performance:</p>
                <a href="/" onclick="testRoute('/'); return false;" class="test-link static-link">GET /</a>
                <a href="/about" onclick="testRoute('/about'); return false;" class="test-link static-link">GET /about</a>
                <a href="/contact" onclick="testRoute('/contact'); return false;" class="test-link static-link">GET /contact</a>
                <a href="/health" onclick="testRoute('/health'); return false;" class="test-link static-link">GET /health</a>
            </div>
            
            <div class="section cached">
                <h3>� Cached Routes (45,000+ RPS)</h3>
                <p>Intelligent caching with automatic optimization:</p>
                <a href="/categories" onclick="testRoute('/categories'); return false;" class="test-link cached-link">GET /categories</a>
            </div>
            
            <div class="section dynamic">
                <h3>🔗 Dynamic Routes (2,000+ RPS)</h3>
                <p>Real-time processing with dummy data:</p>
                <div style="margin: 10px 0;">
                    <strong>Users:</strong>
                    <a href="/user/1" onclick="testRoute('/user/1'); return false;" class="test-link dynamic-link">Alice</a>
                    <a href="/user/2" onclick="testRoute('/user/2'); return false;" class="test-link dynamic-link">Bob</a>
                    <a href="/user/3" onclick="testRoute('/user/3'); return false;" class="test-link dynamic-link">Charlie</a>
                </div>
                <div style="margin: 10px 0;">
                    <strong>Products:</strong>
                    <a href="/product/1" onclick="testRoute('/product/1'); return false;" class="test-link dynamic-link">Laptop</a>
                    <a href="/product/2" onclick="testRoute('/product/2'); return false;" class="test-link dynamic-link">Mouse</a>
                    <a href="/product/3" onclick="testRoute('/product/3'); return false;" class="test-link dynamic-link">Book</a>
                </div>
                <div style="margin: 10px 0;">
                    <strong>Posts:</strong>
                    <a href="/post/getting-started-with-rust" onclick="testRoute('/post/getting-started-with-rust'); return false;" class="test-link dynamic-link">Rust Guide</a>
                    <a href="/post/python-web-frameworks" onclick="testRoute('/post/python-web-frameworks'); return false;" class="test-link dynamic-link">Python Frameworks</a>
                </div>
            </div>
            
            <div class="section dynamic">
                <h3>🏷️ Category + Product Routes</h3>
                <p>Multi-parameter routes with validation:</p>
                <a href="/category/electronics" onclick="testRoute('/category/electronics'); return false;" class="test-link dynamic-link">Electronics Category</a>
                <a href="/category/electronics/product/1" onclick="testRoute('/category/electronics/product/1'); return false;" class="test-link dynamic-link">Electronics → Laptop</a>
                <a href="/category/books/product/3" onclick="testRoute('/category/books/product/3'); return false;" class="test-link dynamic-link">Books → Python Book</a>
            </div>
            
            <div class="section dynamic">
                <h3>� Search Routes</h3>
                <p>Full-text search across all data types:</p>
                <a href="/search/python" onclick="testRoute('/search/python'); return false;" class="test-link dynamic-link">Search "python"</a>
                <a href="/search/alice" onclick="testRoute('/search/alice'); return false;" class="test-link dynamic-link">Search "alice"</a>
                <a href="/search/laptop" onclick="testRoute('/search/laptop'); return false;" class="test-link dynamic-link">Search "laptop"</a>
            </div>
            
            <div class="section">
                <h3>📊 Live Response</h3>
                <div id="result">Click any link above to see the JSON response here...</div>
            </div>
            
            <div class="section">
                <h3>💾 Dummy Data Preview</h3>
                <div class="data-preview">
Users: Alice, Bob, Charlie, Diana, Eve
Products: Laptop Pro, Wireless Mouse, Python Book, Gaming Chair, Coffee Mug  
Posts: Getting Started with Rust, Python Web Frameworks, Sufast Performance Guide
Categories: Electronics, Books, Furniture, Kitchen
                </div>
            </div>
            
            <div class="section">
                <h3>✅ What's Being Tested</h3>
                <ul>
                    <li><strong>🔥 Ultra Performance:</strong> 52K+ RPS static routes with Rust core</li>
                    <li><strong>🧠 Intelligent Caching:</strong> 45K+ RPS cached responses</li>
                    <li><strong>⚡ Dynamic Processing:</strong> 2K+ RPS with real data lookup</li>
                    <li><strong>🔧 Parameter Extraction:</strong> URL path parameters like <code>/user/{id}</code></li>
                    <li><strong>✅ Data Validation:</strong> Type checking and error handling</li>
                    <li><strong>🔍 Search Functionality:</strong> Full-text search across data types</li>
                    <li><strong>🏷️ Multi-Parameter Routes:</strong> Complex patterns like <code>/category/{cat}/product/{id}</code></li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    return html_response(html_content)

@app.route('/stats')
def performance_stats():
    """Performance statistics - cached route (45K+ RPS)."""
    try:
        stats = app.get_performance_stats()
        return json_response({
            'route_type': 'cached',
            'performance_tier': '45,000+ RPS',
            'framework': 'Sufast Ultra-Optimized v2.0',
            'system_stats': stats,
            'dummy_data_counts': {
                'users': len(USERS_DB),
                'products': len(PRODUCTS_DB),
                'posts': len(POSTS_DB),
                'categories': len(CATEGORIES_DB)
            },
            'message': 'Performance statistics retrieved'
        })
    except Exception as e:
        return json_response({
            'error': 'Stats unavailable',
            'message': str(e),
            'fallback_stats': {
                'framework': 'Sufast Ultra-Optimized v2.0',
                'status': 'running'
            }
        })
if __name__ == '__main__':
    print("🚀 Starting Sufast Ultra-Optimized v2.0 Demo Server")
    print("⚡ Three-Tier Performance Architecture Active")
    print("")
    print("📊 Performance Tiers:")
    print("  🔥 Static Routes:  52,000+ RPS (Ultra-fast pre-compiled)")
    print("  🧠 Cached Routes:  45,000+ RPS (Intelligent caching)")  
    print("  ⚡ Dynamic Routes:  2,000+ RPS (Real-time processing)")
    print("")
    print("🌐 Test Endpoints:")
    print("  📍 Static Routes:")
    print("     GET / (home page)")
    print("     GET /about (framework info)")
    print("     GET /contact (contact info)")
    print("     GET /health (health check)")
    print("")
    print("  🧠 Cached Routes:")
    print("     GET /categories (all categories)")
    print("     GET /stats (performance statistics)")
    print("")
    print("  ⚡ Dynamic Routes:")
    print("     GET /user/{id} (user details)")
    print("     GET /product/{id} (product details)")
    print("     GET /post/{slug} (blog post)")
    print("     GET /category/{cat} (category listing)")
    print("     GET /category/{cat}/product/{id} (nested route)")
    print("     GET /search/{query} (full-text search)")
    print("")
    print("💾 Dummy Data Loaded:")
    print(f"     👥 Users: {len(USERS_DB)} (Alice, Bob, Charlie, Diana, Eve)")
    print(f"     � Products: {len(PRODUCTS_DB)} (Laptop, Mouse, Book, Chair, Mug)")
    print(f"     📝 Posts: {len(POSTS_DB)} (Rust, Python, Sufast guides)")
    print(f"     🏷️ Categories: {len(CATEGORIES_DB)} (Electronics, Books, Furniture, Kitchen)")
    print("")
    print("🎨 Interactive Demo:")
    print("     📄 Visit /demo for interactive testing interface")
    print("     📊 Visit /stats for performance metrics")
    print("")
    print("🌐 Server starting on http://127.0.0.1:8080")
    print("� Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        app.run(host="127.0.0.1", port=8080, debug=True)
    except KeyboardInterrupt:
        print("\n� Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        print("💡 Make sure the ultra-optimized Sufast core is properly installed")
