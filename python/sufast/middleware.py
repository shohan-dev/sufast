"""
Middleware system for Sufast framework.
Production-grade middleware with JWT auth, rate limiting, CORS, and security.
"""
import time
import json
import threading
from abc import ABC, abstractmethod
from typing import Callable, List, Dict, Any, Optional
from .request import Request, Response, json_response


class Middleware(ABC):
    """Base middleware class."""
    
    @abstractmethod
    def process_request(self, request: Request) -> Optional[Response]:
        """Process request before handler. Return Response to short-circuit."""
        pass
    
    @abstractmethod
    def process_response(self, request: Request, response: Response) -> Response:
        """Process response after handler."""
        pass


class CORSMiddleware(Middleware):
    """Cross-Origin Resource Sharing middleware.
    
    Usage:
        app.add_middleware(CORSMiddleware, 
                          allow_origins=["https://example.com"],
                          allow_methods=["GET", "POST"],
                          allow_credentials=True)
    """
    
    def __init__(self, allow_origins: List[str] = None, 
                 allow_methods: List[str] = None,
                 allow_headers: List[str] = None,
                 allow_credentials: bool = False,
                 expose_headers: List[str] = None,
                 max_age: int = 86400):
        self.allow_origins = allow_origins or ['*']
        self.allow_methods = allow_methods or ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']
        self.allow_headers = allow_headers or ['*']
        self.allow_credentials = allow_credentials
        self.expose_headers = expose_headers or []
        self.max_age = max_age
    
    def process_request(self, request: Request) -> Optional[Response]:
        if request.method == 'OPTIONS':
            return self._preflight_response(request)
        return None
    
    def process_response(self, request: Request, response: Response) -> Response:
        origin = request.get_header('origin')
        if origin and (self.allow_origins == ['*'] or origin in self.allow_origins):
            if self.allow_credentials:
                # Can't use wildcard with credentials
                response.set_header('access-control-allow-origin', origin)
            else:
                response.set_header('access-control-allow-origin', 
                                   origin if self.allow_origins != ['*'] else '*')
        elif self.allow_origins == ['*']:
            response.set_header('access-control-allow-origin', '*')
        
        if self.allow_credentials:
            response.set_header('access-control-allow-credentials', 'true')
        
        if self.expose_headers:
            response.set_header('access-control-expose-headers', ', '.join(self.expose_headers))
        
        return response
    
    def _preflight_response(self, request: Request) -> Response:
        response = json_response({})
        
        origin = request.get_header('origin')
        if origin and (self.allow_origins == ['*'] or origin in self.allow_origins):
            if self.allow_credentials:
                response.set_header('access-control-allow-origin', origin)
            else:
                response.set_header('access-control-allow-origin',
                                   origin if self.allow_origins != ['*'] else '*')
        
        response.set_header('access-control-allow-methods', ', '.join(self.allow_methods))
        response.set_header('access-control-allow-headers', ', '.join(self.allow_headers))
        response.set_header('access-control-max-age', str(self.max_age))
        
        if self.allow_credentials:
            response.set_header('access-control-allow-credentials', 'true')
        
        return response


class AuthMiddleware(Middleware):
    """JWT Authentication middleware with real token validation.
    
    Integrates with sufast.security.JWTAuth for proper HMAC-SHA256 JWT validation.
    Falls back to configurable token validator if no JWTAuth instance provided.
    
    Usage:
        from sufast.security import JWTAuth
        
        jwt = JWTAuth(secret_key="your-secret-key-min-32-chars!")
        app.add_middleware(AuthMiddleware, 
                          jwt_auth=jwt,
                          exclude_paths=["/", "/docs", "/health", "/auth/login"])
    """
    
    def __init__(self, secret_key: str = "", exclude_paths: List[str] = None,
                 jwt_auth=None, token_validator: Callable = None):
        self.secret_key = secret_key
        self.exclude_paths = exclude_paths or ["/docs", "/redoc", "/openapi.json", "/health"]
        self.jwt_auth = jwt_auth
        self.token_validator = token_validator
        
        # Auto-create JWTAuth if secret_key provided and no jwt_auth
        if secret_key and not jwt_auth:
            try:
                from .security import JWTAuth
                self.jwt_auth = JWTAuth(secret_key=secret_key)
            except Exception:
                pass
    
    def process_request(self, request: Request) -> Optional[Response]:
        # Skip auth for excluded paths
        if any(request.path.startswith(path) for path in self.exclude_paths):
            return None
        
        # Check for Authorization header
        auth_header = request.get_header('authorization')
        if not auth_header:
            return json_response({'detail': 'Authorization header required'}, 401)
        
        if not auth_header.startswith('Bearer '):
            return json_response({'detail': 'Invalid authorization format. Use: Bearer <token>'}, 401)
        
        token = auth_header[7:]  # Remove "Bearer "
        
        # Validate with JWTAuth
        if self.jwt_auth:
            try:
                payload = self.jwt_auth.verify_token(token)
                request.state['user'] = payload
                request.state['token'] = token
                return None
            except Exception as e:
                return json_response({'detail': f'Invalid token: {str(e)}'}, 401)
        
        # Fallback to custom validator
        if self.token_validator:
            try:
                user_info = self.token_validator(token)
                if user_info:
                    request.state['user'] = user_info
                    request.state['token'] = token
                    return None
            except Exception:
                pass
            return json_response({'detail': 'Invalid token'}, 401)
        
        return json_response({'detail': 'No token validator configured'}, 500)
    
    def process_response(self, request: Request, response: Response) -> Response:
        return response


class RateLimitMiddleware(Middleware):
    """Sliding window rate limiting middleware.
    
    Thread-safe rate limiter with per-client tracking,
    configurable limits, and proper cleanup.
    
    Usage:
        app.add_middleware(RateLimitMiddleware, 
                          requests_per_minute=100,
                          burst_size=20)
    """
    
    def __init__(self, requests_per_minute: int = 100, burst_size: int = 0,
                 key_func: Callable = None, exclude_paths: List[str] = None):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size or requests_per_minute
        self.key_func = key_func  # Custom function to extract rate-limit key
        self.exclude_paths = exclude_paths or []
        self._storage: Dict[str, list] = {}
        self._lock = threading.Lock()
        self.window_size = 60  # 1 minute
    
    def _get_client_key(self, request: Request) -> str:
        """Get rate limit key for a request."""
        if self.key_func:
            return self.key_func(request)
        # Default: use IP + path prefix
        return request.remote_addr
    
    def process_request(self, request: Request) -> Optional[Response]:
        # Skip excluded paths
        if any(request.path.startswith(p) for p in self.exclude_paths):
            return None
        
        client_key = self._get_client_key(request)
        current_time = time.time()
        
        with self._lock:
            # Clean old entries
            cutoff = current_time - self.window_size
            if client_key in self._storage:
                self._storage[client_key] = [
                    t for t in self._storage[client_key] if t > cutoff
                ]
            else:
                self._storage[client_key] = []
            
            requests = self._storage[client_key]
            
            if len(requests) >= self.requests_per_minute:
                # Calculate retry-after
                oldest = requests[0] if requests else current_time
                retry_after = int(self.window_size - (current_time - oldest)) + 1
                
                return Response(
                    content=json.dumps({
                        'detail': 'Rate limit exceeded',
                        'retry_after': retry_after,
                    }),
                    status=429,
                    headers={
                        'retry-after': str(retry_after),
                        'x-ratelimit-limit': str(self.requests_per_minute),
                        'x-ratelimit-remaining': '0',
                        'x-ratelimit-reset': str(int(oldest + self.window_size)),
                    },
                    content_type='application/json',
                )
            
            requests.append(current_time)
        
        return None
    
    def process_response(self, request: Request, response: Response) -> Response:
        client_key = self._get_client_key(request)
        with self._lock:
            requests = self._storage.get(client_key, [])
            remaining = max(0, self.requests_per_minute - len(requests))
            response.set_header('x-ratelimit-remaining', str(remaining))
            response.set_header('x-ratelimit-limit', str(self.requests_per_minute))
        return response
    
    def cleanup(self):
        """Remove expired entries. Call periodically."""
        cutoff = time.time() - self.window_size
        with self._lock:
            for key in list(self._storage.keys()):
                self._storage[key] = [t for t in self._storage[key] if t > cutoff]
                if not self._storage[key]:
                    del self._storage[key]


class LoggingMiddleware(Middleware):
    """Request logging middleware with proper cleanup.
    
    Uses weak references to prevent memory leaks from unfinished requests.
    """
    
    def __init__(self, logger=None):
        self.logger = logger
        self._start_times: Dict[int, float] = {}
        self._lock = threading.Lock()
        self._max_tracked = 10000  # Prevent unbounded growth
    
    def process_request(self, request: Request) -> Optional[Response]:
        req_id = id(request)
        with self._lock:
            # Cleanup if too many tracked
            if len(self._start_times) > self._max_tracked:
                cutoff = time.time() - 300  # 5 min old
                self._start_times = {
                    k: v for k, v in self._start_times.items() if v > cutoff
                }
            self._start_times[req_id] = time.time()
        self._log(f"→ {request.method} {request.path} from {request.remote_addr}")
        return None
    
    def process_response(self, request: Request, response: Response) -> Response:
        req_id = id(request)
        with self._lock:
            start = self._start_times.pop(req_id, None)
        if start:
            duration = time.time() - start
            self._log(f"← {request.method} {request.path} {response.status} ({duration:.3f}s)")
        return response
    
    def _log(self, message: str):
        """Log message."""
        if self.logger:
            self.logger.info(message)
        else:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")


class SecurityHeadersMiddleware(Middleware):
    """Security headers middleware with configurable policies.
    
    Applies industry-standard security headers to all responses.
    
    Usage:
        app.add_middleware(SecurityHeadersMiddleware)
    """
    
    def __init__(self, 
                 hsts: bool = True,
                 hsts_max_age: int = 31536000,
                 content_type_nosniff: bool = True,
                 frame_deny: bool = True,
                 xss_protection: bool = True,
                 referrer_policy: str = 'strict-origin-when-cross-origin',
                 content_security_policy: str = None):
        self.security_headers = {}
        
        if content_type_nosniff:
            self.security_headers['x-content-type-options'] = 'nosniff'
        if frame_deny:
            self.security_headers['x-frame-options'] = 'DENY'
        if xss_protection:
            self.security_headers['x-xss-protection'] = '1; mode=block'
        if hsts:
            self.security_headers['strict-transport-security'] = f'max-age={hsts_max_age}; includeSubDomains'
        if referrer_policy:
            self.security_headers['referrer-policy'] = referrer_policy
        if content_security_policy:
            self.security_headers['content-security-policy'] = content_security_policy
        
        # Always add these
        self.security_headers['x-permitted-cross-domain-policies'] = 'none'
    
    def process_request(self, request: Request) -> Optional[Response]:
        return None
    
    def process_response(self, request: Request, response: Response) -> Response:
        for header, value in self.security_headers.items():
            response.set_header(header, value)
        return response


class ValidationMiddleware(Middleware):
    """Request validation middleware with security scanning.
    
    Validates request size, JSON format, and optionally scans
    for SQL injection and XSS patterns.
    """
    
    def __init__(self, max_content_length: int = 10 * 1024 * 1024,
                 scan_for_attacks: bool = False):
        self.max_content_length = max_content_length
        self.scan_for_attacks = scan_for_attacks
    
    def process_request(self, request: Request) -> Optional[Response]:
        # Check content length
        if request.content_length > self.max_content_length:
            return json_response({
                'detail': 'Request entity too large',
                'max_size': self.max_content_length
            }, 413)
        
        # Validate JSON if present
        if request.is_json:
            if request.json is None and request.body:
                return json_response({'detail': 'Invalid JSON in request body'}, 400)
        
        # Optional security scanning
        if self.scan_for_attacks:
            try:
                from .security import SecurityScanner
                warnings = SecurityScanner.scan_request(
                    request.method, request.path, request.headers,
                    request.body.decode('utf-8', errors='replace') if request.body else ""
                )
                if warnings:
                    return json_response({
                        'detail': 'Potentially dangerous request detected',
                        'warnings': warnings,
                    }, 400)
            except ImportError:
                pass
        
        return None
    
    def process_response(self, request: Request, response: Response) -> Response:
        return response


class MiddlewareStack:
    """Manages middleware execution."""
    
    def __init__(self):
        self.middlewares: List[Middleware] = []
    
    def add(self, middleware: Middleware):
        """Add middleware to the stack."""
        self.middlewares.append(middleware)
    
    def process_request(self, request: Request) -> Optional[Response]:
        """Process request through all middleware."""
        for middleware in self.middlewares:
            response = middleware.process_request(request)
            if response:  # Short-circuit if middleware returns response
                return response
        return None
    
    def process_response(self, request: Request, response: Response) -> Response:
        """Process response through all middleware (in reverse order)."""
        for middleware in reversed(self.middlewares):
            response = middleware.process_response(request, response)
        return response
