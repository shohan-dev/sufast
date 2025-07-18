"""
Advanced routing system for Sufast framework.
"""
import re
from typing import Dict, Any, Callable, Optional, List, Tuple, Pattern
from .request import Request, Response


class RouteParameter:
    """Represents a route parameter with type validation."""
    
    def __init__(self, name: str, param_type: str = 'str'):
        self.name = name
        self.param_type = param_type
        self.pattern = self._get_pattern(param_type)
    
    def _get_pattern(self, param_type: str) -> str:
        """Get regex pattern for parameter type."""
        patterns = {
            'str': r'[^/]+',
            'int': r'\d+',
            'float': r'\d+\.?\d*',
            'uuid': r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            'slug': r'[a-z0-9-]+',
            'path': r'.+'  # Matches everything including /
        }
        return patterns.get(param_type, r'[^/]+')
    
    def convert(self, value: str) -> Any:
        """Convert string value to appropriate type."""
        try:
            if self.param_type == 'int':
                return int(value)
            elif self.param_type == 'float':
                return float(value)
            elif self.param_type == 'uuid':
                import uuid
                return uuid.UUID(value)
            else:
                return value
        except (ValueError, TypeError):
            raise ValueError(f"Invalid {self.param_type}: {value}")


class Route:
    """Represents a single route with its handler and metadata."""
    
    def __init__(self, method: str, path: str, handler: Callable, 
                 middleware: List = None, name: str = None):
        self.method = method.upper()
        self.path = path
        self.handler = handler
        self.middleware = middleware or []
        self.name = name or f"{method.lower()}_{path.replace('/', '_').replace('{', '').replace('}', '')}"
        
        # Parse route parameters
        self.parameters = self._parse_parameters(path)
        self.pattern = self._compile_pattern(path)
    
    def _parse_parameters(self, path: str) -> List[RouteParameter]:
        """Parse route parameters from path."""
        import re
        param_pattern = r'\{([^}]+)\}'
        matches = re.findall(param_pattern, path)
        
        parameters = []
        for match in matches:
            if ':' in match:
                name, param_type = match.split(':', 1)
            else:
                name, param_type = match, 'str'
            parameters.append(RouteParameter(name, param_type))
        
        return parameters
    
    def _compile_pattern(self, path: str) -> Pattern:
        """Compile route path to regex pattern."""
        import re
        
        # Replace parameters with their patterns
        pattern = path
        for param in self.parameters:
            param_placeholder = f"{{{param.name}:{param.param_type}}}" if param.param_type != 'str' else f"{{{param.name}}}"
            pattern = pattern.replace(param_placeholder, f"(?P<{param.name}>{param.pattern})")
        
        # Handle wildcard routes
        pattern = pattern.replace('*', r'(?P<wildcard>.*)')
        
        # Ensure exact match
        pattern = f"^{pattern}$"
        
        return re.compile(pattern)
    
    def match(self, path: str) -> Optional[Dict[str, Any]]:
        """Check if path matches this route and extract parameters."""
        match = self.pattern.match(path)
        if not match:
            return None
        
        params = match.groupdict()
        
        # Convert parameters to appropriate types
        for param in self.parameters:
            if param.name in params:
                try:
                    params[param.name] = param.convert(params[param.name])
                except ValueError:
                    return None  # Invalid parameter type
        
        return params


class RouteGroup:
    """Group of routes with common prefix and middleware."""
    
    def __init__(self, prefix: str = '', middleware: List = None):
        self.prefix = prefix.rstrip('/')
        self.middleware = middleware or []
        self.routes: List[Route] = []
    
    def add_route(self, method: str, path: str, handler: Callable, 
                  middleware: List = None, name: str = None) -> Route:
        """Add route to group."""
        full_path = f"{self.prefix}{path}"
        combined_middleware = self.middleware + (middleware or [])
        route = Route(method, full_path, handler, combined_middleware, name)
        self.routes.append(route)
        return route
    
    def get(self, path: str, middleware: List = None, name: str = None):
        """Decorator for GET routes."""
        def decorator(handler: Callable):
            return self.add_route('GET', path, handler, middleware, name)
        return decorator
    
    def post(self, path: str, middleware: List = None, name: str = None):
        """Decorator for POST routes."""
        def decorator(handler: Callable):
            return self.add_route('POST', path, handler, middleware, name)
        return decorator
    
    def put(self, path: str, middleware: List = None, name: str = None):
        """Decorator for PUT routes."""
        def decorator(handler: Callable):
            return self.add_route('PUT', path, handler, middleware, name)
        return decorator
    
    def delete(self, path: str, middleware: List = None, name: str = None):
        """Decorator for DELETE routes."""
        def decorator(handler: Callable):
            return self.add_route('DELETE', path, handler, middleware, name)
        return decorator
    
    def patch(self, path: str, middleware: List = None, name: str = None):
        """Decorator for PATCH routes."""
        def decorator(handler: Callable):
            return self.add_route('PATCH', path, handler, middleware, name)
        return decorator


class Router:
    """Advanced router with parameter extraction and middleware support."""
    
    def __init__(self):
        self.routes: List[Route] = []
        self.route_groups: List[RouteGroup] = []
        self.named_routes: Dict[str, Route] = {}
    
    def add_route(self, method: str, path: str, handler: Callable, 
                  middleware: List = None, name: str = None) -> Route:
        """Add a single route."""
        route = Route(method, path, handler, middleware, name)
        self.routes.append(route)
        if route.name:
            self.named_routes[route.name] = route
        return route
    
    def group(self, prefix: str = '', middleware: List = None) -> RouteGroup:
        """Create a route group."""
        group = RouteGroup(prefix, middleware)
        self.route_groups.append(group)
        return group
    
    def find_route(self, method: str, path: str) -> Optional[Tuple[Route, Dict[str, Any]]]:
        """Find matching route and extract parameters."""
        # Check individual routes first
        for route in self.routes:
            if route.method == method:
                params = route.match(path)
                if params is not None:
                    return route, params
        
        # Check routes in groups
        for group in self.route_groups:
            for route in group.routes:
                if route.method == method:
                    params = route.match(path)
                    if params is not None:
                        return route, params
        
        return None
    
    def url_for(self, name: str, **kwargs) -> str:
        """Generate URL for named route."""
        if name not in self.named_routes:
            raise ValueError(f"Route '{name}' not found")
        
        route = self.named_routes[name]
        url = route.path
        
        # Replace parameters
        for param_name, value in kwargs.items():
            patterns = [
                f"{{{param_name}}}",
                f"{{{param_name}:str}}",
                f"{{{param_name}:int}}",
                f"{{{param_name}:float}}",
                f"{{{param_name}:uuid}}",
                f"{{{param_name}:slug}}",
                f"{{{param_name}:path}}"
            ]
            for pattern in patterns:
                if pattern in url:
                    url = url.replace(pattern, str(value))
                    break
        
        return url
    
    def get_routes_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all routes for debugging."""
        summary = []
        
        # Individual routes
        for route in self.routes:
            summary.append({
                'method': route.method,
                'path': route.path,
                'name': route.name,
                'handler': route.handler.__name__,
                'middleware_count': len(route.middleware)
            })
        
        # Group routes
        for group in self.route_groups:
            for route in group.routes:
                summary.append({
                    'method': route.method,
                    'path': route.path,
                    'name': route.name,
                    'handler': route.handler.__name__,
                    'middleware_count': len(route.middleware),
                    'group_prefix': group.prefix
                })
        
        return summary


# Convenience decorators for common HTTP methods
def route(method: str, path: str, middleware: List = None, name: str = None):
    """Generic route decorator."""
    def decorator(handler: Callable):
        # This will be used by the App class
        handler._route_info = {
            'method': method,
            'path': path,
            'middleware': middleware,
            'name': name
        }
        return handler
    return decorator

def get(path: str, middleware: List = None, name: str = None):
    """GET route decorator."""
    return route('GET', path, middleware, name)

def post(path: str, middleware: List = None, name: str = None):
    """POST route decorator."""
    return route('POST', path, middleware, name)

def put(path: str, middleware: List = None, name: str = None):
    """PUT route decorator."""
    return route('PUT', path, middleware, name)

def delete(path: str, middleware: List = None, name: str = None):
    """DELETE route decorator."""
    return route('DELETE', path, middleware, name)

def patch(path: str, middleware: List = None, name: str = None):
    """PATCH route decorator."""
    return route('PATCH', path, middleware, name)
