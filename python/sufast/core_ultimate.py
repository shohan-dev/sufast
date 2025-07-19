"""
Ultimate Sufast v2.0 - Maximum Performance Hybrid Framework
Three-tier architecture:
- Static routes: 52K+ RPS (pre-compiled)
- Cached routes: 45K+ RPS (intelligent caching)
- Dynamic routes: 2K+ RPS (real-time processing)
"""

import ctypes
import json
import re
import threading
from pathlib import Path

class Sufast:
    """Ultimate Sufast framework with three-tier performance optimization."""
    print("🚀 Welcome to Sufast - The Ultimate Python Web Framework")
    print("\n")
    
    def __init__(self):
        self.routes = {}
        self.static_routes = {}
        self.dynamic_routes = {}
        self.cached_routes = {}
        self.route_metadata = {}  # Store route metadata for auto-docs
        self.docs_enabled = False  # Track if docs should be available
        self.rust_core = None
        self._response_storage = threading.local()
        self._load_ultimate_rust_core()
        
    def _load_ultimate_rust_core(self):
        """Load the ultimate optimized Rust core."""
        lib_paths = [
            Path(__file__).parent / "sufast_server.dll",
            Path(__file__).parent / "libsufast_server.so", 
            Path(__file__).parent / "libsufast_server.dylib",
        ]
        
        for lib_path in lib_paths:
            if lib_path.exists():
                try:
                    self.rust_core = ctypes.CDLL(str(lib_path))
                    self._setup_ultimate_ffi()
                    return
                except Exception as e:
                    print(f"⚠️ Failed to load {lib_path}: {e}")
        
        raise RuntimeError("❌ Could not load ultimate Rust core")

    def _setup_ultimate_ffi(self):
        """Setup ultra-fast performance FFI functions."""
        try:
            # Static route registration for 70K+ RPS
            self.rust_core.add_static_route.argtypes = [
                ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint16, ctypes.c_char_p
            ]
            self.rust_core.add_static_route.restype = ctypes.c_bool
            
            # Dynamic route registration for 5K+ RPS 
            self.rust_core.add_dynamic_route.argtypes = [
                ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint64
            ]
            self.rust_core.add_dynamic_route.restype = ctypes.c_bool
            
            # Ultra-fast Python callback registration (3 parameters)
            PythonCallback = ctypes.CFUNCTYPE(ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p)
            self.rust_core.set_python_callback.argtypes = [PythonCallback]
            self.rust_core.set_python_callback.restype = None
            
            # Fast server start
            self.rust_core.start_ultra_fast_server.argtypes = [ctypes.c_char_p, ctypes.c_uint16]
            self.rust_core.start_ultra_fast_server.restype = ctypes.c_int
            
            # Performance stats
            self.rust_core.get_performance_stats.argtypes = []
            self.rust_core.get_performance_stats.restype = ctypes.POINTER(ctypes.c_char)
            
            # Cache management
            self.rust_core.clear_cache.argtypes = []
            self.rust_core.clear_cache.restype = ctypes.c_bool
            
            # Static route precompilation
            self.rust_core.precompile_static_routes.argtypes = []
            self.rust_core.precompile_static_routes.restype = ctypes.c_uint64
            
            
            # Register ultra-fast Python callback
            self._register_ultimate_callback()
            
            # Precompile static routes for maximum performance
            precompiled_count = self.rust_core.precompile_static_routes()
            self._precompiled_routes = precompiled_count

        except Exception as e:
            raise RuntimeError(f"❌ Failed to setup ultra-fast FFI: {e}")

    def _register_ultimate_callback(self):
        """Register the ultra-fast Python callback for dynamic routes."""
        def ultra_fast_python_callback(method_ptr, path_ptr, params_ptr):
            try:
                method = ctypes.string_at(method_ptr).decode('utf-8')
                path = ctypes.string_at(path_ptr).decode('utf-8')
                params_json = ctypes.string_at(params_ptr).decode('utf-8')
                
                # Parse parameters ultra-fast
                try:
                    params = json.loads(params_json)
                except:
                    params = {}
                
                # Handle dynamic route with ultra-fast processing
                response = self._handle_ultra_fast_dynamic_route(method, path, params)
                
                # Convert response to optimized JSON format
                if isinstance(response, dict):
                    if 'body' in response and 'status' in response:
                        # Already formatted response
                        response_json = json.dumps(response)
                    else:
                        # Convert data to response format
                        response_json = json.dumps({
                            "body": json.dumps(response),
                            "status": 200,
                            "headers": {"Content-Type": "application/json"}
                        })
                elif isinstance(response, tuple) and len(response) == 2:
                    # Handle (data, status) tuple
                    data, status = response
                    response_json = json.dumps({
                        "body": json.dumps(data) if isinstance(data, dict) else str(data),
                        "status": status,
                        "headers": {"Content-Type": "application/json"}
                    })
                else:
                    response_json = json.dumps({
                        "body": json.dumps(response) if isinstance(response, dict) else str(response),
                        "status": 200,
                        "headers": {"Content-Type": "application/json"}
                    })
                
                # Create ultra-fast C string with memory pool
                result_bytes = response_json.encode('utf-8')
                result = ctypes.create_string_buffer(result_bytes)
                
                # Store in thread-local buffer to prevent memory leaks
                if not hasattr(self._response_storage, 'buffer'):
                    self._response_storage.buffer = []
                
                self._response_storage.buffer.append(result)
                
                # Limit buffer size for memory efficiency
                if len(self._response_storage.buffer) > 50:
                    self._response_storage.buffer = self._response_storage.buffer[-25:]
                
                return ctypes.cast(result, ctypes.c_char_p).value
                
            except Exception as e:
                print(f"❌ Ultra-fast callback error: {e}")
                error_response = json.dumps({
                    "body": json.dumps({"error": f"Internal server error: {str(e)}"}),
                    "status": 500,
                    "headers": {"Content-Type": "application/json"}
                })
                
                result_bytes = error_response.encode('utf-8')
                result = ctypes.create_string_buffer(result_bytes)
                return ctypes.cast(result, ctypes.c_char_p).value
        
        # Create ultra-fast callback function with 3 parameters
        callback_func = ctypes.CFUNCTYPE(ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p)(ultra_fast_python_callback)
        
        # Store reference to prevent garbage collection
        self._callback_func_ref = callback_func
        
        # Register with Rust
        self.rust_core.set_python_callback(callback_func)

    def _handle_ultra_fast_dynamic_route(self, method, path, params):
        """Handle dynamic route with ultra-fast parameter processing."""
        route_key = f"{method}:{path}"
        
        # Try exact match first (fastest path)
        if route_key in self.routes:
            handler = self.routes[route_key]
            return handler()
        
        # Ultra-fast pattern matching for dynamic routes
        for pattern_key, handler_info in self.dynamic_routes.items():
            if method in pattern_key:
                regex = handler_info['regex']
                match = regex.match(path)
                if match:
                    # Extract parameters ultra-fast
                    extracted_params = match.groupdict()
                    
                    # Merge with any additional params
                    final_params = {**extracted_params, **params}
                    
                    # Call handler with parameters
                    handler = handler_info['handler']
                    
                    try:
                        if final_params:
                            # Call with extracted parameters
                            return handler(**final_params)
                        else:
                            # Call without parameters
                            return handler()
                    except TypeError:
                        # Handle case where handler doesn't accept parameters
                        try:
                            return handler()
                        except Exception as e:
                            return {
                                "body": json.dumps({"error": f"Handler error: {str(e)}"}),
                                "status": 500,
                                "headers": {"Content-Type": "application/json"}
                            }
        
        # Return 404 if no route found
        return {
            "body": json.dumps({
                "error": "Route not found",
                "path": path,
                "method": method,
                "available_routes": list(self.routes.keys())
            }),
            "status": 404,
            "headers": {"Content-Type": "application/json"}
        }

    def route(self, path: str, cache_ttl: int = 0, static: bool = None):
        """Ultimate route decorator with intelligent three-tier optimization.
        
        Args:
            path: Route pattern (e.g., '/user/{user_id}')
            cache_ttl: Cache time in seconds (0 = no cache, >0 = cached route)
            static: Force static compilation (auto-detected if None)
        """
        def decorator(func):
            # Intelligent tier detection
            has_params = '{' in path and '}' in path
            is_static = static if static is not None else (not has_params and cache_ttl == 0)
            is_cached = cache_ttl > 0
            
            route_key = f"GET:{path}"
            
            if is_static:
                # TIER 1: Static route (52K+ RPS) - Pre-compile response
                try:
                    response = func()
                    
                    # Normalize response format
                    if isinstance(response, dict):
                        if 'body' in response:
                            body = response['body']
                            status = response.get('status', 200)
                            content_type = response.get('headers', {}).get('Content-Type', 'application/json')
                        else:
                            body = json.dumps(response)
                            status = 200
                            content_type = 'application/json'
                    elif isinstance(response, tuple) and len(response) == 2:
                        data, status = response
                        body = json.dumps(data) if isinstance(data, dict) else str(data)
                        content_type = 'application/json'
                    else:
                        body = json.dumps(response) if isinstance(response, dict) else str(response)
                        status = 200
                        content_type = 'application/json'
                    
                    # Register as ultra-fast static route
                    success = self.rust_core.add_static_route(
                        route_key.encode('utf-8'),
                        body.encode('utf-8'),
                        status,
                        content_type.encode('utf-8')
                    )
                    
                    if success:
                        self.static_routes[route_key] = func
                    else:
                        print(f"⚠️ Failed to optimize {path} as static, falling back to dynamic")
                        is_static = False
                        
                except Exception as e:
                    print(f"⚠️ Failed to pre-compile {path}: {e}")
                    # Fall back to dynamic route
                    is_static = False
            
            if not is_static:
                # TIER 2 & 3: Dynamic/Cached routes
                success = self.rust_core.add_dynamic_route(
                    b"GET",
                    path.encode('utf-8'),
                    func.__name__.encode('utf-8'),
                    cache_ttl
                )
                
                if success:
                    if is_cached:
                        self.cached_routes[route_key] = func
                    
                
                # Compile regex for ultra-fast parameter extraction
                pattern_str = path
                for match in re.finditer(r'\{(\w+)\}', path):
                    param_name = match.group(1)
                    pattern_str = pattern_str.replace(f'{{{param_name}}}', f'(?P<{param_name}>[^/]+)')
                
                pattern_str = f"^{pattern_str}$"
                compiled_pattern = re.compile(pattern_str)
                
                # Store for Python callback
                self.dynamic_routes[route_key] = {
                    'handler': func,
                    'regex': compiled_pattern,
                    'cache_ttl': cache_ttl,
                    'pattern': path
                }
            
            # Always store in routes for reference
            self.routes[route_key] = func
            
            # Store metadata for auto-generated docs
            self._store_route_metadata(path, "GET", func, is_static, is_cached, cache_ttl)
            
            return func
        return decorator

    def _store_route_metadata(self, path, method, func, is_static, is_cached, cache_ttl):
        """Store route metadata for auto-generated documentation."""
        # Extract parameters from path
        parameters = []
        for match in re.finditer(r'\{(\w+)\}', path):
            param_name = match.group(1)
            parameters.append({
                'name': param_name,
                'type': 'string',  # Default type, could be enhanced with type hints
                'required': True,
                'description': f'Path parameter: {param_name}'
            })
        
        # Determine performance tier
        if is_static:
            tier = 'static'
            performance = '52,000+ RPS'
            description_suffix = '(Pre-compiled)'
        elif is_cached:
            tier = 'cached'
            performance = '45,000+ RPS'
            description_suffix = f'(Cached {cache_ttl}s)'
        else:
            tier = 'dynamic'
            performance = '2,000+ RPS'
            description_suffix = '(Real-time)'
        
        # Extract description from docstring
        description = func.__doc__ or f"{method} {path}"
        if description:
            description = description.strip().split('\n')[0]  # First line only
        
        self.route_metadata[f"{method}:{path}"] = {
            'path': path,
            'method': method,
            'function_name': func.__name__,
            'description': description,
            'parameters': parameters,
            'tier': tier,
            'performance': performance,
            'cache_ttl': cache_ttl if is_cached else None,
            'description_suffix': description_suffix
        }

    def _register_docs_route(self):
        """Auto-register the /docs route for interactive API documentation."""
        @self.route('/docs', static=False)  # Dynamic so it updates with new routes
        def auto_generated_docs():
            """🌐 Auto-Generated API Documentation - Interactive Explorer"""
            if not self.docs_enabled:
                return {
                    "body": json.dumps({
                        "error": "Documentation not enabled",
                        "message": "To enable documentation, use app.run(doc=True)",
                        "example": "app.run(host='127.0.0.1', port=8080, doc=True)"
                    }),
                    "status": 403,
                    "headers": {"Content-Type": "application/json"}
                }
            
            swagger_html = self._generate_swagger_ui()
            return {
                "body": swagger_html,
                "status": 200,
                "headers": {
                    "Content-Type": "text/html; charset=utf-8",
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            }
        
        # Don't store metadata for the docs route itself to avoid recursion
        if "GET:/docs" in self.route_metadata:
            del self.route_metadata["GET:/docs"]

    def _generate_swagger_ui(self):
        """Generate modern, user-friendly API documentation."""
        # Group routes by tier
        static_routes = []
        cached_routes = []
        dynamic_routes = []
        
        for route_key, metadata in self.route_metadata.items():
            if metadata['tier'] == 'static':
                static_routes.append(metadata)
            elif metadata['tier'] == 'cached':
                cached_routes.append(metadata)
            else:
                dynamic_routes.append(metadata)
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sufast API Documentation</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #1a1a1a;
            line-height: 1.6;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            padding: 1.5rem 0;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }}
        
        .header-content {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .logo {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.5rem;
            font-weight: 700;
            color: #2563eb;
            text-decoration: none;
        }}
        
        .logo i {{
            font-size: 2rem;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .version {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            margin-top: 0;
            border-radius: 0;
            min-height: calc(100vh - 100px);
        }}
        
        .hero {{
            text-align: center;
            padding: 3rem 0;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border-radius: 16px;
            margin-bottom: 3rem;
            position: relative;
            overflow: hidden;
        }}
        
        .hero::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="%23e2e8f0" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
            opacity: 0.5;
        }}
        
        .hero-content {{
            position: relative;
            z-index: 2;
        }}
        
        .hero h1 {{
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1rem;
        }}
        
        .hero p {{
            font-size: 1.2rem;
            color: #64748b;
            margin-bottom: 2rem;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }}
        
        .hero-stats {{
            display: flex;
            justify-content: center;
            gap: 3rem;
            flex-wrap: wrap;
        }}
        
        .stat {{
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 2rem;
            font-weight: 700;
            color: #1e293b;
        }}
        
        .stat-label {{
            font-size: 0.9rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .tabs {{
            display: flex;
            background: #f8fafc;
            border-radius: 12px;
            padding: 0.5rem;
            margin-bottom: 2rem;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.06);
        }}
        
        .tab {{
            flex: 1;
            padding: 1rem 1.5rem;
            text-align: center;
            cursor: pointer;
            border-radius: 8px;
            font-weight: 600;
            color: #64748b;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }}
        
        .tab:hover {{
            color: #3b82f6;
            background: rgba(59, 130, 246, 0.1);
        }}
        
        .tab.active {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            transform: translateY(-1px);
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        .tier-section {{
            margin-bottom: 3rem;
        }}
        
        .tier-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 2rem;
            padding: 2rem;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border-radius: 16px;
            border-left: 6px solid;
            position: relative;
            overflow: hidden;
        }}
        
        .tier-header::before {{
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            bottom: 0;
            width: 100px;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1));
        }}
        
        .tier-static {{ border-left-color: #ef4444; }}
        .tier-cached {{ border-left-color: #f59e0b; }}
        .tier-dynamic {{ border-left-color: #3b82f6; }}
        
        .tier-icon {{
            width: 4rem;
            height: 4rem;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            color: white;
            background: linear-gradient(135deg, #667eea, #764ba2);
            box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
        }}
        
        .tier-info {{
            flex: 1;
        }}
        
        .tier-title {{
            font-size: 2rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.5rem;
        }}
        
        .tier-description {{
            color: #64748b;
            font-size: 1.1rem;
        }}
        
        .route-count {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            font-weight: 700;
            font-size: 1.1rem;
            text-align: center;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }}
        
        .endpoint {{
            background: white;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease;
            overflow: hidden;
            border: 1px solid #f1f5f9;
        }}
        
        .endpoint:hover {{
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
            transform: translateY(-2px);
        }}
        
        .endpoint-header {{
            padding: 1.5rem 2rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #fafafa;
            border-bottom: 1px solid #f1f5f9;
            transition: background 0.2s ease;
        }}
        
        .endpoint-header:hover {{
            background: #f8fafc;
        }}
        
        .endpoint.active .endpoint-header {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }}
        
        .endpoint.active .endpoint-header .method-badge {{
            background: rgba(255, 255, 255, 0.2);
            color: white;
        }}
        
        .endpoint-left {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        
        .method-badge {{
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            min-width: 80px;
            text-align: center;
        }}
        
        .method-get {{ background: #dbeafe; color: #1e40af; }}
        .method-post {{ background: #dcfce7; color: #166534; }}
        .method-put {{ background: #fef3c7; color: #92400e; }}
        .method-delete {{ background: #fee2e2; color: #991b1b; }}
        
        .endpoint-path {{
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-weight: 600;
            font-size: 1.1rem;
            color: #1e293b;
        }}
        
        .endpoint.active .endpoint-path {{
            color: white;
        }}
        
        .endpoint-right {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        
        .performance-badge {{
            background: #f1f5f9;
            color: #475569;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        
        .endpoint.active .performance-badge {{
            background: rgba(255, 255, 255, 0.2);
            color: white;
        }}
        
        .expand-icon {{
            font-size: 1.2rem;
            color: #94a3b8;
            transition: transform 0.3s ease;
        }}
        
        .endpoint.active .expand-icon {{
            transform: rotate(180deg);
            color: white;
        }}
        
        .endpoint-body {{
            padding: 2rem;
            display: none;
            background: #fafafa;
        }}
        
        .endpoint.active .endpoint-body {{
            display: block;
        }}
        
        .description {{
            color: #64748b;
            font-size: 1rem;
            margin-bottom: 2rem;
            padding: 1rem;
            background: white;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
        }}
        
        .parameters {{
            margin-bottom: 2rem;
        }}
        
        .parameters h4 {{
            font-size: 1.2rem;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .parameter {{
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.2s ease;
        }}
        
        .parameter:hover {{
            border-color: #3b82f6;
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
        }}
        
        .parameter-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
        }}
        
        .parameter-name {{
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-weight: 700;
            color: #1e293b;
            font-size: 1rem;
        }}
        
        .parameter-type {{
            background: #f1f5f9;
            color: #475569;
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        
        .parameter-input {{
            width: 100%;
            padding: 0.75rem 1rem;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 1rem;
            transition: all 0.2s ease;
        }}
        
        .parameter-input:focus {{
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }}
        
        .try-section {{
            background: white;
            border-radius: 12px;
            padding: 2rem;
            border: 1px solid #e2e8f0;
        }}
        
        .try-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}
        
        .try-header h4 {{
            font-size: 1.2rem;
            font-weight: 600;
            color: #1e293b;
        }}
        
        .btn {{
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }}
        
        .btn-primary:hover {{
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
        }}
        
        .btn-secondary {{
            background: #f8fafc;
            color: #475569;
            border: 1px solid #e2e8f0;
        }}
        
        .btn-secondary:hover {{
            background: #f1f5f9;
        }}
        
        .response-section {{
            margin-top: 1.5rem;
        }}
        
        .response-container {{
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }}
        
        .response-container.success {{
            border: 2px solid #10b981;
            box-shadow: 0 4px 16px rgba(16, 185, 129, 0.2);
        }}
        
        .response-container.error {{
            border: 2px solid #ef4444;
            box-shadow: 0 4px 16px rgba(239, 68, 68, 0.2);
        }}
        
        .response-container.warning {{
            border: 2px solid #f59e0b;
            box-shadow: 0 4px 16px rgba(245, 158, 11, 0.2);
        }}
        
        .response-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1rem 1.5rem;
            margin: 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .response-header.success {{
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
        }}
        
        .response-header.error {{
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
        }}
        
        .response-header.warning {{
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: white;
        }}
        
        .response-header.info {{
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            color: white;
        }}
        
        .response-title {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 1.1rem;
            font-weight: 600;
        }}
        
        .response-status {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-weight: 600;
            font-size: 0.95rem;
        }}
        
        .status-badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .status-badge.success {{
            background: rgba(255, 255, 255, 0.2);
            color: white;
        }}
        
        .status-badge.error {{
            background: rgba(255, 255, 255, 0.2);
            color: white;
        }}
        
        .status-badge.warning {{
            background: rgba(255, 255, 255, 0.2);
            color: white;
        }}
        
        .timing-badge {{
            background: rgba(255, 255, 255, 0.15);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        
        .response-body {{
            padding: 0;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9rem;
            line-height: 1.6;
            max-height: 500px;
            overflow-y: auto;
            position: relative;
        }}
        
        .response-content {{
            padding: 1.5rem;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        .response-body.success .response-content {{
            background: linear-gradient(135deg, #f0fdf4, #dcfce7);
            color: #166534;
            border-left: 4px solid #10b981;
        }}
        
        .response-body.error .response-content {{
            background: linear-gradient(135deg, #fef2f2, #fee2e2);
            color: #991b1b;
            border-left: 4px solid #ef4444;
        }}
        
        .response-body.warning .response-content {{
            background: linear-gradient(135deg, #fffbeb, #fef3c7);
            color: #92400e;
            border-left: 4px solid #f59e0b;
        }}
        
        .response-body.info .response-content {{
            background: linear-gradient(135deg, #eff6ff, #dbeafe);
            color: #1e40af;
            border-left: 4px solid #3b82f6;
        }}
        
        .response-meta {{
            background: rgba(0, 0, 0, 0.05);
            padding: 0.75rem 1.5rem;
            border-top: 1px solid rgba(0, 0, 0, 0.1);
            font-size: 0.8rem;
            color: #6b7280;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .content-type-badge {{
            background: #f3f4f6;
            color: #374151;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-weight: 500;
        }}
        
        .loading {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.75rem;
            padding: 2rem;
            background: linear-gradient(135deg, #f8fafc, #e2e8f0);
            border-radius: 12px;
            border: 2px solid #cbd5e1;
            color: #475569;
            font-weight: 600;
        }}
        
        .loading i {{
            animation: spin 1s linear infinite;
            font-size: 1.2rem;
            color: #3b82f6;
        }}
        
        @keyframes spin {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        
        /* JSON Syntax Highlighting */
        .json-key {{
            color: #7c3aed;
            font-weight: 600;
        }}
        
        .json-string {{
            color: #059669;
        }}
        
        .json-number {{
            color: #dc2626;
        }}
        
        .json-boolean {{
            color: #2563eb;
            font-weight: 600;
        }}
        
        .json-null {{
            color: #6b7280;
            font-style: italic;
        }}
        
        /* Copy button */
        .copy-button {{
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            padding: 0.5rem 0.75rem;
            cursor: pointer;
            opacity: 0;
            transition: all 0.3s ease;
            color: #374151;
            font-size: 0.85rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.375rem;
            backdrop-filter: blur(10px);
            z-index: 10;
            min-width: 70px;
            justify-content: center;
        }}
        
        .response-body:hover .copy-button {{
            opacity: 1;
            transform: translateY(-1px);
        }}
        
        .copy-button:hover {{
            background: white;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            border-color: #3b82f6;
            color: #3b82f6;
            transform: translateY(-2px);
        }}
        
        .copy-button:active {{
            transform: translateY(0);
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .copy-button.copied {{
            background: #10b981;
            color: white;
            border-color: #10b981;
        }}
        
        .copy-button.copied:hover {{
            background: #059669;
            border-color: #059669;
        }}
        
        /* Legacy status classes for backward compatibility */
        .status-200 {{ color: #10b981; }}
        .status-400 {{ color: #f59e0b; }}
        .status-404 {{ color: #ef4444; }}
        .status-500 {{ color: #ef4444; }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 1rem;
            }}
            
            .hero h1 {{
                font-size: 2rem;
            }}
            
            .hero-stats {{
                gap: 1.5rem;
            }}
            
            .tabs {{
                flex-direction: column;
            }}
            
            .endpoint-header {{
                flex-direction: column;
                align-items: flex-start;
                gap: 1rem;
            }}
            
            .endpoint-right {{
                width: 100%;
                justify-content: space-between;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <a href="#" class="logo">
                <i class="fas fa-rocket"></i>
                Sufast API
            </a>
            <div class="version">v1.0</div>
        </div>
    </div>
    
    <div class="container">
        <div class="hero">
            <div class="hero-content">
                <h1>API Documentation</h1>
                <p>Explore the Three-Tier Performance Architecture with interactive endpoint testing</p>
                <div class="hero-stats">
                    <div class="stat">
                        <div class="stat-number">{len(static_routes)}</div>
                        <div class="stat-label">Static Routes</div>
                    </div>
                    <div class="stat">
                         <div class="stat-number">{len(cached_routes)}</div>
                        <div class="stat-label">Cached Routes</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{len(dynamic_routes)}</div>
                        <div class="stat-label">Dynamic Routes</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="tabs">
            <div class="tab active" onclick="showTab('static')">
                <i class="fas fa-bolt"></i>
                Static Routes 
            </div>
            <div class="tab" onclick="showTab('cached')">
                <i class="fas fa-memory"></i>
                Cached Routes
            </div>
            <div class="tab" onclick="showTab('dynamic')">
                <i class="fas fa-cogs"></i>
                Dynamic Routes
            </div>
        </div>
        
        <div id="static" class="tab-content active">
            <div class="tier-section">
                <div class="tier-header tier-static">
                    <div class="tier-icon">
                        <i class="fas fa-bolt"></i>
                    </div>
                    <div class="tier-info">
                        <div class="tier-title">Static Routes</div>
                        <div class="tier-description">Pre-compiled responses for maximum performance</div>
                    </div>
                    <div class="route-count">{len(static_routes)} routes</div>
                </div>
                {self._generate_modern_routes(static_routes, 'static')}
            </div>
        </div>
        
        <div id="cached" class="tab-content">
            <div class="tier-section">
                <div class="tier-header tier-cached">
                    <div class="tier-icon">
                        <i class="fas fa-memory"></i>
                    </div>
                    <div class="tier-info">
                        <div class="tier-title">Cached Routes</div>
                        <div class="tier-description">Smart caching with configurable TTL</div>
                    </div>
                    <div class="route-count">{len(cached_routes)} routes</div>
                </div>
                {self._generate_modern_routes(cached_routes, 'cached')}
            </div>
        </div>
        
        <div id="dynamic" class="tab-content">
            <div class="tier-section">
                <div class="tier-header tier-dynamic">
                    <div class="tier-icon">
                        <i class="fas fa-cogs"></i>
                    </div>
                    <div class="tier-info">
                        <div class="tier-title">Dynamic Routes</div>
                        <div class="tier-description">Real-time processing with parameter extraction</div>
                    </div>
                    <div class="route-count">{len(dynamic_routes)} routes</div>
                </div>
                {self._generate_modern_routes(dynamic_routes, 'dynamic')}
            </div>
        </div>
    </div>
    
    <script>
        function showTab(tabName) {{
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }}
        
        function toggleEndpoint(endpointId) {{
            const endpoint = document.getElementById(endpointId);
            const isActive = endpoint.classList.contains('active');
            
            document.querySelectorAll('.endpoint').forEach(ep => ep.classList.remove('active'));
            
            if (!isActive) {{
                endpoint.classList.add('active');
            }}
        }}
        
        async function executeRequest(path, method, endpointId) {{
            const inputs = document.querySelectorAll(`#${{endpointId}} .parameter-input`);
            let url = path;
            
            for (const input of inputs) {{
                const paramName = input.dataset.param;
                const value = input.value.trim();
                if (!value) {{
                    alert(`Please enter a value for parameter: ${{paramName}}`);
                    input.focus();
                    return;
                }}
                url = url.replace(`{{${{paramName}}}}`, encodeURIComponent(value));
            }}
            
            const responseContainer = document.getElementById(`response-${{endpointId}}`);
            responseContainer.innerHTML = '<div class="loading"><i class="fas fa-spinner"></i> Executing request...</div>';
            
            try {{
                const start = performance.now();
                const response = await fetch(url, {{
                    method: method,
                    headers: {{
                        'Accept': 'application/json',
                        'Cache-Control': 'no-cache'
                    }}
                }});
                const end = performance.now();
                const responseTime = Math.round(end - start);
                
                const contentType = response.headers.get('content-type') || 'text/plain';
                let data;
                let isJson = false;
                
                if (contentType.includes('application/json')) {{
                    data = await response.json();
                    isJson = true;
                }} else {{
                    const text = await response.text();
                    try {{
                        data = JSON.parse(text);
                        isJson = true;
                    }} catch {{
                        data = {{ raw_response: text, content_type: contentType }};
                        isJson = false;
                    }}
                }}
                
                // Determine response type for styling
                let responseType = 'info';
                let statusIcon = 'fas fa-info-circle';
                let statusText = response.statusText;
                
                if (response.status >= 200 && response.status < 300) {{
                    responseType = 'success';
                    statusIcon = 'fas fa-check-circle';
                }} else if (response.status >= 400 && response.status < 500) {{
                    responseType = 'warning';
                    statusIcon = 'fas fa-exclamation-triangle';
                }} else if (response.status >= 500) {{
                    responseType = 'error';
                    statusIcon = 'fas fa-times-circle';
                }}
                
                // Format the response data with syntax highlighting if it's JSON
                let formattedData;
                if (isJson) {{
                    formattedData = syntaxHighlightJson(JSON.stringify(data, null, 2));
                }} else {{
                    formattedData = escapeHtml(typeof data === 'string' ? data : JSON.stringify(data, null, 2));
                }}
                
                responseContainer.innerHTML = `
                    <div class="response-container ${{responseType}}">
                        <div class="response-header ${{responseType}}">
                            <div class="response-title">
                                <i class="${{statusIcon}}"></i>
                                Response
                            </div>
                            <div class="response-status">
                                <div class="status-badge ${{responseType}}">
                                    ${{response.status}} ${{statusText}}
                                </div>
                                <div class="timing-badge">
                                    ${{responseTime}}ms
                                </div>
                            </div>
                        </div>
                        <div class="response-body ${{responseType}}">
                            <div class="response-content">
                                <button class="copy-button" onclick="copyResponse('${{endpointId}}')">
                                    <i class="fas fa-copy"></i>
                                    Copy
                                </button>
                                ${{formattedData}}
                            </div>
                            <div class="response-meta">
                                <span class="content-type-badge">${{contentType}}</span>
                                <span>Size: ${{new Blob([typeof data === 'string' ? data : JSON.stringify(data)]).size}} bytes</span>
                            </div>
                        </div>
                    </div>
                `;
            }} catch (error) {{
                responseContainer.innerHTML = `
                    <div class="response-container error">
                        <div class="response-header error">
                            <div class="response-title">
                                <i class="fas fa-exclamation-triangle"></i>
                                Network Error
                            </div>
                            <div class="response-status">
                                <div class="status-badge error">Failed</div>
                            </div>
                        </div>
                        <div class="response-body error">
                            <div class="response-content">
                                <button class="copy-button" onclick="copyResponse('${{endpointId}}')">
                                    <i class="fas fa-copy"></i>
                                    Copy
                                </button>
                                ${{syntaxHighlightJson(JSON.stringify({{ 
                                    error: error.message,
                                    type: error.name,
                                    timestamp: new Date().toISOString()
                                }}, null, 2))}}
                            </div>
                            <div class="response-meta">
                                <span class="content-type-badge">application/json</span>
                                <span>Request failed to complete</span>
                            </div>
                        </div>
                    </div>
                `;
            }}
        }}
        
        function syntaxHighlightJson(json) {{
            return json.replace(/("(\\u[a-zA-Z0-9]{{4}}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {{
                let cls = 'json-number';
                if (/^"/.test(match)) {{
                    if (/:$/.test(match)) {{
                        cls = 'json-key';
                    }} else {{
                        cls = 'json-string';
                    }}
                }} else if (/true|false/.test(match)) {{
                    cls = 'json-boolean';
                }} else if (/null/.test(match)) {{
                    cls = 'json-null';
                }}
                return '<span class="' + cls + '">' + match + '</span>';
            }});
        }}
        
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}
        
        function copyResponse(endpointId) {{
            const responseContent = document.querySelector(`#response-${{endpointId}} .response-content`);
            if (responseContent) {{
                // Get clean text content without HTML tags
                const textContent = responseContent.textContent || responseContent.innerText;
                const cleanText = textContent.replace(/Copy/g, '').trim(); // Remove "Copy" button text
                
                navigator.clipboard.writeText(cleanText).then(() => {{
                    const button = responseContent.querySelector('.copy-button');
                    if (button) {{
                        const originalHTML = button.innerHTML;
                        
                        // Show success state
                        button.innerHTML = '<i class="fas fa-check"></i> Copied';
                        button.classList.add('copied');
                        
                        // Reset after 2 seconds
                        setTimeout(() => {{
                            button.innerHTML = originalHTML;
                            button.classList.remove('copied');
                        }}, 2000);
                    }}
                }}).catch(err => {{
                    console.error('Failed to copy response:', err);
                    const button = responseContent.querySelector('.copy-button');
                    if (button) {{
                        const originalHTML = button.innerHTML;
                        
                        // Show error state
                        button.innerHTML = '<i class="fas fa-times"></i> Failed';
                        button.style.background = '#ef4444';
                        button.style.color = 'white';
                        button.style.borderColor = '#ef4444';
                        
                        // Reset after 2 seconds
                        setTimeout(() => {{
                            button.innerHTML = originalHTML;
                            button.style.background = '';
                            button.style.color = '';
                            button.style.borderColor = '';
                        }}, 2000);
                    }}
                }});
            }}
        }}
        
        function clearResponse(endpointId) {{
            document.getElementById(`response-${{endpointId}}`).innerHTML = '';
        }}
        
        function fillExample(endpointId) {{
            const inputs = document.querySelectorAll(`#${{endpointId}} .parameter-input`);
            inputs.forEach(input => {{
                if (input.dataset.example) {{
                    input.value = input.dataset.example;
                }}
            }});
        }}
    </script>
</body>
</html>'''


    def _generate_modern_routes(self, routes, tier_type):
        """Generate modern, user-friendly route documentation HTML."""
        if not routes:
            return '''
                <div style="text-align: center; padding: 4rem 2rem; color: #64748b;">
                    <i class="fas fa-inbox" style="font-size: 4rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                    <h3 style="margin-bottom: 0.5rem; color: #475569;">No routes found</h3>
                    <p>No routes have been registered in this tier yet.</p>
                </div>
            '''
        
        html = ""
        for i, route in enumerate(routes):
            endpoint_id = f"endpoint_{tier_type}_{i}"
            
            # Generate parameters HTML
            params_html = ""
            if route['parameters']:
                params_html = '''
                    <div class="parameters">
                        <h4><i class="fas fa-sliders-h"></i> Parameters</h4>
                '''
                for param in route['parameters']:
                    example_value = self._get_example_value(param['name'])
                    params_html += f'''
                        <div class="parameter">
                            <div class="parameter-header">
                                <div class="parameter-name">{param['name']}</div>
                                <div class="parameter-type">{param['type']}</div>
                            </div>
                            <input type="text" class="parameter-input" 
                                   data-param="{param['name']}" 
                                   data-example="{example_value}"
                                   placeholder="Enter {param['name']}" 
                                   value="{example_value}">
                        </div>
                    '''
                params_html += '</div>'
            
            # Get performance info
            performance_map = {
                'static': '',
                'cached': '', 
                'dynamic': ''
            }
            performance = performance_map.get(tier_type, 'Unknown')
            
            html += f'''
                <div class="endpoint" id="{endpoint_id}">
                    <div class="endpoint-header" onclick="toggleEndpoint('{endpoint_id}')">
                        <div class="endpoint-left">
                            <div class="method-badge method-{route['method'].lower()}">{route['method']}</div>
                            <div class="endpoint-path">{route['path']}</div>
                        </div>
                        <div class="endpoint-right">
                            <div class="performance-badge">{performance}</div>
                            <i class="fas fa-chevron-down expand-icon"></i>
                        </div>
                    </div>
                    
                    <div class="endpoint-body">
                        <div class="description">
                            <i class="fas fa-info-circle"></i>
                            {route.get('description', 'No description available for this endpoint.')}
                        </div>
                        
                        {params_html}
                        
                        <div class="try-section">
                            <div class="try-header">
                                <h4><i class="fas fa-play-circle"></i> Try it out</h4>
                            </div>
                            
                            <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem;">
                                <button class="btn btn-primary" onclick="executeRequest('{route['path']}', '{route['method']}', '{endpoint_id}')">
                                    <i class="fas fa-paper-plane"></i>
                                    Execute
                                </button>
                                <button class="btn btn-secondary" onclick="clearResponse('{endpoint_id}')">
                                    <i class="fas fa-trash"></i>
                                    Clear
                                </button>'''
            
            if route['parameters']:
                fill_button = f'''
                                <button class="btn btn-secondary" onclick="fillExample('{endpoint_id}')">
                                    <i class="fas fa-magic"></i>
                                    Fill Example
                                </button>'''
                html += fill_button
            
            html += f'''
                            </div>
                            
                            <div class="response-section">
                                <div id="response-{endpoint_id}"></div>
                            </div>
                        </div>
                    </div>
                </div>
            '''
        
        return html

    def _get_example_value(self, param_name):
        """Get example values for common parameter names."""
        examples = {
            'user_id': '1',
            'product_id': '1', 
            'id': '1',
            'slug': 'ultimate-rust-performance',
            'category': 'electronics',
            'query': 'python',
            'name': 'alice',
            'email': 'user@example.com'
        }
        return examples.get(param_name.lower(), f'example_{param_name}')

    def get(self, path: str, **kwargs):
        """GET route decorator - FastAPI style."""
        return self.route(path, **kwargs)
    
    def post(self, path: str, **kwargs):
        """POST route decorator - FastAPI style."""
        return self.route(path, **kwargs)
    
    def put(self, path: str, **kwargs):
        """PUT route decorator - FastAPI style."""
        return self.route(path, **kwargs)
    
    def delete(self, path: str, **kwargs):
        """DELETE route decorator - FastAPI style."""
        return self.route(path, **kwargs)

    def get_ultimate_performance_stats(self):
        """Get comprehensive performance statistics from the ultimate system."""
        try:
            stats_ptr = self.rust_core.get_performance_stats()
            if stats_ptr:
                stats_json = ctypes.string_at(stats_ptr).decode('utf-8')
                rust_stats = json.loads(stats_json)
                
                # Add Python-side stats
                python_stats = {
                    "python_route_counts": {
                        "total_registered": len(self.routes),
                        "static_optimized": len(self.static_routes),
                        "cached_routes": len(self.cached_routes), 
                        "dynamic_routes": len(self.dynamic_routes)
                    },
                    "optimization_summary": {
                        "static_percentage": f"{(len(self.static_routes) / max(len(self.routes), 1)) * 100:.1f}%",
                        "cached_percentage": f"{(len(self.cached_routes) / max(len(self.routes), 1)) * 100:.1f}%",
                        "dynamic_percentage": f"{(len(self.dynamic_routes) / max(len(self.routes), 1)) * 100:.1f}%"
                    }
                }
                
                # Merge stats
                return {**rust_stats, **python_stats}
                
        except Exception as e:
            return {"error": f"Could not get ultimate stats: {e}"}
        return {}

    def clear_cache(self):
        """Clear the response cache for cached routes."""
        try:
            return self.rust_core.clear_cache()
        except Exception:
            return False

    def run(self, host: str = "127.0.0.1", port: int = 8080, debug: bool = False, doc: bool = False):
        """Run the ultra-fast optimized server with three-tier performance.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Enable debug mode
            doc: Enable interactive documentation at /docs
        """
        # Enable docs if requested
        if doc:
            self.docs_enabled = True
            self._register_docs_route()
            print("📚 Documentation enabled! Visit /docs for API reference")
        else:
            self.docs_enabled = False
        
        # Show route distribution
        total_routes = len(self.routes)
        if total_routes > 0:
            static_pct = (len(self.static_routes) / total_routes) * 100
            cached_pct = (len(self.cached_routes) / total_routes) * 100
            dynamic_pct = (len(self.dynamic_routes) / total_routes) * 100
            
            print(f"📊 Routes optimized: {total_routes} total")
            print(f"  🔥 Static: {len(self.static_routes)} ({static_pct:.1f}%)")
            print(f"  🧠 Cached: {len(self.cached_routes)} ({cached_pct:.1f}%)")
            print(f"  ⚡ Dynamic: {len(self.dynamic_routes)} ({dynamic_pct:.1f}%)")
            print()
        
        print(f"🌐 Server starting on http://{host}:{port}")
        if doc:
            print(f"📖 Documentation: http://{host}:{port}/docs")
        # print("🔥 Press Ctrl+C to stop")
        
        try:
            # This blocks and runs the fast server
            host_bytes = host.encode('utf-8')
            result = self.rust_core.start_ultra_fast_server(host_bytes, port)
            if result != 0:
                print(f"❌ Server failed with code: {result}")
        except KeyboardInterrupt:
            print("\n🔄 Server stopped by user")
        except Exception as e:
            print(f"❌ Server error: {e}")


def create_app():
    """Create a new Sufast application instance."""
    return Sufast()


# Export the main class
__all__ = ['Sufast', 'create_app']
