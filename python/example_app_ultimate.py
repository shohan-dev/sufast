"""
Ultra-Fast Sufast v2.0 Example
This demonstrates the three-tier optimization system:
- Static routes: High performance (pre-compiled responses)
- Cached routes: Medium performance (intelligent caching)
- Dynamic routes: Standard performance (real-time processing with parameters)
Modern web framework with zero overhead!
"""

import json
from sufast import Sufast

# Create the ultimate optimized application
app = Sufast()

# ========================
# ENHANCED DUMMY DATA
# ========================

USERS_DB = {
    1: {"id": 1, "name": "Alice Johnson", "email": "alice@example.com", "role": "admin", "department": "Engineering", "joined": "2024-01-15"},
    2: {"id": 2, "name": "Bob Smith", "email": "bob@example.com", "role": "user", "department": "Marketing", "joined": "2024-02-20"},
    3: {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com", "role": "user", "department": "Sales", "joined": "2024-03-10"},
    4: {"id": 4, "name": "Diana Prince", "email": "diana@example.com", "role": "moderator", "department": "Support", "joined": "2024-01-30"},
    5: {"id": 5, "name": "Eve Wilson", "email": "eve@example.com", "role": "user", "department": "Engineering", "joined": "2024-04-05"}
}

PRODUCTS_DB = {
    1: {"id": 1, "name": "UltraBook Pro", "price": 1299.99, "category": "electronics", "stock": 15, "rating": 4.8, "reviews": 324},
    2: {"id": 2, "name": "Precision Mouse X1", "price": 29.99, "category": "electronics", "stock": 100, "rating": 4.5, "reviews": 89},
    3: {"id": 3, "name": "Python Mastery Guide", "price": 49.99, "category": "books", "stock": 25, "rating": 4.9, "reviews": 156},
    4: {"id": 4, "name": "ErgoChair Elite", "price": 299.99, "category": "furniture", "stock": 8, "rating": 4.7, "reviews": 67},
    5: {"id": 5, "name": "DevCoder Mug", "price": 12.99, "category": "kitchen", "stock": 50, "rating": 4.3, "reviews": 23}
}

POSTS_DB = {
    "ultimate-rust-performance": {
        "slug": "ultimate-rust-performance",
        "title": "Ultimate Rust Performance Techniques",
        "content": "Discover advanced Rust optimization techniques for maximum performance...",
        "author": "Alice Johnson",
        "published": "2025-01-15",
        "tags": ["rust", "performance", "optimization"],
        "views": 1542,
        "likes": 89
    },
    "python-async-mastery": {
        "slug": "python-async-mastery", 
        "title": "Mastering Python Async Programming",
        "content": "A comprehensive guide to asynchronous programming in Python...",
        "author": "Bob Smith",
        "published": "2025-01-10", 
        "tags": ["python", "async", "programming"],
        "views": 2341,
        "likes": 156
    },
    "sufast-three-tier-architecture": {
        "slug": "sufast-three-tier-architecture",
        "title": "Sufast Three-Tier Performance Architecture", 
        "content": "Learn how Sufast achieves 52K+ RPS with intelligent three-tier optimization...",
        "author": "Diana Prince",
        "published": "2025-01-20",
        "tags": ["sufast", "architecture", "performance"],
        "views": 897,
        "likes": 78
    }
}

CATEGORIES_DB = {
    "electronics": {"name": "Electronics", "description": "Latest electronic devices and accessories", "product_count": 2},
    "books": {"name": "Books", "description": "Programming and technical books", "product_count": 1},
    "furniture": {"name": "Furniture", "description": "Office and home furniture", "product_count": 1},
    "kitchen": {"name": "Kitchen", "description": "Kitchen appliances and accessories", "product_count": 1}
}

# Helper functions
def json_response(data, status=200):
    """Helper function to create optimized JSON responses"""
    if isinstance(data, str):
        return {"body": data, "status": status, "headers": {"Content-Type": "text/plain"}}
    return {"body": json.dumps(data), "status": status, "headers": {"Content-Type": "application/json"}}

# ========================
# TIER 1: STATIC ROUTES (52K+ RPS)
# Pre-compiled responses for maximum performance
# ========================

@app.route('/', static=True)
def home():
    """Ultimate home page - pre-compiled static route (52K+ RPS)."""
    return {
        'message': '🚀 Welcome to Sufast Ultimate v2.0!',
        'framework': 'Three-Tier Hybrid Architecture',
        'version': '2.0.0',
        'performance': {
            'tier_1_static': '70,000+ RPS (pre-compiled)',
            'tier_2_cached': '60,000+ RPS (intelligent cache)', 
            'tier_3_dynamic': '5,000+ RPS (real-time)'
        },
        'optimization': 'Ultimate Performance Mode',
        'features': [
            'Pre-compiled static responses',
            'Intelligent response caching',
            'Real-time dynamic routing',
            'Parameter extraction',
            'Ultra-fast Rust core',
            'Python developer experience'
        ],
        'architecture': {
            'core': 'Rust (Axum + DashMap)',
            'interface': 'Python (ctypes FFI)',
            'performance': 'Three-tier optimization'
        }
    }

@app.route('/about', static=True)
def about():
    """About page - pre-compiled static route (52K+ RPS)."""
    return {
        'page': 'about',
        'framework': 'Sufast Ultimate v2.0',
        'architecture': 'Three-Tier Performance System',
        'performance': 'Static route - 52,000+ RPS',
        'optimization': 'Pre-compiled response',
        'tiers': {
            'tier_1': {
                'name': 'Static Routes',
                'performance': '52,000+ RPS',
                'method': 'Pre-compiled responses',
                'use_case': 'Fixed content, maximum speed'
            },
            'tier_2': {
                'name': 'Cached Routes', 
                'performance': '45,000+ RPS',
                'method': 'Intelligent caching',
                'use_case': 'Semi-static content with TTL'
            },
            'tier_3': {
                'name': 'Dynamic Routes',
                'performance': '2,000+ RPS', 
                'method': 'Real-time processing',
                'use_case': 'Parameter-based content'
            }
        }
    }

@app.route('/contact', static=True)
def contact():
    """Contact page - pre-compiled static route (52K+ RPS)."""
    return {
        'page': 'contact',
        'message': 'Contact the Sufast Ultimate Team',
        'performance': 'Static route - 52,000+ RPS',
        'contact_info': {
            'email': 'hello@sufast.dev',
            'github': 'https://github.com/shohan-dev/sufast',
            'documentation': 'https://docs.sufast.dev',
            'support': 'GitHub Issues & Discussions'
        },
        'response_time': 'Sub-millisecond (pre-compiled)'
    }

@app.route('/health', static=True)
def health():
    """Health check - pre-compiled static route (52K+ RPS)."""
    return {
        'status': 'healthy',
        'service': 'Sufast Ultimate v2.0',
        'performance': 'Static route - 52,000+ RPS',
        'optimization': 'Pre-compiled response',
        'uptime': '99.9%',
        'response_time': 'Sub-millisecond'
    }

# ========================
# TIER 2: CACHED ROUTES (45K+ RPS)
# Intelligent caching with TTL
# ========================

@app.route('/categories', cache_ttl=300)  # 5 minutes cache
def list_categories():
    """Categories list - cached route (45K+ RPS)."""
    return {
        'route_type': 'cached',
        'performance': '45,000+ RPS (cached)',
        'cache_ttl': '300 seconds',
        'categories': CATEGORIES_DB,
        'total_categories': len(CATEGORIES_DB),
        'total_products': sum(cat['product_count'] for cat in CATEGORIES_DB.values()),
        'cache_benefit': 'Fast access to frequently requested data'
    }

@app.route('/stats', cache_ttl=60)  # 1 minute cache
def get_stats():
    """Performance statistics - cached route (45K+ RPS)."""
    stats = app.get_ultimate_performance_stats()
    
    return {
        'route_type': 'cached',
        'performance': '45,000+ RPS (cached)',
        'cache_ttl': '60 seconds',
        'system_stats': stats,
        'data_summary': {
            'users': len(USERS_DB),
            'products': len(PRODUCTS_DB), 
            'posts': len(POSTS_DB),
            'categories': len(CATEGORIES_DB)
        },
        'message': 'Real-time performance metrics (cached for efficiency)'
    }

# ========================
# TIER 3: DYNAMIC ROUTES (2K+ RPS)
# Real-time processing with parameters
# ========================

@app.route('/user/{user_id}')
def get_user(user_id):
    """Get user by ID - dynamic route with parameter (2K+ RPS)."""
    try:
        user_id = int(user_id)
        user = USERS_DB.get(user_id)

        if user:
            return {
                'route_type': 'dynamic',
                'performance': '2,000+ RPS (real-time)',
                'pattern': '/user/{user_id}',
                'extracted_param': {'user_id': user_id},
                'user': user,
                'message': f'Hello, {user["name"]}! Welcome to Sufast Ultimate.',
                'profile_completion': '85%',
                'last_login': '2025-01-18T10:30:00Z',
                'related_links': {
                    'edit_profile': f'/user/{user_id}/edit',
                    'user_posts': f'/user/{user_id}/posts',
                    'department': f'/department/{user["department"].lower()}'
                }
            }
        else:
            return json_response({
                'error': 'User not found',
                'user_id': user_id,
                'available_users': list(USERS_DB.keys()),
                'suggestion': 'Try user IDs 1-5 for demo data'
            }, status=404)
    except ValueError:
        return json_response({
            'error': 'Invalid user ID format',
            'provided': user_id,
            'expected': 'Integer (1, 2, 3, etc.)',
            'available_users': list(USERS_DB.keys())
        }, status=400)

@app.route('/product/{product_id}')
def get_product(product_id):
    """Get product by ID - dynamic route with parameter (2K+ RPS)."""
    try:
        product_id = int(product_id)
        product = PRODUCTS_DB.get(product_id)
        
        if product:
            # Calculate dynamic data
            discount = 0.1 if product['stock'] > 50 else 0.05
            discounted_price = product['price'] * (1 - discount)
            
            return {
                'route_type': 'dynamic',
                'performance': '2,000+ RPS (real-time)',
                'pattern': '/product/{product_id}',
                'extracted_param': {'product_id': product_id},
                'product': product,
                'pricing': {
                    'original_price': product['price'],
                    'discount': f'{discount * 100}%',
                    'discounted_price': round(discounted_price, 2)
                },
                'availability': {
                    'in_stock': product['stock'] > 0,
                    'stock_level': 'High' if product['stock'] > 20 else 'Medium' if product['stock'] > 5 else 'Low',
                    'estimated_delivery': '2-3 business days'
                },
                'related_links': {
                    'category': f'/category/{product["category"]}',
                    'reviews': f'/product/{product_id}/reviews',
                    'similar': f'/category/{product["category"]}/similar/{product_id}'
                }
            }
        else:
            return json_response({
                'error': 'Product not found',
                'product_id': product_id,
                'available_products': list(PRODUCTS_DB.keys()),
                'suggestion': 'Try product IDs 1-5 for demo data'
            }, status=404)
    except ValueError:
        return json_response({
            'error': 'Invalid product ID format',
            'provided': product_id,
            'expected': 'Integer (1, 2, 3, etc.)',
            'available_products': list(PRODUCTS_DB.keys())
        }, status=400)

@app.route('/post/{slug}')
def get_post(slug):
    """Get post by slug - dynamic route with slug parameter (2K+ RPS)."""
    post = POSTS_DB.get(slug)
    
    if post:
        # Calculate dynamic metrics
        read_time = max(1, len(post['content'].split()) // 200)
        engagement_rate = (post['likes'] / max(post['views'], 1)) * 100
        
        return {
            'route_type': 'dynamic',
            'performance': '2,000+ RPS (real-time)',
            'pattern': '/post/{slug}',
            'extracted_param': {'slug': slug},
            'post': post,
            'reading_info': {
                'word_count': len(post['content'].split()),
                'read_time_minutes': read_time,
                'difficulty': 'Intermediate'
            },
            'engagement': {
                'views': post['views'],
                'likes': post['likes'],
                'engagement_rate': f'{engagement_rate:.1f}%'
            },
            'related_links': {
                'author_profile': f'/author/{post["author"].lower().replace(" ", "-")}',
                'tag_search': f'/search/tags/{"+".join(post["tags"])}',
                'related_posts': f'/posts/related/{slug}'
            }
        }
    else:
        return json_response({
            'error': 'Post not found',
            'slug': slug,
            'available_posts': list(POSTS_DB.keys()),
            'suggestion': 'Try available post slugs for demo content'
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
                'category': category,
                'available_categories': list(CATEGORIES_DB.keys())
            }, status=404)
        
        if not product:
            return json_response({
                'error': 'Product not found',
                'product_id': product_id,
                'available_products': list(PRODUCTS_DB.keys())
            }, status=404)
        
        if product['category'] != category:
            return json_response({
                'error': 'Product not in specified category',
                'product_category': product['category'],
                'requested_category': category,
                'correct_url': f'/category/{product["category"]}/product/{product_id}'
            }, status=400)
        
        # Find related products in same category
        related_products = [
            {'id': pid, 'name': p['name'], 'price': p['price']} 
            for pid, p in PRODUCTS_DB.items() 
            if p['category'] == category and pid != product_id
        ]
        
        return {
            'route_type': 'dynamic',
            'performance': '2,000+ RPS (real-time)',
            'pattern': '/category/{category}/product/{product_id}',
            'extracted_params': {'category': category, 'product_id': product_id},
            'category': category_info,
            'product': product,
            'breadcrumb': [
                {'name': 'Home', 'url': '/'},
                {'name': category_info['name'], 'url': f'/category/{category}'},
                {'name': product['name'], 'url': f'/category/{category}/product/{product_id}'}
            ],
            'related_products': related_products,
            'category_stats': {
                'total_products': len(related_products) + 1,
                'avg_price': round(sum(p['price'] for p in PRODUCTS_DB.values() if p['category'] == category) / max(len(related_products) + 1, 1), 2)
            }
        }
    except ValueError:
        return json_response({
            'error': 'Invalid product ID format',
            'provided': product_id,
            'expected': 'Integer (1, 2, 3, etc.)'
        }, status=400)

@app.route('/search/{query}')
def search(query):
    """Advanced search - dynamic route with query processing (2K+ RPS)."""
    results = []
    query_lower = query.lower()
    
    # Search users
    for user in USERS_DB.values():
        if (query_lower in user['name'].lower() or 
            query_lower in user['email'].lower() or 
            query_lower in user['department'].lower()):
            results.append({
                'type': 'user',
                'id': user['id'],
                'title': user['name'],
                'description': f"{user['role']} in {user['department']}",
                'url': f'/user/{user["id"]}',
                'relevance': 0.9
            })
    
    # Search products
    for product in PRODUCTS_DB.values():
        if (query_lower in product['name'].lower() or 
            query_lower in product['category'].lower()):
            results.append({
                'type': 'product',
                'id': product['id'],
                'title': product['name'],
                'description': f"${product['price']} - {product['category']}",
                'url': f'/product/{product["id"]}',
                'relevance': 0.8
            })
    
    # Search posts
    for post in POSTS_DB.values():
        if (query_lower in post['title'].lower() or 
            query_lower in post['content'].lower() or
            any(query_lower in tag.lower() for tag in post['tags'])):
            results.append({
                'type': 'post',
                'id': post['slug'],
                'title': post['title'],
                'description': f"By {post['author']} - {post['views']} views",
                'url': f'/post/{post["slug"]}',
                'relevance': 0.7
            })
    
    # Sort by relevance
    results.sort(key=lambda x: x['relevance'], reverse=True)
    
    return {
        'route_type': 'dynamic_search',
        'performance': '2,000+ RPS (real-time)',
        'pattern': '/search/{query}',
        'extracted_param': {'query': query},
        'search_results': {
            'query': query,
            'results': results,
            'total_found': len(results),
            'search_time_ms': '< 1ms (in-memory)',
            'categories': {
                'users': len([r for r in results if r['type'] == 'user']),
                'products': len([r for r in results if r['type'] == 'product']),
                'posts': len([r for r in results if r['type'] == 'post'])
            }
        },
        'suggestions': {
            'try_queries': ['python', 'alice', 'electronics', 'chair'],
            'advanced_search': '/search/advanced',
            'filters': f'/search/{query}?type=product&category=electronics'
        }
    }

@app.route('/category/{category}')
def get_category(category):
    """Get category with products - dynamic route (2K+ RPS)."""
    category_info = CATEGORIES_DB.get(category)
    
    if not category_info:
        return json_response({
            'error': 'Category not found',
            'category': category,
            'available_categories': list(CATEGORIES_DB.keys()),
            'suggestion': 'Try: electronics, books, furniture, kitchen'
        }, status=404)
    
    # Get all products in this category
    products = [
        {**product, 'url': f'/category/{category}/product/{product["id"]}'}
        for product in PRODUCTS_DB.values() 
        if product['category'] == category
    ]
    
    return {
        'route_type': 'dynamic',
        'performance': '2,000+ RPS (real-time)',
        'pattern': '/category/{category}',
        'extracted_param': {'category': category},
        'category': category_info,
        'products': products,
        'category_stats': {
            'total_products': len(products),
            'price_range': {
                'min': min(p['price'] for p in products) if products else 0,
                'max': max(p['price'] for p in products) if products else 0,
                'average': round(sum(p['price'] for p in products) / max(len(products), 1), 2)
            },
            'stock_total': sum(p['stock'] for p in products)
        },
        'navigation': {
            'all_categories': '/categories',
            'search_category': f'/search/{category}',
            'category_products': [f'/category/{category}/product/{p["id"]}' for p in products[:3]]
        }
    }

# ========================
# DEMO AND TESTING ROUTES
# ========================
@app.route('/fine', static=True)
def fine():
    """Fine-tuning demo - static route (52K+ RPS)."""
    return {
        'message': '🎉 Sufast Ultimate v2.0 is running smoothly!',
        'performance': 'Static route - 52,000+ RPS',
        'optimization': 'Pre-compiled response',
        'status': 'All systems operational',
        'next_steps': [
            'Explore the /demo route for interactive testing',
            'Check /docs for auto-generated documentation',
            'Visit /categories for cached data'
        ]
    }



@app.route('/demo')
def demo():
    """Interactive demo page - dynamic route (2K+ RPS)."""
    return {
        'route_type': 'dynamic',
        'performance': '2,000+ RPS (real-time)',
        'message': '🎮 Sufast Ultimate v2.0 Interactive Demo',
        'test_endpoints': {
            'static_routes': {
                'description': '52,000+ RPS - Pre-compiled responses',
                'endpoints': [
                    {'url': '/', 'description': 'Home page'},
                    {'url': '/about', 'description': 'Framework info'},
                    {'url': '/contact', 'description': 'Contact info'},
                    {'url': '/health', 'description': 'Health check'}
                ]
            },
            'cached_routes': {
                'description': '45,000+ RPS - Intelligent caching',
                'endpoints': [
                    {'url': '/categories', 'description': 'Categories list (5min cache)'},
                    {'url': '/stats', 'description': 'Performance stats (1min cache)'}
                ]
            },
            'dynamic_routes': {
                'description': '2,000+ RPS - Real-time processing',
                'endpoints': [
                    {'url': '/user/1', 'description': 'User profile (Alice)'},
                    {'url': '/product/1', 'description': 'Product details (UltraBook)'},
                    {'url': '/post/ultimate-rust-performance', 'description': 'Blog post'},
                    {'url': '/category/electronics/product/1', 'description': 'Product in category'},
                    {'url': '/search/python', 'description': 'Search functionality'},
                    {'url': '/category/electronics', 'description': 'Category listing'}
                ]
            }
        },
        'performance_tip': 'Try hitting the same route multiple times to see caching in action!',
        'architecture_info': 'Each tier is optimized for different use cases and performance characteristics.'
    }

# ========================
# DOCUMENTATION IS AUTO-GENERATED!
# The /docs route is automatically available - no setup needed!
# Just like FastAPI, visit /docs to see all your routes
# ========================

if __name__ == "__main__":
    # 🎉 Documentation is automatically available at /docs
    # No need to manually create or enable it - it's built into the framework!
    
    
    # Just run the server - /docs is automatically available
    app.run(host="127.0.0.1", port=8080, doc=True)
