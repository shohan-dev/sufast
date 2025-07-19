"""
Enhanced Sufast Example with Tags and Groups
Demonstrates the new organizational features for better API documentation.
"""

from sufast import Sufast, CORSMiddleware, RateLimitMiddleware, AuthMiddleware
import time
import json

app = Sufast()

# ========================================
# MIDDLEWARE CONFIGURATION
# ========================================

# Add CORS middleware for cross-origin requests
app.add_middleware(CORSMiddleware(
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    allow_credentials=True
))

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware(
    requests_per_minute=100
))

# Custom logging middleware example
class LoggingMiddleware:
    def __init__(self):
        self.request_count = 0
    
    def process_request(self, request):
        self.request_count += 1
        start_time = time.time()
        request.start_time = start_time
        print(f"🔍 [{self.request_count}] {request.method} {request.path} - Started")
        return None  # Continue to next middleware/handler
    
    def process_response(self, request, response):
        duration = time.time() - getattr(request, 'start_time', 0)
        print(f"✅ {request.method} {request.path} - {response.status} ({duration:.3f}s)")
        return response

# Add custom logging middleware
app.add_middleware(LoggingMiddleware())

# Custom authentication middleware for admin routes
class SimpleAuthMiddleware:
    def process_request(self, request):
        # Only protect admin routes
        if request.path.startswith('/admin'):
            auth_header = request.headers.get('authorization', '')
            if not auth_header.startswith('Bearer admin-token'):
                from sufast import json_response
                return json_response({"error": "Authentication required for admin routes"}, 401)
        return None
    
    def process_response(self, request, response):
        # Add security headers
        response.set_header('X-Content-Type-Options', 'nosniff')
        response.set_header('X-Frame-Options', 'DENY')
        return response

# Add authentication middleware
app.add_middleware(SimpleAuthMiddleware())

# Middleware usage tracker
middleware_stats = {
    "total_requests": 0,
    "cors_requests": 0,
    "rate_limited_requests": 0,
    "auth_protected_requests": 0
}

# ========================================
# USING GROUPS FOR ORGANIZATION
# ========================================

# Create route groups for better organization
users_group = app.group("User Management", prefix="/api/v1", tags=["api", "v1"], description="User management endpoints")
products_group = app.group("Product Catalog", prefix="/api/v1", tags=["api", "v1"], description="Product management endpoints")
middleware_group = app.group("Middleware Demo", prefix="/middleware", tags=["demo", "middleware"], description="Middleware functionality demonstrations")

# ========================================
# USER MANAGEMENT GROUP
# ========================================

@users_group.get("/users", 
                 tags=["list", "users"], 
                 summary="List all users",
                 description="Retrieve a paginated list of all users in the system")
def list_users():
    """Get all users with pagination."""
    return {
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"}
        ],
        "pagination": {"page": 1, "total": 2}
    }

@users_group.get("/users/{user_id}", 
                 tags=["get", "users", "profile"], 
                 summary="Get user by ID",
                 description="Retrieve detailed information about a specific user")
def get_user(user_id):
    """Get user by ID with detailed profile information."""
    return {
        "id": int(user_id),
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
        "profile": {"created": "2025-01-01", "last_login": "2025-01-19"}
    }

@users_group.post("/users", 
                  tags=["create", "users"], 
                  summary="Create new user",
                  description="Create a new user account with profile information")
def create_user():
    """Create a new user account."""
    return {"message": "User created successfully", "id": 123}

@users_group.put("/users/{user_id}", 
                 tags=["update", "users", "profile"], 
                 summary="Update user",
                 description="Update user profile and account information")
def update_user(user_id):
    """Update user profile information."""
    return {"message": f"User {user_id} updated successfully"}

@users_group.delete("/users/{user_id}", 
                    tags=["delete", "users"], 
                    summary="Delete user",
                    description="Permanently delete a user account")
def delete_user(user_id):
    """Delete a user account."""
    return {"message": f"User {user_id} deleted successfully"}

# ========================================
# PRODUCT CATALOG GROUP
# ========================================

@products_group.get("/products", 
                    cache_ttl=300,  # 5 minutes cache
                    tags=["list", "products", "catalog"], 
                    summary="List products",
                    description="Get paginated list of products with filtering options")
def list_products():
    """Get all products with caching for better performance."""
    return {
        "products": [
            {"id": 1, "name": "Laptop", "price": 999.99},
            {"id": 2, "name": "Mouse", "price": 29.99}
        ],
        "cache_info": "Cached for 5 minutes"
    }

@products_group.get("/products/{product_id}", 
                    tags=["get", "products", "details"], 
                    summary="Get product details",
                    description="Retrieve detailed product information including reviews and specs")
def get_product(product_id):
    """Get detailed product information."""
    return {
        "id": int(product_id),
        "name": f"Product {product_id}",
        "price": 99.99,
        "details": {"category": "electronics", "stock": 50}
    }

@products_group.get("/products/category/{category}", 
                    tags=["filter", "products", "category"], 
                    summary="Products by category",
                    description="Get all products in a specific category")
def get_products_by_category(category):
    """Get products filtered by category."""
    return {
        "category": category,
        "products": [{"id": 1, "name": f"{category} Product", "price": 49.99}]
    }

# ========================================
# MIDDLEWARE DEMONSTRATION GROUP
# ========================================

@middleware_group.get("/cors-test", 
                      tags=["cors", "demo"], 
                      summary="CORS middleware test",
                      description="Test CORS headers - middleware automatically adds them")
def cors_test():
    """Test CORS middleware functionality."""
    middleware_stats["cors_requests"] += 1
    return {
        "message": "CORS headers added by middleware",
        "test": "Check response headers for Access-Control-* headers",
        "cors_enabled": True,
        "stats": middleware_stats
    }

@middleware_group.get("/rate-limit-test", 
                      tags=["rate-limit", "demo"], 
                      summary="Rate limiting test",
                      description="Test rate limiting - make rapid requests to see limits")
def rate_limit_test():
    """Test rate limiting middleware."""
    middleware_stats["rate_limited_requests"] += 1
    return {
        "message": "Rate limiting active",
        "limit": "100 requests per minute",
        "tip": "Make rapid requests to test rate limiting",
        "stats": middleware_stats
    }

@middleware_group.get("/logging-demo", 
                      tags=["logging", "demo"], 
                      summary="Logging middleware demo",
                      description="Check console output to see request logging")
def logging_demo():
    """Demonstrate logging middleware in action."""
    middleware_stats["total_requests"] += 1
    time.sleep(0.1)  # Simulate some processing time
    
    return {
        "message": "Check console for logging output",
        "logged": True,
        "processing_time": "~0.1 seconds",
        "total_requests": middleware_stats["total_requests"]
    }

@middleware_group.get("/admin/protected", 
                      tags=["auth", "admin", "demo"], 
                      summary="Protected admin route",
                      description="Requires 'Bearer admin-token' in Authorization header")
def protected_admin():
    """Protected route requiring authentication."""
    middleware_stats["auth_protected_requests"] += 1
    return {
        "message": "Admin access granted!",
        "protected": True,
        "auth_required": "Bearer admin-token",
        "stats": middleware_stats
    }

@middleware_group.get("/headers-demo", 
                      tags=["security", "headers", "demo"], 
                      summary="Security headers demo",
                      description="Check response headers for security middleware additions")
def headers_demo():
    """Demonstrate security headers added by middleware."""
    return {
        "message": "Check response headers",
        "security_headers": [
            "X-Content-Type-Options: nosniff",
            "X-Frame-Options: DENY"
        ],
        "note": "These headers are automatically added by middleware"
    }

@middleware_group.post("/middleware-chain", 
                       tags=["chain", "demo"], 
                       summary="Middleware chain test",
                       description="Test the complete middleware chain execution")
def middleware_chain_test():
    """Test complete middleware chain processing."""
    middleware_stats["total_requests"] += 1
    return {
        "message": "Request processed through middleware chain",
        "middlewares": [
            "CORS → Rate Limiting → Logging → Auth → Security Headers"
        ],
        "chain_complete": True,
        "middleware_applied": [
            "CORSMiddleware", "RateLimitMiddleware", 
            "LoggingMiddleware", "SimpleAuthMiddleware"
        ],
        "stats": middleware_stats
    }

@middleware_group.get("/middleware-stats", 
                      tags=["stats", "monitoring"], 
                      summary="Middleware statistics",
                      description="View middleware usage statistics")
def get_middleware_stats():
    """Get middleware usage statistics."""
    return {
        "middleware_stats": middleware_stats,
        "active_middleware": [type(m).__name__ for m in app.middleware_stack.middlewares],
        "middleware_count": len(app.middleware_stack.middlewares)
    }

# ========================================
# USING DECORATORS FOR ADVANCED TAGGING
# ========================================

@app.tag("admin", "system")
@app.summary("System health check")
@app.description("Comprehensive system health and performance monitoring endpoint")
@app.get("/health", static=True, group="System Monitoring")
def health_check():
    """System health check with admin access."""
    return {"status": "healthy", "timestamp": "2025-01-19T10:30:00Z"}

@app.tag("admin", "analytics", "reports")
@app.get("/admin/analytics", 
         cache_ttl=60, 
         group="Administration",
         summary="Analytics dashboard",
         description="Get system analytics and usage statistics")
def get_analytics():
    """Get system analytics and usage reports."""
    return {
        "daily_users": 1250,
        "requests_per_hour": 3500,
        "cache_hit_rate": "94%"
    }

@app.tag("search", "discovery")
@app.get("/search/{query}", 
         group="Search & Discovery",
         summary="Global search",
         description="Search across users, products, and content with advanced filtering")
def global_search(query):
    """Advanced search across all entities."""
    return {
        "query": query,
        "results": {"users": 3, "products": 7, "total": 10},
        "suggestions": ["related", "searches"]
    }

# ========================================
# MIXED ROUTING WITH ENHANCED FEATURES
# ========================================

@app.get("/", 
         static=True, 
         tags=["home", "welcome"], 
         group="Core Features",
         summary="Welcome page",
         description="Main landing page with API information and navigation")
def home():
    """Enhanced home page with navigation."""
    return {
        "message": "🚀 Enhanced Sufast with Groups & Tags!",
        "features": ["Groups", "Tags", "Enhanced Documentation"],
        "documentation": "/docs"
    }

@app.get("/stats", 
         cache_ttl=30,
         tags=["system", "performance"], 
         group="System Monitoring",
         summary="Performance statistics",
         description="Real-time system performance metrics and statistics")
def get_stats():
    """Get real-time performance statistics."""
    return {
        "performance": {
            "routes_total": len(app.route_metadata),
            "groups": len(app.get_all_groups()),
            "tags": len(app.get_all_tags())
        }
    }

# ========================================
# DEMONSTRATION ROUTES
# ========================================

@app.get("/demo/tags", 
         tags=["demo", "showcase", "examples"], 
         group="Demo & Examples",
         summary="Tag demonstration",
         description="Showcase different tagging strategies and filtering capabilities")
def demo_tags():
    """Demonstrate tag functionality."""
    return {
        "all_tags": app.get_all_tags(),
        "message": "Check /docs to see tags in action!"
    }

@app.get("/demo/groups", 
         tags=["demo", "showcase", "organization"], 
         group="Demo & Examples",
         summary="Group demonstration", 
         description="Showcase route grouping and organization features")
def demo_groups():
    """Demonstrate group functionality."""
    return {
        "all_groups": app.get_all_groups(),
        "message": "Visit /docs to explore grouped routes!"
    }

if __name__ == "__main__":
    print("🎯 Enhanced Sufast Example with Groups, Tags & Middleware")
    print(f"📊 Total Routes: {len(app.route_metadata)}")
    print(f"🏷️  Total Tags: {len(app.get_all_tags())}")
    print(f"📁 Total Groups: {len(app.get_all_groups())}")
    print(f"🛡️  Middleware Stack: {len(app.middleware_stack.middlewares)} middlewares")
    print()
    print("🔗 Available Groups:")
    for group in app.get_all_groups():
        routes_count = len(app.get_routes_by_group(group))
        print(f"   • {group}: {routes_count} routes")
    print()
    print("🏷️  Available Tags:")
    for tag in app.get_all_tags()[:10]:  # Show first 10 tags
        routes_count = len(app.get_routes_by_tag(tag))
        print(f"   • #{tag}: {routes_count} routes")
    print()
    print("🛡️  Active Middleware:")
    middleware_types = [type(m).__name__ for m in app.middleware_stack.middlewares]
    for i, middleware in enumerate(middleware_types, 1):
        print(f"   {i}. {middleware}")
    print()
    print("🧪 Test Middleware:")
    print("   • CORS: Try requests from different origins")
    print("   • Rate Limiting: Make rapid requests to /middleware/rate-limit-test")
    print("   • Auth: Access /middleware/admin/protected (need 'Bearer admin-token')")
    print("   • Logging: Check console output for request logs")
    print("   • Stats: View /middleware/middleware-stats")
    
    app.run(host="127.0.0.1", port=8080, doc=True)
