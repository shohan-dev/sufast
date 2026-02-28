"""
Sufast - Hybrid Rust+Python Web Framework
=========================================
FastAPI-style API with Rust-powered performance.

Usage:
    from sufast import Sufast
    
    app = Sufast(title="My API", version="1.0.0")
    
    @app.get("/")
    async def root():
        return {"message": "Hello World"}
    
    @app.get("/users/{user_id}")
    async def get_user(user_id: int):
        return {"user_id": user_id}
    
    @app.post("/users")
    async def create_user(request):
        data = await request.json()
        return {"created": data}
    
    @app.websocket("/ws")
    async def ws_endpoint(websocket):
        await websocket.accept()
        async for msg in websocket.iter_text():
            await websocket.send_text(f"Echo: {msg}")
    
    app.run(host="0.0.0.0", port=8000, docs=True)
"""

import asyncio
import ctypes
import inspect
import json
import os
import re
import sys
import time
import secrets
import threading
import traceback
from pathlib import Path
from typing import (
    Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Type, Union
)
from functools import wraps
from datetime import datetime, timezone

from .request import Request, Response, json_response, html_response
from .exceptions import HTTPException, STATUS_PHRASES
from .websocket import WebSocket, WebSocketRoute, WebSocketState
from .background import BackgroundTasks
from .openapi import OpenAPIGenerator, extract_route_params, extract_function_info
from .swagger import generate_swagger_html, generate_redoc_html


# ===========================================================
# Route Storage
# ===========================================================

class RouteEntry:
    """Stores a single route definition."""
    
    __slots__ = (
        'method', 'path', 'handler', 'name', 'tags', 'group',
        'summary', 'description', 'deprecated', 'response_model',
        'status_code', 'request_body', 'query_parameters',
        'path_regex', 'param_names', 'param_types',
        'is_async', 'is_static', 'cache_ttl',
        'tier', 'middleware',
    )
    
    def __init__(self, method: str, path: str, handler: Callable, **kwargs):
        self.method = method.upper()
        self.path = path
        self.handler = handler
        self.name = kwargs.get('name', handler.__name__)
        self.tags = kwargs.get('tags', [])
        self.group = kwargs.get('group', '')
        self.summary = kwargs.get('summary', '')
        self.description = kwargs.get('description', '')
        self.deprecated = kwargs.get('deprecated', False)
        self.response_model = kwargs.get('response_model')
        self.status_code = kwargs.get('status_code', 200)
        self.request_body = kwargs.get('request_body')
        self.query_parameters = kwargs.get('query_parameters', [])
        self.is_async = asyncio.iscoroutinefunction(handler)
        self.is_static = kwargs.get('is_static', False)
        self.cache_ttl = kwargs.get('cache_ttl', 0)
        self.tier = kwargs.get('tier', 'dynamic')
        self.middleware = kwargs.get('middleware', [])
        
        # Compile path pattern
        self.param_names = []
        self.param_types = {}
        self.path_regex = self._compile(path)
    
    def _compile(self, path: str):
        """Compile path pattern into regex."""
        pattern = path
        self.param_names = []
        self.param_types = {}
        
        for match in re.finditer(r'\{(\w+)(?::(\w+))?\}', path):
            name = match.group(1)
            ptype = match.group(2) or 'str'
            self.param_names.append(name)
            self.param_types[name] = ptype
            
            type_patterns = {
                'str': r'[^/]+',
                'int': r'\d+',
                'float': r'\d+\.?\d*',
                'uuid': r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
                'slug': r'[a-z0-9-]+',
                'path': r'.+',
            }
            regex_part = type_patterns.get(ptype, r'[^/]+')
            full_match_str = match.group(0)
            pattern = pattern.replace(full_match_str, f'(?P<{name}>{regex_part})')
        
        return re.compile(f'^{pattern}$')
    
    def match(self, path: str) -> Optional[Dict[str, Any]]:
        """Match a path against this route and extract params."""
        m = self.path_regex.match(path)
        if not m:
            return None
        
        params = m.groupdict()
        # Type conversion
        for name, value in params.items():
            ptype = self.param_types.get(name, 'str')
            try:
                if ptype == 'int':
                    params[name] = int(value)
                elif ptype == 'float':
                    params[name] = float(value)
            except (ValueError, TypeError):
                return None
        
        return params
    
    def to_metadata(self) -> dict:
        """Convert to metadata dict for OpenAPI generation."""
        parameters = extract_route_params(self.path)
        
        # Extract info from function
        func_info = extract_function_info(self.handler)
        
        summary = self.summary or func_info.get('description', '') or f"{self.method} {self.path}"
        description = self.description or (self.handler.__doc__ or '').strip()
        
        meta = {
            'path': self.path,
            'method': self.method,
            'function_name': self.name,
            'summary': summary,
            'description': description,
            'detailed_description': self.description,
            'parameters': parameters,
            'query_parameters': self.query_parameters,
            'tags': self.tags,
            'group': self.group,
            'tier': self.tier,
            'cache_ttl': self.cache_ttl,
            'deprecated': self.deprecated,
            'status_code': self.status_code,
            'request_body': self.request_body,
            'operation_id': self.name,
        }
        
        return meta


class Router:
    """Stores and matches routes."""
    
    def __init__(self):
        self.routes: List[RouteEntry] = []
        self._exact_routes: Dict[str, RouteEntry] = {}  # "METHOD:/path" -> RouteEntry
        self._pattern_routes: List[RouteEntry] = []
    
    def add(self, route: RouteEntry):
        """Add a route."""
        self.routes.append(route)
        key = f"{route.method}:{route.path}"
        
        if route.param_names:
            self._pattern_routes.append(route)
        else:
            self._exact_routes[key] = route
    
    def find(self, method: str, path: str) -> Optional[Tuple[RouteEntry, Dict[str, Any]]]:
        """Find matching route. Returns (route, params) or None."""
        method = method.upper()
        
        # Try exact match first (fastest)
        key = f"{method}:{path}"
        if key in self._exact_routes:
            return self._exact_routes[key], {}
        
        # Try pattern routes
        for route in self._pattern_routes:
            if route.method != method:
                continue
            params = route.match(path)
            if params is not None:
                return route, params
        
        return None
    
    def get_all_metadata(self) -> List[dict]:
        """Get metadata for all routes."""
        return [r.to_metadata() for r in self.routes]


# ===========================================================
# Middleware
# ===========================================================

class MiddlewareWrapper:
    """Wraps middleware functions."""
    
    def __init__(self, func: Callable, type: str = "http"):
        self.func = func
        self.type = type
    
    async def __call__(self, request, call_next):
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(request, call_next)
        else:
            return self.func(request, call_next)


# ===========================================================
# Sufast Application
# ===========================================================

class APIRouter:
    """A group of routes that can be mounted on the main app.
    
    Usage:
        router = APIRouter(prefix="/api/v1", tags=["api"])
        
        @router.get("/users")
        async def list_users():
            return {"users": []}
        
        app.include_router(router)
    """
    
    def __init__(self, prefix: str = "", tags: List[str] = None, 
                 group: str = "", middleware: List[Callable] = None):
        self.prefix = prefix.rstrip("/")
        self.tags = tags or []
        self.group = group
        self.middleware = middleware or []
        self._routes: List[dict] = []
        self._ws_routes: List[dict] = []
    
    def _add_route(self, method: str, path: str, **kwargs):
        def decorator(func):
            self._routes.append({
                'method': method,
                'path': path,
                'handler': func,
                **kwargs
            })
            return func
        return decorator
    
    def get(self, path: str, **kwargs):
        return self._add_route("GET", path, **kwargs)
    
    def post(self, path: str, **kwargs):
        return self._add_route("POST", path, **kwargs)
    
    def put(self, path: str, **kwargs):
        return self._add_route("PUT", path, **kwargs)
    
    def delete(self, path: str, **kwargs):
        return self._add_route("DELETE", path, **kwargs)
    
    def patch(self, path: str, **kwargs):
        return self._add_route("PATCH", path, **kwargs)
    
    def websocket(self, path: str, **kwargs):
        def decorator(func):
            self._ws_routes.append({
                'path': path,
                'handler': func,
                **kwargs
            })
            return func
        return decorator


class Sufast:
    """Sufast Web Framework - FastAPI-style hybrid Rust+Python server.
    
    Args:
        title: API title for documentation
        description: API description
        version: API version string
        docs_url: URL for Swagger UI (None to disable)
        redoc_url: URL for ReDoc (None to disable)
        openapi_url: URL for OpenAPI JSON spec
        debug: Enable debug mode
    """
    
    def __init__(
        self,
        title: str = "Sufast API",
        description: str = "",
        version: str = "1.0.0",
        docs_url: Optional[str] = "/docs",
        redoc_url: Optional[str] = "/redoc",
        openapi_url: Optional[str] = "/openapi.json",
        debug: bool = False,
        secret_key: Optional[str] = None,
        **kwargs
    ):
        self.title = title
        self.description = description
        self.version = version
        self.docs_url = docs_url
        self.redoc_url = redoc_url
        self.openapi_url = openapi_url
        self.debug = debug
        self.secret_key = secret_key or secrets.token_hex(32)
        
        # Route storage
        self._router = Router()
        self._ws_routes: List[WebSocketRoute] = []
        
        # Middleware stack
        self._middleware: List[MiddlewareWrapper] = []
        
        # Event handlers
        self._on_startup: List[Callable] = []
        self._on_shutdown: List[Callable] = []
        
        # Error handlers
        self._exception_handlers: Dict[int, Callable] = {}
        
        # Static file mounts
        self._static_mounts: Dict[str, str] = {}
        
        # Rust core
        self._rust_core = None
        self._rust_available = False
        self._python_callback_ref = None
        
        # Load Rust core (optional - won't fail)
        self._try_load_rust_core()
        
        # Performance tracking
        self._request_count = 0
        self._start_time = None
        
        # OpenAPI generator and cache
        self._openapi_generator = OpenAPIGenerator(
            title=title, version=version, description=description
        )
        self._openapi_cache: Optional[dict] = None
        self._openapi_cache_time: float = 0
        self._openapi_cache_ttl: float = 5.0  # 5 second cache
        
        # Register docs routes
        self._register_docs_routes()
        
        # Register built-in health endpoint
        self._register_health_endpoint()
    
    # ===========================================================
    # Rust Core Integration
    # ===========================================================
    
    def _try_load_rust_core(self):
        """Try to load the Rust shared library. Non-fatal if not found."""
        lib_names = {
            "win32": ["sufast_server.dll", "libsufast_server.dll"],
            "linux": ["libsufast_server.so"],
            "darwin": ["libsufast_server.dylib"],
        }
        
        platform = sys.platform
        names = lib_names.get(platform, lib_names.get("linux", []))
        
        search_dirs = [
            Path(__file__).parent,
            Path(__file__).parent.parent,
            Path.cwd(),
            Path.cwd() / "rust-core" / "target" / "release",
            Path.cwd() / "rust-core" / "target" / "debug",
        ]
        
        for search_dir in search_dirs:
            for name in names:
                lib_path = search_dir / name
                if lib_path.exists():
                    try:
                        self._rust_core = ctypes.CDLL(str(lib_path))
                        self._setup_rust_ffi()
                        self._rust_available = True
                        return
                    except Exception:
                        continue
        
        # Rust core not found - that's OK, we'll use Python server
        self._rust_available = False
    
    def _setup_rust_ffi(self):
        """Setup FFI bindings with the Rust core."""
        if not self._rust_core:
            return
        
        try:
            # Static route registration
            self._rust_core.add_static_route.argtypes = [
                ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint16, ctypes.c_char_p
            ]
            self._rust_core.add_static_route.restype = ctypes.c_bool
            
            # Dynamic route registration
            self._rust_core.add_dynamic_route.argtypes = [
                ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint64
            ]
            self._rust_core.add_dynamic_route.restype = ctypes.c_bool
            
            # Python callback
            self._PythonCallbackType = ctypes.CFUNCTYPE(
                ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p
            )
            self._rust_core.set_python_callback.argtypes = [self._PythonCallbackType]
            self._rust_core.set_python_callback.restype = None
            
            # Server start
            self._rust_core.start_ultra_fast_server.argtypes = [ctypes.c_char_p, ctypes.c_uint16]
            self._rust_core.start_ultra_fast_server.restype = ctypes.c_int
            
            # Performance stats
            self._rust_core.get_performance_stats.argtypes = []
            self._rust_core.get_performance_stats.restype = ctypes.POINTER(ctypes.c_char)
            
            # Cache
            self._rust_core.clear_cache.argtypes = []
            self._rust_core.clear_cache.restype = ctypes.c_bool
            
            self._rust_core.precompile_static_routes.argtypes = []
            self._rust_core.precompile_static_routes.restype = ctypes.c_uint64
            
            # Register callback
            self._register_rust_callback()
            
        except Exception as e:
            self._rust_available = False
    
    def _register_rust_callback(self):
        """Register Python callback for Rust to call on dynamic routes."""
        _response_buffer = threading.local()
        router = self._router
        middleware_stack = self._middleware
        app = self
        
        def rust_python_callback(method_ptr, path_ptr, params_ptr):
            try:
                method = ctypes.string_at(method_ptr).decode('utf-8')
                path = ctypes.string_at(path_ptr).decode('utf-8')
                params_json = ctypes.string_at(params_ptr).decode('utf-8')
                
                try:
                    extra_params = json.loads(params_json) if params_json else {}
                except Exception:
                    extra_params = {}
                
                # Find route
                result = router.find(method, path)
                if not result:
                    resp = {
                        "body": json.dumps({"detail": "Not Found", "path": path}),
                        "status": 404,
                        "headers": {"Content-Type": "application/json"}
                    }
                else:
                    route, params = result
                    params.update(extra_params)
                    
                    try:
                        # Call handler
                        handler = route.handler
                        
                        # Build args based on handler signature
                        sig = inspect.signature(handler)
                        kwargs = {}
                        for pname in sig.parameters:
                            if pname in params:
                                kwargs[pname] = params[pname]
                        
                        if asyncio.iscoroutinefunction(handler):
                            loop = asyncio.new_event_loop()
                            try:
                                response = loop.run_until_complete(handler(**kwargs))
                            finally:
                                loop.close()
                        else:
                            response = handler(**kwargs)
                        
                        resp = app._format_handler_response(response, route.status_code)
                        
                    except HTTPException as e:
                        resp = {
                            "body": json.dumps({"detail": e.detail}),
                            "status": e.status_code,
                            "headers": {"Content-Type": "application/json", **e.headers}
                        }
                    except Exception as e:
                        resp = {
                            "body": json.dumps({"detail": f"Internal Server Error: {str(e)}"}),
                            "status": 500,
                            "headers": {"Content-Type": "application/json"}
                        }
                
                resp_json = json.dumps(resp, default=str)
                result_buf = ctypes.create_string_buffer(resp_json.encode('utf-8'))
                
                if not hasattr(_response_buffer, 'buf'):
                    _response_buffer.buf = []
                _response_buffer.buf.append(result_buf)
                if len(_response_buffer.buf) > 100:
                    _response_buffer.buf = _response_buffer.buf[-50:]
                
                return ctypes.cast(result_buf, ctypes.c_char_p).value
                
            except Exception as e:
                err = json.dumps({
                    "body": json.dumps({"detail": f"Callback error: {str(e)}"}),
                    "status": 500,
                    "headers": {"Content-Type": "application/json"}
                })
                buf = ctypes.create_string_buffer(err.encode('utf-8'))
                return ctypes.cast(buf, ctypes.c_char_p).value
        
        callback = self._PythonCallbackType(rust_python_callback)
        self._python_callback_ref = callback  # prevent GC
        self._rust_core.set_python_callback(callback)
    
    def _register_with_rust(self, route: RouteEntry):
        """Register a route with the Rust core for acceleration."""
        if not self._rust_available:
            return
        
        try:
            if route.is_static and route.method == "GET":
                # Try to pre-compute static response
                try:
                    if route.is_async:
                        loop = asyncio.new_event_loop()
                        resp = loop.run_until_complete(route.handler())
                        loop.close()
                    else:
                        resp = route.handler()
                    
                    formatted = self._format_handler_response(resp, route.status_code)
                    body = formatted.get("body", "")
                    status = formatted.get("status", 200)
                    ct = formatted.get("headers", {}).get("Content-Type", "application/json")
                    
                    route_key = f"{route.method}:{route.path}"
                    self._rust_core.add_static_route(
                        route_key.encode('utf-8'),
                        body.encode('utf-8') if isinstance(body, str) else body,
                        status,
                        ct.encode('utf-8')
                    )
                    route.tier = "static"
                    return
                except Exception:
                    pass  # Fall through to dynamic
            
            # Register as dynamic route
            self._rust_core.add_dynamic_route(
                route.method.encode('utf-8'),
                route.path.encode('utf-8'),
                route.name.encode('utf-8'),
                route.cache_ttl
            )
            
            if route.cache_ttl > 0:
                route.tier = "cached"
            else:
                route.tier = "dynamic"
                
        except Exception:
            pass
    
    # ===========================================================
    # Route Registration
    # ===========================================================
    
    def _add_route(self, method: str, path: str, handler: Callable, **kwargs) -> Callable:
        """Internal: register a route."""
        # Auto-detect if handler should be static
        has_params = bool(re.search(r'\{(\w+)', path))
        is_static = kwargs.pop('static', None)
        if is_static is None:
            is_static = not has_params and method == "GET" and kwargs.get('cache_ttl', 0) == 0
        
        # Get summary from docstring if not provided
        if not kwargs.get('summary') and handler.__doc__:
            kwargs['summary'] = handler.__doc__.strip().split('\n')[0]
        
        # Auto-detect group from path
        if not kwargs.get('group'):
            kwargs['group'] = self._auto_detect_group(path, handler.__name__)
        
        route = RouteEntry(method, path, handler, is_static=is_static, **kwargs)
        self._router.add(route)
        
        # Register with Rust core
        self._register_with_rust(route)
        
        return handler
    
    def route(self, path: str, methods: List[str] = None, **kwargs):
        """Generic route decorator.
        
        Usage:
            @app.route("/endpoint", methods=["GET", "POST"])
            async def handler():
                return {"ok": True}
        """
        methods = methods or ["GET"]
        def decorator(func):
            for method in methods:
                self._add_route(method.upper(), path, func, **kwargs)
            return func
        return decorator
    
    def get(self, path: str, **kwargs):
        """GET route decorator.
        
        Usage:
            @app.get("/users")
            async def list_users():
                return {"users": []}
        """
        def decorator(func):
            return self._add_route("GET", path, func, **kwargs)
        return decorator
    
    def post(self, path: str, **kwargs):
        """POST route decorator.
        
        Usage:
            @app.post("/users", status_code=201)
            async def create_user(request):
                data = await request.json()
                return data
        """
        def decorator(func):
            return self._add_route("POST", path, func, **kwargs)
        return decorator
    
    def put(self, path: str, **kwargs):
        """PUT route decorator."""
        def decorator(func):
            return self._add_route("PUT", path, func, **kwargs)
        return decorator
    
    def delete(self, path: str, **kwargs):
        """DELETE route decorator."""
        def decorator(func):
            return self._add_route("DELETE", path, func, **kwargs)
        return decorator
    
    def patch(self, path: str, **kwargs):
        """PATCH route decorator."""
        def decorator(func):
            return self._add_route("PATCH", path, func, **kwargs)
        return decorator
    
    def head(self, path: str, **kwargs):
        """HEAD route decorator."""
        def decorator(func):
            return self._add_route("HEAD", path, func, **kwargs)
        return decorator
    
    def options(self, path: str, **kwargs):
        """OPTIONS route decorator."""
        def decorator(func):
            return self._add_route("OPTIONS", path, func, **kwargs)
        return decorator
    
    def websocket(self, path: str, **kwargs):
        """WebSocket route decorator.
        
        Usage:
            @app.websocket("/ws")
            async def ws_handler(websocket: WebSocket):
                await websocket.accept()
                async for msg in websocket.iter_text():
                    await websocket.send_text(f"Echo: {msg}")
        """
        def decorator(func):
            ws_route = WebSocketRoute(path, func, kwargs.get('name'))
            self._ws_routes.append(ws_route)
            return func
        return decorator
    
    # ===========================================================
    # Middleware
    # ===========================================================
    
    def middleware(self, middleware_type: str = "http"):
        """Register middleware.
        
        Usage:
            @app.middleware("http")
            async def add_timing(request, call_next):
                start = time.time()
                response = await call_next(request)
                response.headers["X-Process-Time"] = str(time.time() - start)
                return response
        """
        def decorator(func):
            self._middleware.append(MiddlewareWrapper(func, middleware_type))
            return func
        return decorator
    
    def add_middleware(self, middleware_cls, **kwargs):
        """Add a middleware class instance.
        
        Usage:
            from sufast.middleware import CORSMiddleware
            app.add_middleware(CORSMiddleware, allow_origins=["*"])
        """
        if callable(middleware_cls) and not isinstance(middleware_cls, type):
            # Already an instance
            instance = middleware_cls
        elif isinstance(middleware_cls, type):
            instance = middleware_cls(**kwargs)
        else:
            instance = middleware_cls
        
        async def middleware_wrapper(request, call_next):
            # Process request
            if hasattr(instance, 'process_request'):
                result = instance.process_request(request)
                if result is not None and isinstance(result, Response):
                    return result
            
            response = await call_next(request)
            
            # Process response
            if hasattr(instance, 'process_response'):
                response = instance.process_response(request, response)
            
            return response
        
        self._middleware.append(MiddlewareWrapper(middleware_wrapper, "http"))
    
    # ===========================================================
    # Event Handlers
    # ===========================================================
    
    def on_event(self, event_type: str):
        """Register startup/shutdown event handler.
        
        Usage:
            @app.on_event("startup")
            async def startup():
                print("Server starting...")
        """
        def decorator(func):
            if event_type == "startup":
                self._on_startup.append(func)
            elif event_type == "shutdown":
                self._on_shutdown.append(func)
            return func
        return decorator
    
    def exception_handler(self, status_code: int):
        """Register custom exception handler.
        
        Usage:
            @app.exception_handler(404)
            async def not_found(request, exc):
                return json_response({"error": "Not found"}, status=404)
        """
        def decorator(func):
            self._exception_handlers[status_code] = func
            return func
        return decorator
    
    # ===========================================================
    # Router inclusion
    # ===========================================================
    
    def include_router(self, router: 'APIRouter', prefix: str = "", 
                       tags: List[str] = None):
        """Include an APIRouter's routes.
        
        Usage:
            users_router = APIRouter(prefix="/users", tags=["Users"])
            app.include_router(users_router)
        """
        final_prefix = (prefix or "") + (router.prefix or "")
        merged_tags = (tags or []) + (router.tags or [])
        
        for route_def in router._routes:
            raw_path = final_prefix + route_def['path']
            # Normalize: "/api/products/" -> "/api/products"  
            # but keep "/" as "/"
            path = raw_path.rstrip("/") if raw_path != "/" else "/"
            if not path:
                path = final_prefix or "/"
            
            handler = route_def['handler']
            method = route_def['method']
            route_tags = merged_tags + route_def.get('tags', [])
            group = route_def.get('group', router.group)
            
            self._add_route(
                method, path, handler,
                tags=route_tags, group=group,
                summary=route_def.get('summary', ''),
                description=route_def.get('description', ''),
                **{k: v for k, v in route_def.items() 
                   if k not in ('method', 'path', 'handler', 'tags', 'group', 'summary', 'description')}
            )
        
        for ws_def in router._ws_routes:
            path = final_prefix + ws_def['path']
            ws_route = WebSocketRoute(path, ws_def['handler'], ws_def.get('name'))
            self._ws_routes.append(ws_route)
    
    # ===========================================================
    # Static Files
    # ===========================================================
    
    def mount_static(self, path: str, directory: str, name: str = "static"):
        """Mount a directory for serving static files.
        
        Usage:
            app.mount_static("/static", "public")
        """
        self._static_mounts[path.rstrip("/")] = os.path.abspath(directory)
    
    # ===========================================================
    # Documentation Routes
    # ===========================================================
    
    def _register_docs_routes(self):
        """Register documentation routes."""
        app = self
        
        if self.openapi_url:
            @self.get(self.openapi_url, tags=["Documentation"], group="Documentation",
                     summary="OpenAPI Schema", static=False)
            async def openapi_schema():
                """Returns the OpenAPI 3.1 JSON schema."""
                spec = app._generate_openapi_spec()
                return Response(
                    content=json.dumps(spec, default=str),
                    status=200,
                    headers={"Content-Type": "application/json"},
                    content_type="application/json"
                )
        
        if self.docs_url:
            @self.get(self.docs_url, tags=["Documentation"], group="Documentation",
                     summary="Swagger UI", static=False)
            async def swagger_ui():
                """Interactive API documentation (Swagger UI)."""
                spec = app._generate_openapi_spec()
                html = generate_swagger_html(spec)
                return Response(
                    content=html,
                    status=200,
                    headers={"Content-Type": "text/html; charset=utf-8"},
                    content_type="text/html; charset=utf-8"
                )
        
        if self.redoc_url:
            @self.get(self.redoc_url, tags=["Documentation"], group="Documentation",
                     summary="ReDoc", static=False)
            async def redoc():
                """Alternative API documentation (ReDoc)."""
                spec = app._generate_openapi_spec()
                html = generate_redoc_html(spec)
                return Response(
                    content=html,
                    status=200,
                    headers={"Content-Type": "text/html; charset=utf-8"},
                    content_type="text/html; charset=utf-8"
                )
    
    def _generate_openapi_spec(self) -> dict:
        """Generate the OpenAPI specification (cached)."""
        now = time.time()
        if self._openapi_cache and (now - self._openapi_cache_time) < self._openapi_cache_ttl:
            return self._openapi_cache
        
        routes_meta = self._router.get_all_metadata()
        
        # Filter out docs routes from the spec
        doc_paths = {self.docs_url, self.redoc_url, self.openapi_url}
        routes_meta = [r for r in routes_meta if r['path'] not in doc_paths]
        
        ws_meta = []
        for ws_route in self._ws_routes:
            ws_meta.append({
                'path': ws_route.path,
                'function_name': ws_route.name,
                'summary': f"WebSocket: {ws_route.path}",
                'description': (ws_route.handler.__doc__ or '').strip(),
                'tags': ['WebSocket'],
                'parameters': extract_route_params(ws_route.path),
            })
        
        spec = self._openapi_generator.generate(routes_meta, ws_meta)
        self._openapi_cache = spec
        self._openapi_cache_time = now
        return spec
    
    def _register_health_endpoint(self):
        """Register built-in health check endpoint."""
        app = self
        
        @self.get("/health", tags=["System"], group="System",
                 summary="Health Check")
        async def health_check():
            """Returns service health status and basic metrics."""
            return {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": app.version,
                "framework": "Sufast",
                "rust_accelerated": app._rust_available,
            }
    
    # ===========================================================
    # Request Handling
    # ===========================================================
    
    async def _handle_request(self, method: str, path: str, headers: dict,
                               body: bytes, query_string: str = "",
                               client_addr=None) -> dict:
        """Handle an incoming HTTP request. Called by the server."""
        
        # Check static file mounts
        for mount_path, directory in self._static_mounts.items():
            if path.startswith(mount_path + "/") or path == mount_path:
                return await self._serve_static_file(path, mount_path, directory)
        
        # Build Request object
        request = Request(
            method=method,
            path=path,
            headers=headers,
            body=body,
            query_string=query_string,
        )
        if client_addr:
            request.remote_addr = f"{client_addr[0]}:{client_addr[1]}" if isinstance(client_addr, tuple) else str(client_addr)
        
        # Inject request ID for tracing
        request_id = headers.get("x-request-id", secrets.token_hex(8))
        request.state["request_id"] = request_id
        
        # Find route
        result = self._router.find(method, path)
        
        if result is None:
            # Check if method exists for this path (405 vs 404)
            for m in ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"):
                if m != method and self._router.find(m, path):
                    raise HTTPException(405, "Method Not Allowed")
            raise HTTPException(404, f"Route not found: {method} {path}")
        
        route, params = result
        request.path_params = params
        
        # Build the handler chain with middleware
        async def call_handler():
            result = await self._invoke_handler(route, request, params)
            # Convert to Response object for middleware compatibility
            if isinstance(result, Response):
                return result
            formatted = self._format_handler_response(result, route.status_code)
            return Response(
                content=formatted.get("body", ""),
                status=formatted.get("status", 200),
                headers=formatted.get("headers", {}),
                content_type=formatted.get("headers", {}).get("Content-Type", "application/json")
            )
        
        # Apply middleware (inner-to-outer ordering)
        handler_chain = call_handler
        for mw in reversed(self._middleware):
            if mw.type == "http":
                _prev = handler_chain
                _mw = mw
                
                async def make_chain(__prev=_prev, __mw=_mw):
                    async def call_next(_req=None):
                        return await __prev()
                    return await __mw(request, call_next)
                
                handler_chain = make_chain
        
        # Execute
        try:
            response = await handler_chain()
        except HTTPException:
            raise
        except Exception as e:
            # Check for custom exception handler
            if 500 in self._exception_handlers:
                try:
                    handler = self._exception_handlers[500]
                    if asyncio.iscoroutinefunction(handler):
                        response = await handler(request, e)
                    else:
                        response = handler(request, e)
                except Exception:
                    raise HTTPException(500, "Internal Server Error")
            else:
                if self.debug:
                    traceback.print_exc()
                    raise HTTPException(500, f"Internal Server Error: {str(e)}")
                else:
                    raise HTTPException(500, "Internal Server Error")
        
        # Format response and add standard headers
        resp_dict = self._format_handler_response(response, route.status_code)
        
        # Add request ID to response
        if "headers" not in resp_dict:
            resp_dict["headers"] = {}
        resp_dict["headers"]["x-request-id"] = request_id
        
        # Add security headers (safe defaults)
        resp_dict["headers"].setdefault("x-content-type-options", "nosniff")
        resp_dict["headers"].setdefault("x-frame-options", "DENY")
        resp_dict["headers"].setdefault("referrer-policy", "strict-origin-when-cross-origin")
        
        # Check for SSE response
        if isinstance(response, dict) and "_sse_generator" in response:
            resp_dict["_sse_generator"] = response["_sse_generator"]
            resp_dict["_sse_ping_interval"] = response.get("_sse_ping_interval", 15)
        
        # Invalidate OpenAPI cache when routes might change
        self._request_count += 1
        
        return resp_dict
    
    async def _invoke_handler(self, route: RouteEntry, request: Request, 
                               params: dict) -> Any:
        """Invoke a route handler with proper argument injection."""
        handler = route.handler
        sig = inspect.signature(handler)
        
        kwargs = {}
        background_tasks = None
        
        for param_name, param in sig.parameters.items():
            if param_name in params:
                value = params[param_name]
                # Type conversion based on handler annotation
                ann = param.annotation
                if ann != inspect.Parameter.empty:
                    try:
                        if ann is int:
                            value = int(value)
                        elif ann is float:
                            value = float(value)
                        elif ann is bool:
                            value = str(value).lower() in ('true', '1', 'yes')
                        elif ann is str:
                            value = str(value)
                    except (ValueError, TypeError):
                        pass
                kwargs[param_name] = value
            elif param_name == 'request' or param.annotation is Request:
                kwargs[param_name] = request
            elif param_name == 'background_tasks' or param.annotation is BackgroundTasks:
                background_tasks = BackgroundTasks()
                kwargs[param_name] = background_tasks
            # Query parameter injection
            elif param_name in request.query_params:
                value = request.query_params[param_name]
                # Type conversion based on annotation
                if param.annotation == int:
                    value = int(value)
                elif param.annotation == float:
                    value = float(value)
                elif param.annotation == bool:
                    value = value.lower() in ('true', '1', 'yes')
                kwargs[param_name] = value
            elif param.default != inspect.Parameter.empty:
                kwargs[param_name] = param.default
        
        # Call handler
        if route.is_async:
            result = await handler(**kwargs)
        else:
            result = handler(**kwargs)
        
        # Run background tasks
        if background_tasks and len(background_tasks) > 0:
            asyncio.create_task(background_tasks.run_all())
        
        return result
    
    async def _handle_websocket(self, ws: WebSocket, path: str):
        """Handle an incoming WebSocket connection."""
        for ws_route in self._ws_routes:
            params = ws_route.match(path)
            if params is not None:
                # Build kwargs
                sig = inspect.signature(ws_route.handler)
                kwargs = {}
                for pname in sig.parameters:
                    if pname in ('websocket', 'ws') or sig.parameters[pname].annotation is WebSocket:
                        kwargs[pname] = ws
                    elif pname in params:
                        kwargs[pname] = params[pname]
                
                await ws_route.handler(**kwargs)
                return
        
        # No matching WebSocket route
        await ws.close(1008, "No handler for this path")
    
    async def _serve_static_file(self, path: str, mount_path: str, 
                                  directory: str) -> dict:
        """Serve a static file."""
        import mimetypes
        
        relative = path[len(mount_path):]
        if relative.startswith("/"):
            relative = relative[1:]
        
        # Security: prevent path traversal
        file_path = os.path.normpath(os.path.join(directory, relative))
        if not file_path.startswith(os.path.normpath(directory)):
            return {"status": 403, "headers": {"Content-Type": "text/plain"}, "body": "Forbidden"}
        
        if not os.path.isfile(file_path):
            return {"status": 404, "headers": {"Content-Type": "text/plain"}, "body": "Not Found"}
        
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"
        
        with open(file_path, "rb") as f:
            content = f.read()
        
        return {
            "status": 200,
            "headers": {
                "Content-Type": mime_type,
                "Cache-Control": "public, max-age=3600",
            },
            "body": content
        }
    
    def _format_handler_response(self, result: Any, default_status: int = 200) -> dict:
        """Convert handler return value to response dict."""
        if isinstance(result, Response):
            return result.to_dict()
        
        if isinstance(result, dict):
            # Check if it's already a formatted response
            if 'body' in result and 'status' in result and 'headers' in result:
                return result
            # Regular dict -> JSON response
            return {
                "status": default_status,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(result, default=str)
            }
        
        if isinstance(result, (list, tuple)):
            return {
                "status": default_status,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(result, default=str)
            }
        
        if isinstance(result, str):
            return {
                "status": default_status,
                "headers": {"Content-Type": "text/plain"},
                "body": result
            }
        
        if isinstance(result, bytes):
            return {
                "status": default_status,
                "headers": {"Content-Type": "application/octet-stream"},
                "body": result
            }
        
        if result is None:
            return {
                "status": 204,
                "headers": {"Content-Type": "application/json"},
                "body": ""
            }
        
        # Fallback: serialize to JSON
        return {
            "status": default_status,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result, default=str)
        }
    
    # ===========================================================
    # Utilities
    # ===========================================================
    
    def _auto_detect_group(self, path: str, func_name: str) -> str:
        """Auto-detect route group from path."""
        patterns = {
            'Users': ['user', 'profile', 'account'],
            'Products': ['product', 'item', 'catalog'],
            'Content': ['post', 'article', 'blog', 'content'],
            'Categories': ['category', 'tag', 'collection'],
            'Search': ['search', 'find', 'query'],
            'System': ['health', 'stats', 'status', 'monitor', 'metrics'],
            'Auth': ['auth', 'login', 'logout', 'token', 'register'],
            'Admin': ['admin', 'manage', 'config', 'settings'],
        }
        
        combined = (path + " " + func_name).lower()
        for group_name, keywords in patterns.items():
            if any(kw in combined for kw in keywords):
                return group_name
        
        parts = [p for p in path.split('/') if p and '{' not in p]
        if parts:
            return parts[0].title()
        
        return "General"
    
    def get_routes(self) -> List[dict]:
        """Get all registered routes as metadata."""
        return self._router.get_all_metadata()
    
    def url_for(self, name: str, **kwargs) -> str:
        """Generate URL for a named route."""
        for route in self._router.routes:
            if route.name == name:
                url = route.path
                for k, v in kwargs.items():
                    url = re.sub(r'\{' + k + r'(?::\w+)?\}', str(v), url)
                return url
        raise ValueError(f"Route '{name}' not found")
    
    @property
    def is_rust_accelerated(self) -> bool:
        """Check if Rust core is loaded and active."""
        return self._rust_available
    
    def get_performance_stats(self) -> dict:
        """Get performance statistics."""
        stats = {
            "framework": "Sufast",
            "version": self.version,
            "rust_accelerated": self._rust_available,
            "routes": {
                "total": len(self._router.routes),
                "websocket": len(self._ws_routes),
            },
            "middleware_count": len(self._middleware),
        }
        
        if self._rust_available:
            try:
                ptr = self._rust_core.get_performance_stats()
                if ptr:
                    rust_json = ctypes.string_at(ptr).decode('utf-8')
                    stats["rust_stats"] = json.loads(rust_json)
            except Exception:
                pass
        
        return stats
    
    # ===========================================================
    # Server Start
    # ===========================================================
    
    def run(self, host: str = "127.0.0.1", port: int = 8000, 
            debug: bool = None, docs: bool = True, reload: bool = False,
            workers: int = 1, ssl_certfile: str = None, ssl_keyfile: str = None,
            **kwargs):
        """Start the Sufast server.
        
        Uses Rust core for maximum performance when available,
        falls back to Python asyncio server otherwise.
        
        Args:
            host: Bind address
            port: Bind port  
            debug: Enable debug mode (default: self.debug)
            docs: Enable documentation endpoints
            reload: Auto-reload on file changes (dev mode)
            workers: Number of worker processes
            ssl_certfile: Path to SSL certificate file
            ssl_keyfile: Path to SSL private key file
        """
        if debug is not None:
            self.debug = debug
        
        if not docs:
            self.docs_url = None
            self.redoc_url = None
            self.openapi_url = None
        
        # Run startup events
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._run_events(self._on_startup))
        
        scheme = "https" if ssl_certfile else "http"
        
        # Print startup info
        print(f"\n  \033[1;35m{'=' * 50}\033[0m")
        print(f"  \033[1;36m⚡ Sufast v{self.version}\033[0m - {self.title}")
        if self._rust_available:
            print(f"  \033[1;32m🦀 Rust core loaded\033[0m - Maximum performance mode")
        else:
            print(f"  \033[1;33m🐍 Python mode\033[0m - Install Rust core for 10x speed")
        if ssl_certfile:
            print(f"  \033[1;32m🔒 TLS enabled\033[0m")
        print(f"  \033[90mRoutes: {len(self._router.routes)} HTTP + {len(self._ws_routes)} WebSocket\033[0m")
        if workers > 1:
            print(f"  \033[90mWorkers: {workers}\033[0m")
        if self.docs_url:
            print(f"  \033[90mDocs:\033[0m {scheme}://{host}:{port}{self.docs_url}")
        print(f"  \033[1;35m{'=' * 50}\033[0m\n")
        
        try:
            if self._rust_available and not self.debug:
                # Use Rust server for production  
                self._run_rust_server(host, port)
            else:
                # Use Python asyncio server
                self._run_python_server(host, port, ssl_certfile, ssl_keyfile, workers)
        except KeyboardInterrupt:
            pass
        finally:
            loop.run_until_complete(self._run_events(self._on_shutdown))
            loop.close()
            print("\n  \033[90mServer stopped.\033[0m\n")
    
    def _run_rust_server(self, host: str, port: int):
        """Start the Rust-powered server."""
        try:
            # Precompile static routes
            self._rust_core.precompile_static_routes()
            
            result = self._rust_core.start_ultra_fast_server(
                host.encode('utf-8'), port
            )
            
            if result != 0:
                print(f"  \033[33mRust server failed (code {result}), falling back to Python\033[0m")
                self._run_python_server(host, port)
        except Exception as e:
            print(f"  \033[33mRust server error: {e}, falling back to Python\033[0m")
            self._run_python_server(host, port)
    
    def _run_python_server(self, host: str, port: int, ssl_certfile: str = None,
                            ssl_keyfile: str = None, workers: int = 1):
        """Start the Python asyncio server."""
        from .server import run_server
        run_server(self, host, port, ssl_certfile=ssl_certfile, 
                   ssl_keyfile=ssl_keyfile, workers=workers)
    
    async def _run_events(self, events):
        """Run a list of event handlers."""
        for handler in events:
            if asyncio.iscoroutinefunction(handler):
                await handler()
            else:
                handler()


# ===========================================================
# Convenience functions
# ===========================================================

def create_app(**kwargs) -> Sufast:
    """Create a new Sufast application.
    
    Usage:
        app = create_app(title="My API", version="2.0.0")
    """
    return Sufast(**kwargs)
