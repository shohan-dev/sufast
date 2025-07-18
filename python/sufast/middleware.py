"""
Middleware system for Sufast framework.
"""
import time
import json
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
    """Cross-Origin Resource Sharing middleware."""
    
    def __init__(self, allow_origins: List[str] = None, 
                 allow_methods: List[str] = None,
                 allow_headers: List[str] = None,
                 allow_credentials: bool = False,
                 max_age: int = 86400):
        self.allow_origins = allow_origins or ['*']
        self.allow_methods = allow_methods or ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
        self.allow_headers = allow_headers or ['*']
        self.allow_credentials = allow_credentials
        self.max_age = max_age
    
    def process_request(self, request: Request) -> Optional[Response]:
        if request.method == 'OPTIONS':
            return self._preflight_response(request)
        return None
    
    def process_response(self, request: Request, response: Response) -> Response:
        origin = request.get_header('origin')
        if origin and (self.allow_origins == ['*'] or origin in self.allow_origins):
            response.set_header('access-control-allow-origin', origin)
        elif self.allow_origins == ['*']:
            response.set_header('access-control-allow-origin', '*')
        
        if self.allow_credentials:
            response.set_header('access-control-allow-credentials', 'true')
        
        return response
    
    def _preflight_response(self, request: Request) -> Response:
        response = json_response({})
        
        origin = request.get_header('origin')
        if origin and (self.allow_origins == ['*'] or origin in self.allow_origins):
            response.set_header('access-control-allow-origin', origin)
        
        response.set_header('access-control-allow-methods', ', '.join(self.allow_methods))
        response.set_header('access-control-allow-headers', ', '.join(self.allow_headers))
        response.set_header('access-control-max-age', str(self.max_age))
        
        if self.allow_credentials:
            response.set_header('access-control-allow-credentials', 'true')
        
        return response


class AuthMiddleware(Middleware):
    """Authentication middleware."""
    
    def __init__(self, secret_key: str, exclude_paths: List[str] = None):
        self.secret_key = secret_key
        self.exclude_paths = exclude_paths or []
    
    def process_request(self, request: Request) -> Optional[Response]:
        # Skip auth for excluded paths
        if any(request.path.startswith(path) for path in self.exclude_paths):
            return None
        
        # Check for Authorization header
        auth_header = request.get_header('authorization')
        if not auth_header:
            return json_response({'error': 'Authorization header required'}, 401)
        
        # Simple token validation (in production, use JWT or similar)
        if not auth_header.startswith('Bearer '):
            return json_response({'error': 'Invalid authorization format'}, 401)
        
        token = auth_header[7:]  # Remove "Bearer "
        if not self._validate_token(token):
            return json_response({'error': 'Invalid token'}, 401)
        
        # Add user info to request
        request.user = self._get_user_from_token(token)
        return None
    
    def process_response(self, request: Request, response: Response) -> Response:
        return response
    
    def _validate_token(self, token: str) -> bool:
        """Validate token. Override for custom validation."""
        # Simple validation - in production use proper JWT validation
        return len(token) > 10
    
    def _get_user_from_token(self, token: str) -> Dict[str, Any]:
        """Get user info from token. Override for custom user retrieval."""
        return {'id': 1, 'username': 'user', 'token': token}


class RateLimitMiddleware(Middleware):
    """Rate limiting middleware."""
    
    def __init__(self, requests_per_minute: int = 100, storage: Dict = None):
        self.requests_per_minute = requests_per_minute
        self.storage = storage or {}  # In production, use Redis
        self.window_size = 60  # 1 minute
    
    def process_request(self, request: Request) -> Optional[Response]:
        client_ip = request.remote_addr
        current_time = time.time()
        
        # Clean old entries
        self._cleanup_old_entries(current_time)
        
        # Get or create client record
        if client_ip not in self.storage:
            self.storage[client_ip] = []
        
        client_requests = self.storage[client_ip]
        
        # Check rate limit
        if len(client_requests) >= self.requests_per_minute:
            return json_response({
                'error': 'Rate limit exceeded',
                'retry_after': self.window_size
            }, 429)
        
        # Add current request
        client_requests.append(current_time)
        return None
    
    def process_response(self, request: Request, response: Response) -> Response:
        client_ip = request.remote_addr
        if client_ip in self.storage:
            remaining = max(0, self.requests_per_minute - len(self.storage[client_ip]))
            response.set_header('x-ratelimit-remaining', str(remaining))
            response.set_header('x-ratelimit-limit', str(self.requests_per_minute))
        return response
    
    def _cleanup_old_entries(self, current_time: float):
        """Remove entries older than window size."""
        cutoff_time = current_time - self.window_size
        for client_ip in list(self.storage.keys()):
            self.storage[client_ip] = [
                timestamp for timestamp in self.storage[client_ip]
                if timestamp > cutoff_time
            ]
            if not self.storage[client_ip]:
                del self.storage[client_ip]


class LoggingMiddleware(Middleware):
    """Request logging middleware."""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.start_times = {}
    
    def process_request(self, request: Request) -> Optional[Response]:
        self.start_times[id(request)] = time.time()
        self._log(f"→ {request.method} {request.path} from {request.remote_addr}")
        return None
    
    def process_response(self, request: Request, response: Response) -> Response:
        request_id = id(request)
        if request_id in self.start_times:
            duration = time.time() - self.start_times[request_id]
            del self.start_times[request_id]
            self._log(f"← {request.method} {request.path} {response.status} ({duration:.3f}s)")
        return response
    
    def _log(self, message: str):
        """Log message. Override to use custom logger."""
        if self.logger:
            self.logger.info(message)
        else:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")


class SecurityHeadersMiddleware(Middleware):
    """Security headers middleware."""
    
    def __init__(self):
        self.security_headers = {
            'x-content-type-options': 'nosniff',
            'x-frame-options': 'DENY',
            'x-xss-protection': '1; mode=block',
            'strict-transport-security': 'max-age=31536000; includeSubDomains',
            'referrer-policy': 'strict-origin-when-cross-origin'
        }
    
    def process_request(self, request: Request) -> Optional[Response]:
        return None
    
    def process_response(self, request: Request, response: Response) -> Response:
        for header, value in self.security_headers.items():
            response.set_header(header, value)
        return response


class ValidationMiddleware(Middleware):
    """Request validation middleware."""
    
    def __init__(self, max_content_length: int = 10 * 1024 * 1024):  # 10MB default
        self.max_content_length = max_content_length
    
    def process_request(self, request: Request) -> Optional[Response]:
        # Check content length
        if request.content_length > self.max_content_length:
            return json_response({
                'error': 'Request entity too large',
                'max_size': self.max_content_length
            }, 413)
        
        # Validate JSON if present
        if request.is_json:
            if request.json is None and request.body:
                return json_response({'error': 'Invalid JSON'}, 400)
        
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
