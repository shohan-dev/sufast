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
        
        .response-header {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }}
        
        .response-header h5 {{
            font-size: 1.1rem;
            font-weight: 600;
            color: #1e293b;
        }}
        
        .response-body {{
            background: #1e293b;
            color: #e2e8f0;
            border-radius: 8px;
            padding: 1.5rem;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9rem;
            overflow-x: auto;
            white-space: pre-wrap;
            max-height: 400px;
            overflow-y: auto;
            line-height: 1.5;
        }}
        
        .loading {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: #3b82f6;
            font-weight: 500;
            padding: 1rem;
        }}
        
        .loading i {{
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        
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
            <div class="version">v2.0</div>
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
                Static Routes (52K+ RPS)
            </div>
            <div class="tab" onclick="showTab('cached')">
                <i class="fas fa-memory"></i>
                Cached Routes (45K+ RPS)
            </div>
            <div class="tab" onclick="showTab('dynamic')">
                <i class="fas fa-cogs"></i>
                Dynamic Routes (2K+ RPS)
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
                
                const contentType = response.headers.get('content-type');
                let data;
                
                if (contentType && contentType.includes('application/json')) {{
                    data = await response.json();
                }} else {{
                    const text = await response.text();
                    try {{
                        data = JSON.parse(text);
                    }} catch {{
                        data = {{ raw_response: text, content_type: contentType }};
                    }}
                }}
                
                const statusClass = response.ok ? 'status-200' : `status-${{response.status}}`;
                responseContainer.innerHTML = `
                    <div class="response-header">
                        <h5><i class="fas fa-arrow-left"></i> Response</h5>
                        <span class="${{statusClass}}" style="font-weight: 600;">
                            ${{response.status}} ${{response.statusText}} (${{Math.round(end - start)}}ms)
                        </span>
                    </div>
                    <div class="response-body">${{JSON.stringify(data, null, 2)}}</div>
                `;
            }} catch (error) {{
                responseContainer.innerHTML = `
                    <div class="response-header">
                        <h5><i class="fas fa-exclamation-triangle"></i> Error</h5>
                        <span class="status-500">Request Failed</span>
                    </div>
                    <div class="response-body">${{JSON.stringify({{ error: error.message }}, null, 2)}}</div>
                `;
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
        
        all_routes = static_routes + cached_routes + dynamic_routes
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sufast API Documentation</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #fafafa;
            color: #3b4151;
            line-height: 1.5;
        }}
        
        .swagger-ui {{
            max-width: 1460px;
            margin: 0 auto;
            padding: 0;
        }}
        
        .topbar {{
            background: #89bf04;
            padding: 10px 0;
        }}
        
        .topbar-wrapper {{
            max-width: 1460px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            align-items: center;
        }}
        
        .topbar .link {{
            color: #fff;
            text-decoration: none;
            font-size: 24px;
            font-weight: bold;
        }}
        
        .information-container {{
            background: #fff;
            border-bottom: 1px solid #ebebeb;
            padding: 20px;
        }}
        
        .info {{
            max-width: 1460px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        
        .info .title {{
            color: #3b4151;
            font-family: sans-serif;
            font-size: 36px;
            margin-bottom: 10px;
            font-weight: normal;
        }}
        
        .info .description {{
            color: #3b4151;
            font-size: 14px;
        }}
        
        .scheme-container {{
            background: #fff;
            border-bottom: 1px solid #ebebeb;
            padding: 20px;
        }}
        
        .schemes {{
            max-width: 1460px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        
        .schemes .schemes-title {{
            color: #3b4151;
            font-size: 12px;
            font-weight: bold;
            margin-right: 12px;
        }}
        
        .operations-container {{
            max-width: 1460px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .operation-tag-content {{
            margin-bottom: 20px;
        }}
        
        .opblock-tag {{
            border-bottom: 1px solid rgba(59, 65, 81, 0.3);
            color: #3b4151;
            font-size: 24px;
            margin: 0 0 20px;
            padding: 0 0 5px;
            font-weight: normal;
        }}
        
        .opblock {{
            border: 1px solid #d3d3d3;
            border-radius: 4px;
            box-shadow: 0 0 3px rgba(0,0,0,0.19);
            margin: 0 0 15px;
            background: #fff;
        }}
        
        .opblock-summary {{
            padding: 10px 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
        }}
        
        .opblock.is-open .opblock-summary {{
            border-bottom: 1px solid #d3d3d3;
        }}
        
        .opblock-summary-method {{
            background: #61affe;
            border-radius: 3px;
            color: #fff;
            font-family: sans-serif;
            font-size: 14px;
            font-weight: 700;
            min-width: 80px;
            padding: 6px 15px;
            text-align: center;
            text-shadow: 0 1px 0 rgba(0,0,0,0.1);
            margin-right: 10px;
        }}
        
        .opblock-summary-method.get {{ background: #61affe; }}
        .opblock-summary-method.post {{ background: #49cc90; }}
        .opblock-summary-method.put {{ background: #fca130; }}
        .opblock-summary-method.delete {{ background: #f93e3e; }}
        
        .opblock-summary-path {{
            color: #3b4151;
            font-family: monospace;
            font-size: 16px;
            font-weight: 600;
            flex: 1;
        }}
        
        .opblock-summary-description {{
            color: #3b4151;
            font-size: 13px;
        }}
        
        .opblock-body {{
            padding: 20px;
            display: none;
        }}
        
        .opblock.is-open .opblock-body {{
            display: block;
        }}
        
        .opblock-description-wrapper {{
            margin-bottom: 15px;
        }}
        
        .opblock-description {{
            color: #3b4151;
            font-size: 14px;
        }}
        
        .opblock-section-header {{
            background: rgba(255,255,255,0.8);
            border-bottom: 1px solid rgba(59,65,81,0.2);
            font-size: 14px;
            font-weight: bold;
            margin: 0 0 10px;
            padding: 8px 0;
            color: #3b4151;
        }}
        
        .parameters-container {{
            margin-bottom: 20px;
        }}
        
        .parameter {{
            border-bottom: 1px solid #ebebeb;
            padding: 10px 0;
        }}
        
        .parameter:last-child {{
            border-bottom: none;
        }}
        
        .parameter-name {{
            color: #3b4151;
            font-family: monospace;
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 5px;
        }}
        
        .parameter-type {{
            color: #3b4151;
            font-size: 12px;
            margin-bottom: 5px;
        }}
        
        .parameter-input {{
            border: 1px solid #d9d9d9;
            border-radius: 4px;
            font-size: 14px;
            padding: 8px 12px;
            width: 100%;
            max-width: 300px;
        }}
        
        .parameter-input:focus {{
            border-color: #61affe;
            outline: none;
            box-shadow: 0 0 0 1px #61affe;
        }}
        
        .btn {{
            background: #4990e2;
            border: none;
            border-radius: 4px;
            color: #fff;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            padding: 10px 20px;
            margin-right: 10px;
            margin-bottom: 10px;
        }}
        
        .btn:hover {{
            background: #4174c7;
        }}
        
        .btn.cancel {{
            background: transparent;
            border: 1px solid #888;
            color: #888;
        }}
        
        .btn.cancel:hover {{
            background: #f7f7f7;
        }}
        
        .responses-wrapper {{
            margin-top: 20px;
        }}
        
        .response {{
            margin-bottom: 10px;
        }}
        
        .response-col_status {{
            color: #3b4151;
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .response-col_description {{
            color: #3b4151;
            font-size: 14px;
            margin-bottom: 10px;
        }}
        
        .highlight-code {{
            background: #41444e;
            color: #fff;
            border-radius: 4px;
            padding: 15px;
            font-family: monospace;
            font-size: 12px;
            overflow-x: auto;
            white-space: pre;
        }}
        
        .loading {{
            color: #61affe;
            font-style: italic;
        }}
        
        .badge {{
            background: #89bf04;
            border-radius: 3px;
            color: #fff;
            font-size: 11px;
            font-weight: bold;
            padding: 2px 6px;
            margin-left: 10px;
        }}
        
        .performance-badge {{
            background: #666;
            border-radius: 3px;
            color: #fff;
            font-size: 10px;
            padding: 2px 5px;
            margin-left: 5px;
        }}
        
        .tier-static {{ background: #f93e3e; }}
        .tier-cached {{ background: #fca130; }}
        .tier-dynamic {{ background: #61affe; }}
        
        @media (max-width: 768px) {{
            .topbar-wrapper, .info, .schemes, .operations-container {{
                padding: 0 10px;
            }}
            
            .opblock-summary {{
                flex-direction: column;
                align-items: flex-start;
            }}
            
            .opblock-summary-method {{
                margin-bottom: 5px;
            }}
        }}
    </style>
</head>
<body>
    <div class="swagger-ui">
        <div class="topbar">
            <div class="topbar-wrapper">
                <a href="#" class="link">
                    🚀 Sufast API
                </a>
            </div>
        </div>
        
        <div class="information-container">
            <div class="info">
                <h2 class="title">Sufast Ultimate v2.0 API</h2>
                <div class="description">
                    Three-Tier Performance Architecture: Static (52K+ RPS), Cached (45K+ RPS), Dynamic (2K+ RPS)
                </div>
            </div>
        </div>
        
        <div class="scheme-container">
            <div class="schemes">
                <span class="schemes-title">Schemes:</span>
                <span>http</span>
            </div>
        </div>
        
        <div class="operations-container">
            <div class="operation-tag-content">
                <h3 class="opblock-tag">
                    🔥 Static Routes 
                    <span class="performance-badge tier-static">52,000+ RPS</span>
                </h3>
                {self._generate_fastapi_routes(static_routes)}
            </div>
            
            <div class="operation-tag-content">
                <h3 class="opblock-tag">
                    ⚡ Cached Routes 
                    <span class="performance-badge tier-cached">45,000+ RPS</span>
                </h3>
                {self._generate_fastapi_routes(cached_routes)}
            </div>
            
            <div class="operation-tag-content">
                <h3 class="opblock-tag">
                    🎯 Dynamic Routes 
                    <span class="performance-badge tier-dynamic">2,000+ RPS</span>
                </h3>
                {self._generate_fastapi_routes(dynamic_routes)}
            </div>
        </div>
    </div>
    
    <script>
        function toggleOperation(operationId) {{
            const operation = document.getElementById(operationId);
            operation.classList.toggle('is-open');
        }}
        
        async function executeRequest(path, method, operationId) {{
            const params = [];
            const paramInputs = document.querySelectorAll(`#${{operationId}} .parameter-input`);
            
            let url = path;
            for (const input of paramInputs) {{
                const paramName = input.dataset.param;
                const value = input.value.trim();
                if (!value) {{
                    alert(`Please enter a value for ${{paramName}}`);
                    input.focus();
                    return;
                }}
                url = url.replace(`{{${{paramName}}}}`, encodeURIComponent(value));
            }}
            
            const responseContainer = document.getElementById(`response-${{operationId}}`);
            responseContainer.innerHTML = '<div class="loading">Executing...</div>';
            
            try {{
                const response = await fetch(url, {{
                    method: method,
                    headers: {{
                        'Accept': 'application/json',
                        'Cache-Control': 'no-cache'
                    }}
                }});
                
                const contentType = response.headers.get('content-type');
                let data;
                
                if (contentType && contentType.includes('application/json')) {{
                    data = await response.json();
                }} else {{
                    const text = await response.text();
                    try {{
                        data = JSON.parse(text);
                    }} catch {{
                        data = {{ raw_response: text }};
                    }}
                }}
                
                responseContainer.innerHTML = `
                    <div class="response-col_status" style="color: ${{response.ok ? '#49cc90' : '#f93e3e'}}">
                        ${{response.status}} ${{response.statusText}}
                    </div>
                    <div class="highlight-code">${{JSON.stringify(data, null, 2)}}</div>
                `;
            }} catch (error) {{
                responseContainer.innerHTML = `
                    <div class="response-col_status" style="color: #f93e3e">Error</div>
                    <div class="highlight-code">${{JSON.stringify({{ error: error.message }}, null, 2)}}</div>
                `;
            }}
        }}
        
        function clearResponse(operationId) {{
            document.getElementById(`response-${{operationId}}`).innerHTML = '';
        }}
    </script>
</body>
</html>'''
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sufast API Documentation</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #fafafa;
            color: #333;
            line-height: 1.6;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            color: white;
            padding: 2rem 0;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        
        .header p {{
            font-size: 1.1rem;
            opacity: 0.9;
            margin-bottom: 1rem;
        }}
        
        .performance-badges {{
            display: flex;
            justify-content: center;
            gap: 1rem;
            flex-wrap: wrap;
        }}
        
        .performance-badge {{
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            padding: 0.5rem 1rem;
            border-radius: 25px;
            font-size: 0.9rem;
            font-weight: 500;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        .docs-nav {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            margin-bottom: 2rem;
            overflow: hidden;
        }}
        
        .nav-tabs {{
            display: flex;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        .nav-tab {{
            flex: 1;
            padding: 1rem 1.5rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            font-weight: 500;
            border-bottom: 3px solid transparent;
        }}
        
        .nav-tab:hover {{
            background: #f9fafb;
        }}
        
        .nav-tab.active {{
            background: #eff6ff;
            border-bottom-color: #3b82f6;
            color: #1e40af;
        }}
        
        .tab-content {{
            display: none;
            padding: 2rem;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        .tier-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}
        
        .tier-icon {{
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }}
        
        .tier-static .tier-icon {{
            background: linear-gradient(135deg, #dc2626, #ef4444);
        }}
        
        .tier-cached .tier-icon {{
            background: linear-gradient(135deg, #d97706, #f59e0b);
        }}
        
        .tier-dynamic .tier-icon {{
            background: linear-gradient(135deg, #2563eb, #3b82f6);
        }}
        
        .tier-info {{
            flex: 1;
        }}
        
        .tier-title {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 0.25rem;
        }}
        
        .tier-description {{
            color: #6b7280;
            font-size: 0.95rem;
        }}
        
        .route-count {{
            background: #f3f4f6;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.9rem;
            color: #374151;
        }}
        
        .endpoint {{
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            margin-bottom: 1rem;
            overflow: hidden;
            transition: box-shadow 0.2s ease;
        }}
        
        .endpoint:hover {{
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        
        .endpoint-header {{
            padding: 1rem 1.5rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: background-color 0.2s ease;
        }}
        
        .endpoint-header:hover {{
            background: #f9fafb;
        }}
        
        .endpoint-left {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        
        .method-badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .method-get {{
            background: #dcfdf7;
            color: #065f46;
        }}
        
        .method-post {{
            background: #dbeafe;
            color: #1e40af;
        }}
        
        .method-put {{
            background: #fef3c7;
            color: #92400e;
        }}
        
        .method-delete {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        .endpoint-path {{
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-weight: 500;
            font-size: 1rem;
        }}
        
        .performance-info {{
            background: #eff6ff;
            color: #1e40af;
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 500;
        }}
        
        .endpoint-description {{
            color: #6b7280;
            font-size: 0.9rem;
        }}
        
        .endpoint-content {{
            display: none;
            padding: 1.5rem;
            background: #fafafa;
            border-top: 1px solid #e5e7eb;
        }}
        
        .endpoint-content.active {{
            display: block;
        }}
        
        .parameters {{
            margin: 1rem 0;
        }}
        
        .parameters h4 {{
            margin-bottom: 0.75rem;
            color: #374151;
            font-weight: 600;
        }}
        
        .param-row {{
            display: grid;
            grid-template-columns: 120px 80px 1fr;
            gap: 1rem;
            align-items: center;
            margin-bottom: 0.75rem;
            padding: 0.75rem;
            background: white;
            border-radius: 6px;
            border: 1px solid #e5e7eb;
        }}
        
        .param-name {{
            font-weight: 600;
            color: #374151;
        }}
        
        .param-type {{
            background: #f3f4f6;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            color: #6b7280;
            text-align: center;
        }}
        
        .param-input {{
            width: 100%;
            padding: 0.5rem 0.75rem;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            font-size: 0.9rem;
            transition: border-color 0.2s ease;
        }}
        
        .param-input:focus {{
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }}
        
        .try-it-section {{
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
            margin-top: 1rem;
        }}
        
        .try-button {{
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.2s ease;
        }}
        
        .try-button:hover {{
            background: linear-gradient(135deg, #1d4ed8, #1e40af);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        }}
        
        .response-section {{
            margin-top: 1rem;
        }}
        
        .response-header {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.5rem;
        }}
        
        .response-status {{
            font-weight: 600;
            color: #374151;
        }}
        
        .response-box {{
            background: #1f2937;
            color: #f9fafb;
            padding: 1rem;
            border-radius: 6px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.85rem;
            overflow-x: auto;
            white-space: pre-wrap;
            line-height: 1.5;
            max-height: 400px;
            overflow-y: auto;
        }}
        
        .loading {{
            display: none;
            color: #3b82f6;
            font-style: italic;
            padding: 0.5rem 0;
        }}
        
        .overview-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }}
        
        .overview-card {{
            background: white;
            padding: 2rem;
            border-radius: 12px;
            border: 1px solid #e5e7eb;
            text-align: center;
            transition: transform 0.2s ease;
        }}
        
        .overview-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }}
        
        .overview-icon {{
            width: 60px;
            height: 60px;
            border-radius: 15px;
            margin: 0 auto 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }}
        
        .overview-count {{
            font-size: 2.5rem;
            font-weight: 700;
            margin: 1rem 0 0.5rem;
        }}
        
        .overview-title {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}
        
        .overview-description {{
            color: #6b7280;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }}
        
        .overview-performance {{
            font-weight: 600;
            font-size: 0.9rem;
        }}
        
        .test-section {{
            background: white;
            padding: 2rem;
            border-radius: 12px;
            border: 1px solid #e5e7eb;
            margin-top: 2rem;
        }}
        
        .test-results {{
            margin-top: 1rem;
        }}
        
        .test-result-item {{
            margin: 0.5rem 0;
            padding: 0.75rem;
            border-radius: 6px;
            border-left: 4px solid;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9rem;
        }}
        
        .test-success {{
            background: #f0fdf4;
            border-left-color: #16a34a;
            color: #15803d;
        }}
        
        .test-error {{
            background: #fef2f2;
            border-left-color: #dc2626;
            color: #dc2626;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 1rem;
            }}
            
            .nav-tabs {{
                flex-wrap: wrap;
            }}
            
            .nav-tab {{
                flex: 1;
                min-width: 120px;
            }}
            
            .param-row {{
                grid-template-columns: 1fr;
                gap: 0.5rem;
            }}
            
            .overview-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Sufast API Documentation</h1>
        <p>Auto-Generated Interactive API Explorer</p>
        <div class="performance-badges">
            <div class="performance-badge">Static: 52K+ RPS</div>
            <div class="performance-badge">Cached: 45K+ RPS</div>
            <div class="performance-badge">Dynamic: 2K+ RPS</div>
        </div>
    </div>

    <div class="container">
        <div class="docs-nav">
            <div class="nav-tabs">
                <div class="nav-tab active" onclick="showTab('static')">🔥 Static Routes</div>
                <div class="nav-tab" onclick="showTab('cached')">⚡ Cached Routes</div>
                <div class="nav-tab" onclick="showTab('dynamic')">🎯 Dynamic Routes</div>
                <div class="nav-tab" onclick="showTab('overview')">📊 Overview</div>
            </div>

            <!-- Static Routes Tab -->
            <div id="static" class="tab-content active">
                <div class="tier-header tier-static">
                    <div class="tier-icon">🔥</div>
                    <div class="tier-info">
                        <div class="tier-title">Static Routes</div>
                        <div class="tier-description">Pre-compiled responses for maximum performance (52,000+ RPS)</div>
                    </div>
                    <div class="route-count">{len(static_routes)} routes</div>
                </div>
                
                {self._generate_route_html(static_routes, 'static')}
            </div>

            <!-- Cached Routes Tab -->
            <div id="cached" class="tab-content">
                <div class="tier-header tier-cached">
                    <div class="tier-icon">⚡</div>
                    <div class="tier-info">
                        <div class="tier-title">Cached Routes</div>
                        <div class="tier-description">Smart caching with configurable TTL (45,000+ RPS)</div>
                    </div>
                    <div class="route-count">{len(cached_routes)} routes</div>
                </div>
                
                {self._generate_route_html(cached_routes, 'cached')}
            </div>

            <!-- Dynamic Routes Tab -->
            <div id="dynamic" class="tab-content">
                <div class="tier-header tier-dynamic">
                    <div class="tier-icon">🎯</div>
                    <div class="tier-info">
                        <div class="tier-title">Dynamic Routes</div>
                        <div class="tier-description">Real-time processing with parameter extraction (2,000+ RPS)</div>
                    </div>
                    <div class="route-count">{len(dynamic_routes)} routes</div>
                </div>
                
                {self._generate_route_html(dynamic_routes, 'dynamic')}
            </div>

            <!-- Overview Tab -->
            <div id="overview" class="tab-content">
                <div class="tier-header">
                    <div class="tier-icon" style="background: linear-gradient(135deg, #6366f1, #8b5cf6);">📊</div>
                    <div class="tier-info">
                        <div class="tier-title">API Overview</div>
                        <div class="tier-description">Complete summary of your Sufast application</div>
                    </div>
                </div>
                
                <div class="overview-grid">
                    <div class="overview-card">
                        <div class="overview-icon" style="background: linear-gradient(135deg, #dc2626, #ef4444);">🔥</div>
                        <div class="overview-count" style="color: #dc2626;">{len(static_routes)}</div>
                        <div class="overview-title">Static Routes</div>
                        <div class="overview-description">Ultra-fast pre-compiled responses</div>
                        <div class="overview-performance" style="color: #dc2626;">52,000+ RPS</div>
                    </div>
                    
                    <div class="overview-card">
                        <div class="overview-icon" style="background: linear-gradient(135deg, #d97706, #f59e0b);">⚡</div>
                        <div class="overview-count" style="color: #d97706;">{len(cached_routes)}</div>
                        <div class="overview-title">Cached Routes</div>
                        <div class="overview-description">Intelligent caching with TTL</div>
                        <div class="overview-performance" style="color: #d97706;">45,000+ RPS</div>
                    </div>
                    
                    <div class="overview-card">
                        <div class="overview-icon" style="background: linear-gradient(135deg, #2563eb, #3b82f6);">🎯</div>
                        <div class="overview-count" style="color: #2563eb;">{len(dynamic_routes)}</div>
                        <div class="overview-title">Dynamic Routes</div>
                        <div class="overview-description">Real-time parameter processing</div>
                        <div class="overview-performance" style="color: #2563eb;">2,000+ RPS</div>
                    </div>
                </div>
                
                <div class="test-section">
                    <h3>🚀 Quick API Test</h3>
                    <p style="color: #6b7280; margin-bottom: 1rem;">Test all your endpoints to verify they're working correctly</p>
                    <button class="try-button" onclick="runQuickTests()">Run All Tests</button>
                    <div id="quick-test-results" class="test-results"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function showTab(tabName) {{
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(tab => tab.classList.remove('active'));
            
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }}

        function toggleEndpoint(endpointId) {{
            const content = document.getElementById(endpointId);
            const isActive = content.classList.contains('active');
            
            document.querySelectorAll('.endpoint-content').forEach(ep => ep.classList.remove('active'));
            
            if (!isActive) {{
                content.classList.add('active');
            }}
        }}

        async function tryEndpoint(endpoint, responseKey) {{
            const loadingId = 'loading-' + responseKey;
            const responseId = 'response-' + responseKey;
            
            // Show loading state
            const loadingEl = document.getElementById(loadingId);
            const responseEl = document.getElementById(responseId);
            
            if (loadingEl) loadingEl.style.display = 'block';
            if (responseEl) responseEl.style.display = 'none';
            
            try {{
                const response = await fetch(endpoint, {{
                    method: 'GET',
                    headers: {{
                        'Accept': 'application/json',
                        'Cache-Control': 'no-cache'
                    }}
                }});
                
                const contentType = response.headers.get('content-type');
                let data;
                
                if (contentType && contentType.includes('application/json')) {{
                    data = await response.json();
                }} else {{
                    const text = await response.text();
                    try {{
                        data = JSON.parse(text);
                    }} catch {{
                        data = {{ raw_response: text, content_type: contentType }};
                    }}
                }}
                
                if (responseEl) {{
                    responseEl.innerHTML = `
                        <div class="response-status" style="color: ${{response.ok ? '#16a34a' : '#dc2626'}}; margin-bottom: 0.5rem;">
                            Status: ${{response.status}} ${{response.statusText}}
                        </div>
                        <pre style="background: #f8fafc; padding: 1rem; border-radius: 6px; overflow-x: auto; font-size: 0.9rem;">${{JSON.stringify(data, null, 2)}}</pre>
                    `;
                    responseEl.style.display = 'block';
                }}
            }} catch (error) {{
                if (responseEl) {{
                    responseEl.innerHTML = `
                        <div class="response-status" style="color: #dc2626; margin-bottom: 0.5rem;">
                            Error: ${{error.message}}
                        </div>
                        <pre style="background: #fef2f2; padding: 1rem; border-radius: 6px; color: #dc2626;">${{error.stack || error.message}}</pre>
                    `;
                    responseEl.style.display = 'block';
                }}
            }}
            
            if (loadingEl) loadingEl.style.display = 'none';
        }}

        async function tryDynamicEndpoint(basePath, params, responseKey) {{
            let endpoint = basePath;
            
            // Build the endpoint URL with parameters
            for (const param of params) {{
                const inputEl = document.getElementById(param.inputId);
                if (!inputEl) {{
                    alert('Input field not found for parameter: ' + param.name);
                    return;
                }}
                
                const value = inputEl.value.trim();
                if (!value) {{
                    alert('Please enter a value for parameter: ' + param.name);
                    inputEl.focus();
                    return;
                }}
                
                endpoint = endpoint.replace('{{' + param.name + '}}', encodeURIComponent(value));
            }}
            
            // Call the regular tryEndpoint function
            await tryEndpoint(endpoint, responseKey);
        }}

        async function runQuickTests() {{
            const testResults = document.getElementById('quick-test-results');
            testResults.innerHTML = '<div style="display:block; text-align:center; padding:1rem; color:#3b82f6;"><div class="loading-spinner" style="display:inline-block; width:20px; height:20px; border:2px solid #3b82f6; border-radius:50%; border-top:transparent; animation:spin 1s linear infinite; margin-right:0.5rem;"></div>Running comprehensive API tests...</div>';
            
            // Get all non-parameterized routes for testing
            const testableRoutes = [];
            {', '.join([f'testableRoutes.push({{path: "{route["path"]}", method: "{route["method"]}", tier: "{route["tier"]}"}});' for route in static_routes + cached_routes + [route for route in dynamic_routes if not route['parameters']]])}
            
            const results = [];
            let passed = 0;
            let failed = 0;
            
            for (const route of testableRoutes) {{
                try {{
                    const start = performance.now();
                    const response = await fetch(route.path, {{
                        method: route.method,
                        headers: {{
                            'Accept': 'application/json',
                            'Cache-Control': 'no-cache'
                        }}
                    }});
                    const end = performance.now();
                    
                    const success = response.ok;
                    if (success) passed++;
                    else failed++;
                    
                    results.push({{
                        path: route.path,
                        method: route.method,
                        tier: route.tier,
                        status: response.status,
                        time: Math.round(end - start),
                        success: success
                    }});
                }} catch (error) {{
                    failed++;
                    results.push({{
                        path: route.path,
                        method: route.method,
                        tier: route.tier,
                        error: error.message,
                        success: false
                    }});
                }}
            }}
            
            // Generate results HTML
            let resultHtml = `
                <div style="background: #f8fafc; padding: 1.5rem; border-radius: 8px; margin: 1rem 0;">
                    <div style="display: flex; gap: 2rem; margin-bottom: 1rem;">
                        <div style="text-align: center;">
                            <div style="font-size: 1.5rem; font-weight: bold; color: #16a34a;">${{passed}}</div>
                            <div style="color: #6b7280; font-size: 0.9rem;">Passed</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 1.5rem; font-weight: bold; color: #dc2626;">${{failed}}</div>
                            <div style="color: #6b7280; font-size: 0.9rem;">Failed</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 1.5rem; font-weight: bold; color: #3b82f6;">${{results.length}}</div>
                            <div style="color: #6b7280; font-size: 0.9rem;">Total</div>
                        </div>
                    </div>
                </div>
                <div style="max-height: 400px; overflow-y: auto;">
            `;
            
            results.forEach(result => {{
                const tierColors = {{
                    'static': '#dc2626',
                    'cached': '#d97706', 
                    'dynamic': '#3b82f6'
                }};
                const tierColor = tierColors[result.tier] || '#6b7280';
                const className = result.success ? 'test-success' : 'test-error';
                const icon = result.success ? '✅' : '❌';
                
                resultHtml += `
                    <div class="test-result-item ${{className}}" style="margin-bottom: 0.5rem; padding: 0.75rem; border-radius: 6px; display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center; gap: 0.75rem;">
                            ${{icon}}
                            <span style="background: ${{tierColor}}; color: white; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.7rem; font-weight: bold; text-transform: uppercase;">${{result.tier}}</span>
                            <span style="font-family: 'Monaco', 'Menlo', monospace; font-weight: 500;">${{result.method}} ${{result.path}}</span>
                        </div>
                        <div style="font-size: 0.9rem; color: #6b7280;">
                            ${{result.success ? 
                                `${{result.status}} (${{result.time}}ms)` : 
                                `Error: ${{result.error}}`
                            }}
                        </div>
                    </div>
                `;
            }});
            
            resultHtml += '</div>';
            testResults.innerHTML = resultHtml;
        }}
        
        // Add CSS for loading spinner animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        `;
        document.head.appendChild(style);
        
        function fillExampleValues(routeId) {{
            // Fill all parameter inputs with their example values
            const inputs = document.querySelectorAll(`[id^="param-${{routeId}}-"]`);
            inputs.forEach(input => {{
                const placeholder = input.getAttribute('placeholder');
                if (placeholder) {{
                    // Extract example from placeholder or use the value attribute
                    input.value = input.getAttribute('value') || input.getAttribute('placeholder').replace('Enter ', '');
                }}
            }});
        }}
    </script>
</body>
</html>'''

    def _generate_route_html(self, routes, tier_type):
        """Generate HTML for a specific tier of routes."""
        if not routes:
            return '''<div style="text-align: center; padding: 3rem; color: #6b7280;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📭</div>
                <h3 style="margin-bottom: 0.5rem;">No routes found</h3>
                <p>No routes have been registered in this tier yet.</p>
            </div>'''
        
        html = ""
        for i, route in enumerate(routes):
            route_id = f"{tier_type}-{i}"
            param_inputs = []
            
            # Generate example values for common parameter names
            def get_example_value(param_name):
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
            
            # Generate parameter inputs for dynamic routes
            if route['parameters']:
                param_html = '''
                    <div class="parameters">
                        <h4 style="margin-bottom: 1rem; color: #374151; display: flex; align-items: center; gap: 0.5rem;">
                            <span>🔧</span> Parameters
                        </h4>
                        <div style="background: #eff6ff; padding: 1rem; border-radius: 6px; margin-bottom: 1rem; border-left: 4px solid #3b82f6;">
                            <p style="margin: 0; color: #1e40af; font-size: 0.9rem;">
                                💡 <strong>Tip:</strong> Fill in the parameters below and click "Try it out" to test this endpoint with real data.
                            </p>
                        </div>
                '''
                for param in route['parameters']:
                    param_input_id = f"param-{route_id}-{param['name']}"
                    example_value = get_example_value(param['name'])
                    param_inputs.append({
                        'name': param['name'],
                        'inputId': param_input_id
                    })
                    param_html += f'''
                        <div class="param-row">
                            <div class="param-name">{param['name']}</div>
                            <div class="param-type">{param['type']}</div>
                            <div style="display: flex; flex-direction: column; gap: 0.25rem;">
                                <input type="text" id="{param_input_id}" class="param-input" 
                                       placeholder="Enter {param['name']}" value="{example_value}">
                                <small style="color: #6b7280; font-size: 0.8rem;">Example: {example_value}</small>
                            </div>
                        </div>
                    '''
                param_html += '</div>'
            else:
                param_html = ''
            
            # Generate try button based on route type
            if route['parameters']:
                try_button_html = f'''
                    <div class="try-it-section">
                        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                            <button class="try-button" onclick="tryDynamicEndpoint('{route['path']}', {param_inputs}, '{route_id}')">
                                🚀 Try it out
                            </button>
                            <button class="try-button" onclick="fillExampleValues('{route_id}')" 
                                    style="background: linear-gradient(135deg, #059669, #047857);">
                                📝 Fill Examples
                            </button>
                        </div>
                        <div class="response-section">
                            <div class="response-header">
                                <h4 style="margin: 0; color: #374151;">Response</h4>
                            </div>
                            <div id="loading-{route_id}" class="loading" style="display: none;">
                                <div style="display: flex; align-items: center; gap: 0.5rem; color: #3b82f6;">
                                    <div style="width: 16px; height: 16px; border: 2px solid #3b82f6; border-radius: 50%; border-top: transparent; animation: spin 1s linear infinite;"></div>
                                    Making request...
                                </div>
                            </div>
                            <div id="response-{route_id}" class="response-body" style="display: none;"></div>
                        </div>
                    </div>
                '''
            else:
                try_button_html = f'''
                    <div class="try-it-section">
                        <button class="try-button" onclick="tryEndpoint('{route['path']}', '{route_id}')">
                            🚀 Try it out
                        </button>
                        <div class="response-section">
                            <div class="response-header">
                                <h4 style="margin: 0; color: #374151;">Response</h4>
                            </div>
                            <div id="loading-{route_id}" class="loading" style="display: none;">
                                <div style="display: flex; align-items: center; gap: 0.5rem; color: #3b82f6;">
                                    <div style="width: 16px; height: 16px; border: 2px solid #3b82f6; border-radius: 50%; border-top: transparent; animation: spin 1s linear infinite;"></div>
                                    Making request...
                                </div>
                            </div>
                            <div id="response-{route_id}" class="response-body" style="display: none;"></div>
                        </div>
                    </div>
                '''
            
            # Get performance info based on tier
            performance_info = {
                'static': '52,000+ RPS (Pre-compiled)',
                'cached': '45,000+ RPS (Cached)',
                'dynamic': '2,000+ RPS (Real-time)'
            }.get(tier_type, 'Unknown')
            
            html += f'''
                <div class="endpoint-card">
                    <div class="endpoint-header" onclick="toggleEndpoint('{route_id}')">
                        <div class="endpoint-left">
                            <div class="method-badge method-{route['method'].lower()}">{route['method']}</div>
                            <div class="endpoint-path">{route['path']}</div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <div class="performance-info">{performance_info}</div>
                            <div style="color: #6b7280;">▼</div>
                        </div>
                    </div>
                    
                    <div class="endpoint-content" id="{route_id}">
                        <div class="endpoint-description">
                            {route.get('description', 'No description available')}
                        </div>
                        
                        {param_html}
                        {try_button_html}
                    </div>
                </div>
            '''
        
        return html

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
                'static': '52,000+ RPS',
                'cached': '45,000+ RPS', 
                'dynamic': '2,000+ RPS'
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
