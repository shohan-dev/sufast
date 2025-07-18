import ctypes
import json
import platform
import warnings
import os
import sys
from typing import Dict, Any, Callable, List, Optional

# Set up proper import paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    import pkg_resources
except ImportError:
    pkg_resources = None

from .request import Request, Response, json_response
from .middleware import MiddlewareStack, Middleware
from .routing import Router, RouteGroup
from .templates import TemplateEngine, StaticFileHandler, JinjaTemplateEngine
from .database import Database, DatabaseConnection

class App:
    """Main Sufast application class with enhanced dynamic routing support."""
    
    def __init__(self, debug=False, cors=True):
        self.debug = debug
        self.cors = cors
        self.router = Router()
        self.route = self.router  # Alias for convenience
        self.middleware = MiddlewareStack()
        self.template_engine: Optional[TemplateEngine] = None
        self.static_handler: Optional[StaticFileHandler] = None
        self.database: Optional[Database] = None
        
        # Enhanced routing support
        self.request_handlers: Dict[str, Dict[str, Callable]] = {
            'GET': {}, 'POST': {}, 'PUT': {}, 'DELETE': {}, 'PATCH': {}, 'OPTIONS': {}
        }
        self.routes: Dict[str, Dict[str, str]] = {
            'GET': {}, 'POST': {}, 'PUT': {}, 'DELETE': {}, 'PATCH': {}, 'OPTIONS': {}
        }
        
        # Dynamic library detection and loading
        self.library_name = self._detect_library()
        self.dll_path = self._resolve_library_path()

    def _detect_library(self):
        """Detect the appropriate shared library for the current platform."""
        if platform.system() == "Windows":
            return "sufast_server.dll"
        elif platform.system() == "Linux":
            return "sufast_server.so"
        elif platform.system() == "Darwin":
            return "sufast_server.dylib"
        else:
            raise RuntimeError(f"❌ Unsupported platform: {platform.system()}")

    def _resolve_library_path(self):
        """Resolve the path to the shared library."""
        try:
            if pkg_resources:
                dll_path = pkg_resources.resource_filename("sufast", self.library_name)
            else:
                dll_path = os.path.join(os.path.dirname(__file__), self.library_name)
                if not os.path.exists(dll_path):
                    # Try alternative locations
                    alt_paths = [
                        os.path.join(os.path.dirname(os.path.dirname(__file__)), self.library_name),
                        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "rust-core", "target", "release", self.library_name),
                    ]
                    for path in alt_paths:
                        if os.path.exists(path):
                            dll_path = path
                            break
                    else:
                        raise FileNotFoundError(f"Library {self.library_name} not found in any expected location")
            
            return dll_path
        except Exception as e:
            raise RuntimeError(f"Could not resolve {self.library_name} location: {e}")

    def _load_sufast_lib(self):
        try:
            full_path = os.path.abspath(self.dll_path)
            if platform.system() == "Linux":
                if not os.path.isfile(full_path):
                    raise FileNotFoundError(f"Linux .so file not found at: {full_path}")
                if not os.access(full_path, os.R_OK):
                    raise PermissionError(f"No read access to .so file: {full_path}")
            lib = ctypes.CDLL(full_path)
            
            # Set up function signatures for dynamic routing
            lib.set_routes.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t]
            lib.set_routes.restype = ctypes.c_bool
            lib.set_python_handler.argtypes = [ctypes.c_void_p]
            lib.set_python_handler.restype = ctypes.c_bool
            lib.start_server.argtypes = [ctypes.c_bool, ctypes.c_uint16]
            lib.start_server.restype = ctypes.c_bool
            
            return lib
        except OSError as e:
            raise ImportError(
                f"❌ Failed to load shared library at {full_path}:\n{str(e)}\n"
                "💡 Tips:\n"
                "  - Check the file exists and is readable\n"
                "  - Check 'ldd' output on Linux for missing dependencies\n"
                "  - Ensure Python and library architectures match (both 64-bit or 32-bit)\n"
                "  - Check file permissions\n"
            ) from e

    def _python_request_handler(self, request_json_ptr):
        """Handle dynamic requests from Rust core."""
        try:
            # Convert C string to Python string
            request_json = ctypes.string_at(request_json_ptr).decode('utf-8')
            request_data = json.loads(request_json)
            
            print(f"🐍 Python handler called: {request_data['method']} {request_data['path']}")
            print(f"📋 Handler: {request_data['handler_name']}")
            print(f"🔗 Path params: {request_data['path_params']}")
            
            # Find the route handler by searching all routes
            handler_name = request_data['handler_name']
            route_handler = None
            
            # Search in router.routes list
            all_routes = self.router.routes[:] if hasattr(self.router, 'routes') else []
            for group in getattr(self.router, 'route_groups', []):
                all_routes.extend(group.routes)
                
            for route in all_routes:
                if hasattr(route, 'handler') and route.handler.__name__ == handler_name:
                    route_handler = route.handler
                    break
            
            if route_handler:
                # Create Request object with path parameters
                request = Request(
                    method=request_data['method'],
                    path=request_data['path'],
                    headers=request_data.get('headers', {}),
                    body=request_data.get('body', ''),
                    query_params=request_data.get('query_params', {}),
                    path_params=request_data.get('path_params', {})
                )
                
                # Call the handler
                response = route_handler(request)
                
                # Handle different response types
                if hasattr(response, 'to_dict'):
                    # Response object with to_dict method
                    response_dict = response.to_dict()
                elif hasattr(response, 'status_code') and hasattr(response, 'body'):
                    # Response object with status_code and body attributes
                    response_dict = {
                        'status_code': response.status_code,
                        'headers': getattr(response, 'headers', {'Content-Type': 'application/json'}),
                        'body': response.body
                    }
                elif isinstance(response, str):
                    # Plain string response (like HTML)
                    content_type = 'text/html' if '<html>' in response.lower() else 'text/plain'
                    response_dict = {
                        'status_code': 200,
                        'headers': {'Content-Type': content_type},
                        'body': response
                    }
                elif isinstance(response, dict):
                    # Plain dict response
                    response_dict = {
                        'status_code': 200,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps(response)
                    }
                else:
                    # Any other type, try to serialize
                    response_dict = {
                        'status_code': 200,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps(response) if response is not None else ''
                    }
                
                response_json = json.dumps(response_dict)
                print(f"✅ Response sent")
                
                # Create persistent string buffer and return void pointer
                result_bytes = response_json.encode('utf-8')
                self._last_response_buffer = ctypes.create_string_buffer(result_bytes)
                return ctypes.cast(self._last_response_buffer, ctypes.c_void_p).value
            else:
                print(f"❌ Handler not found: {handler_name}")
                error_response = {
                    'status_code': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': f'Handler {handler_name} not found'})
                }
                error_json = json.dumps(error_response)
                error_bytes = error_json.encode('utf-8')
                self._last_response_buffer = ctypes.create_string_buffer(error_bytes)
                return ctypes.cast(self._last_response_buffer, ctypes.c_void_p).value
                
        except Exception as e:
            print(f"❌ Python handler error: {e}")
            error_response = {
                'status_code': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': str(e)})
            }
            error_json = json.dumps(error_response)
            error_bytes = error_json.encode('utf-8')
            self._last_response_buffer = ctypes.create_string_buffer(error_bytes)
            return ctypes.cast(self._last_response_buffer, ctypes.c_void_p).value

    def get(self, path, middleware: List[Middleware] = None, name: str = None):
        """Register GET route with modern features."""
        def decorator(func):
            # Add to new router
            self.router.add_route('GET', path, func, middleware, name)
            # Also store for dynamic routing
            if 'GET' not in self.request_handlers:
                self.request_handlers['GET'] = {}
            self.request_handlers['GET'][func.__name__] = func
            return func
        return decorator

    def post(self, path, middleware: List[Middleware] = None, name: str = None):
        """Register POST route with modern features."""
        def decorator(func):
            self.router.add_route('POST', path, func, middleware, name)
            if 'POST' not in self.request_handlers:
                self.request_handlers['POST'] = {}
            self.request_handlers['POST'][func.__name__] = func
            return func
        return decorator

    def put(self, path, middleware: List[Middleware] = None, name: str = None):
        """Register PUT route with modern features."""
        def decorator(func):
            self.router.add_route('PUT', path, func, middleware, name)
            if 'PUT' not in self.request_handlers:
                self.request_handlers['PUT'] = {}
            self.request_handlers['PUT'][func.__name__] = func
            return func
        return decorator

    def patch(self, path, middleware: List[Middleware] = None, name: str = None):
        """Register PATCH route with modern features."""
        def decorator(func):
            self.router.add_route('PATCH', path, func, middleware, name)
            if 'PATCH' not in self.request_handlers:
                self.request_handlers['PATCH'] = {}
            self.request_handlers['PATCH'][func.__name__] = func
            return func
        return decorator

    def delete(self, path, middleware: List[Middleware] = None, name: str = None):
        """Register DELETE route with modern features."""
        def decorator(func):
            self.router.add_route('DELETE', path, func, middleware, name)
            if 'DELETE' not in self.request_handlers:
                self.request_handlers['DELETE'] = {}
            self.request_handlers['DELETE'][func.__name__] = func
            return func
        return decorator

    def options(self, path, middleware: List[Middleware] = None, name: str = None):
        """Register OPTIONS route with modern features."""
        def decorator(func):
            self.router.add_route('OPTIONS', path, func, middleware, name)
            if 'OPTIONS' not in self.request_handlers:
                self.request_handlers['OPTIONS'] = {}
            self.request_handlers['OPTIONS'][func.__name__] = func
            return func
        return decorator

    def run(self, port=8080, production=False):
        lib = self._load_sufast_lib()
        
        # Prepare routes for dynamic routing
        dynamic_routes = {}
        for method in ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]:
            dynamic_routes[method] = []
        
        # Get routes from router (all routes are in the routes list)
        all_routes = self.router.routes[:]
        
        # Also get routes from route groups
        for group in self.router.route_groups:
            all_routes.extend(group.routes)
            
        # Process all routes
        for route in all_routes:
            route_def = {
                'method': route.method,
                'path': route.path,
                'handler_name': route.handler.__name__,
                'middleware': [m.__class__.__name__ for m in route.middleware or []],
                'params': {}  # Will be filled by Rust during pattern compilation
            }
            dynamic_routes[route.method].append(route_def)
            print(f"📋 Found route: {route.method} {route.path} -> {route.handler.__name__}")
        
        # Convert to JSON and send to Rust
        json_routes = json.dumps(dynamic_routes).encode('utf-8')
        buffer = (ctypes.c_ubyte * len(json_routes)).from_buffer_copy(json_routes)

        print("\n🔧 Booting up ⚡ sufast web server engine...\n")
        print(f"🌐 Mode     : {'🔒 Production' if production else '🧪 Development'}")
        print(f"🔀  Routes   : {sum(len(routes) for routes in dynamic_routes.values())} registered")
        print(f"🚪 Port     : {port}")
        print("🟢 Status   : Server is up and running!")
        if not production:
            print(f"➡️  Visit    : http://localhost:{port}")
        print("🔄 Press Ctrl+C to stop the server.\n")

        # Register Python callback handler with correct signature  
        # The Rust side expects: extern "C" fn(*const c_char) -> *mut c_char
        callback_type = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_char_p)
        callback_func = callback_type(self._python_request_handler)
        if not lib.set_python_handler(callback_func):
            raise RuntimeError("❌ Failed to register Python callback handler.")

        if not lib.set_routes(buffer, len(json_routes)):
            raise RuntimeError("❌ sufast_server failed to accept route configuration.")

        if not lib.start_server(production, port):
            raise RuntimeError("❌ sufast_server failed to start.")
