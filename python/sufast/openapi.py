"""
Sufast OpenAPI Schema Generation - Auto-generate OpenAPI 3.1 specs from routes.
"""

import json
import re
import inspect
from typing import Any, Dict, List, Optional, get_type_hints
from datetime import datetime


class OpenAPIGenerator:
    """Generates OpenAPI 3.1 specification from Sufast routes."""
    
    def __init__(self, title: str = "Sufast API", version: str = "1.0.0",
                 description: str = "", servers: List[dict] = None,
                 contact: dict = None, license_info: dict = None):
        self.title = title
        self.version = version
        self.description = description
        self.servers = servers or []
        self.contact = contact
        self.license_info = license_info
    
    def generate(self, routes: List[dict], websocket_routes: List[dict] = None) -> dict:
        """Generate complete OpenAPI 3.1 specification.
        
        Args:
            routes: List of route metadata dicts
            websocket_routes: List of WebSocket route metadata dicts
        """
        spec = {
            "openapi": "3.1.0",
            "info": self._build_info(),
            "paths": self._build_paths(routes, websocket_routes or []),
            "components": self._build_components(routes),
            "tags": self._build_tags(routes, websocket_routes or []),
        }
        
        if self.servers:
            spec["servers"] = self.servers
        
        return spec
    
    def generate_json(self, routes: List[dict], websocket_routes: List[dict] = None) -> str:
        """Generate OpenAPI spec as JSON string."""
        return json.dumps(self.generate(routes, websocket_routes), indent=2, default=str)
    
    def _build_info(self) -> dict:
        info = {
            "title": self.title,
            "version": self.version,
        }
        if self.description:
            info["description"] = self.description
        if self.contact:
            info["contact"] = self.contact
        if self.license_info:
            info["license"] = self.license_info
        return info
    
    def _build_paths(self, routes: List[dict], websocket_routes: List[dict]) -> dict:
        paths = {}
        
        for route in routes:
            path = route["path"]
            method = route["method"].lower()
            
            # Convert {param} to OpenAPI format (already correct)
            openapi_path = path
            
            if openapi_path not in paths:
                paths[openapi_path] = {}
            
            operation = self._build_operation(route)
            paths[openapi_path][method] = operation
        
        # Add WebSocket routes as special documentation
        for ws_route in websocket_routes:
            ws_path = ws_route["path"]
            if ws_path not in paths:
                paths[ws_path] = {}
            paths[ws_path]["get"] = self._build_websocket_operation(ws_route)
        
        return paths
    
    def _build_operation(self, route: dict) -> dict:
        operation = {
            "summary": route.get("summary", route.get("description", f"{route['method']} {route['path']}")),
            "operationId": route.get("operation_id", route.get("function_name", "")),
            "responses": self._build_responses(route),
        }
        
        # Description
        desc = route.get("detailed_description") or route.get("description", "")
        if desc:
            operation["description"] = desc
        
        # Tags
        tags = route.get("tags", [])
        if route.get("group"):
            tags = [route["group"]] + [t for t in tags if t != route["group"]]
        if tags:
            operation["tags"] = tags
        
        # Parameters (path + query)
        params = self._build_parameters(route)
        if params:
            operation["parameters"] = params
        
        # Request body for POST/PUT/PATCH
        if route["method"] in ("POST", "PUT", "PATCH"):
            request_body = route.get("request_body")
            if request_body:
                operation["requestBody"] = request_body
            else:
                operation["requestBody"] = {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object"
                            }
                        }
                    },
                    "required": False
                }
        
        # Performance tier info as extension
        if route.get("tier"):
            operation["x-performance-tier"] = route["tier"]
        if route.get("cache_ttl"):
            operation["x-cache-ttl"] = route["cache_ttl"]
        
        # Deprecated flag
        if route.get("deprecated"):
            operation["deprecated"] = True
        
        return operation
    
    def _build_websocket_operation(self, ws_route: dict) -> dict:
        return {
            "summary": ws_route.get("summary", f"WebSocket: {ws_route['path']}"),
            "description": ws_route.get("description", "WebSocket endpoint. Connect using ws:// protocol."),
            "operationId": ws_route.get("function_name", ""),
            "tags": ["WebSocket"] + ws_route.get("tags", []),
            "responses": {
                "101": {
                    "description": "WebSocket connection established (Switching Protocols)"
                }
            },
            "x-websocket": True,
            "parameters": self._build_parameters(ws_route),
        }
    
    def _build_parameters(self, route: dict) -> List[dict]:
        params = []
        
        # Path parameters
        for param in route.get("parameters", []):
            p = {
                "name": param["name"],
                "in": "path",
                "required": True,
                "schema": self._python_type_to_schema(param.get("type", "string")),
                "description": param.get("description", f"Path parameter: {param['name']}"),
            }
            if param.get("example"):
                p["example"] = param["example"]
            params.append(p)
        
        # Query parameters
        for qparam in route.get("query_parameters", []):
            p = {
                "name": qparam["name"],
                "in": "query",
                "required": qparam.get("required", False),
                "schema": self._python_type_to_schema(qparam.get("type", "string")),
                "description": qparam.get("description", ""),
            }
            if qparam.get("default") is not None:
                p["schema"]["default"] = qparam["default"]
            if qparam.get("example"):
                p["example"] = qparam["example"]
            params.append(p)
        
        # Header parameters
        for hparam in route.get("header_parameters", []):
            params.append({
                "name": hparam["name"],
                "in": "header",
                "required": hparam.get("required", False),
                "schema": self._python_type_to_schema(hparam.get("type", "string")),
                "description": hparam.get("description", ""),
            })
        
        return params
    
    def _build_responses(self, route: dict) -> dict:
        responses = {}
        
        # Custom response definitions
        custom_responses = route.get("responses", {})
        if custom_responses:
            for code, resp in custom_responses.items():
                responses[str(code)] = {
                    "description": resp.get("description", ""),
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object"
                            }
                        }
                    }
                }
                if resp.get("example"):
                    responses[str(code)]["content"]["application/json"]["example"] = resp["example"]
        
        # Always include a 200 response
        if "200" not in responses:
            resp_200 = {
                "description": "Successful response",
                "content": {
                    "application/json": {
                        "schema": {"type": "object"}
                    }
                }
            }
            # Add example from route metadata
            example = route.get("response_example")
            if example:
                resp_200["content"]["application/json"]["example"] = example
            responses["200"] = resp_200
        
        # Error responses
        if "422" not in responses:
            responses["422"] = {
                "description": "Validation Error",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "detail": {"type": "string"}
                            }
                        }
                    }
                }
            }
        
        return responses
    
    def _build_components(self, routes: List[dict]) -> dict:
        return {
            "schemas": {
                "HTTPValidationError": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "array",
                            "items": {
                                "$ref": "#/components/schemas/ValidationError"
                            }
                        }
                    }
                },
                "ValidationError": {
                    "type": "object",
                    "required": ["loc", "msg", "type"],
                    "properties": {
                        "loc": {
                            "type": "array",
                            "items": {
                                "anyOf": [{"type": "string"}, {"type": "integer"}]
                            }
                        },
                        "msg": {"type": "string"},
                        "type": {"type": "string"}
                    }
                },
                "HealthCheck": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "healthy"},
                        "version": {"type": "string"},
                        "timestamp": {"type": "string", "format": "date-time"}
                    }
                }
            },
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                },
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key"
                }
            }
        }
    
    def _build_tags(self, routes: List[dict], websocket_routes: List[dict]) -> List[dict]:
        tag_set = {}
        
        for route in routes:
            group = route.get("group")
            if group and group not in tag_set:
                tag_set[group] = {
                    "name": group,
                    "description": f"Endpoints in {group}"
                }
            for tag in route.get("tags", []):
                if tag not in tag_set:
                    tag_set[tag] = {
                        "name": tag,
                        "description": f"Endpoints tagged with '{tag}'"
                    }
        
        if websocket_routes:
            tag_set["WebSocket"] = {
                "name": "WebSocket",
                "description": "WebSocket real-time endpoints"
            }
        
        return list(tag_set.values())
    
    @staticmethod
    def _python_type_to_schema(type_str: str) -> dict:
        """Convert Python type string to OpenAPI schema."""
        type_map = {
            "str": {"type": "string"},
            "string": {"type": "string"},
            "int": {"type": "integer"},
            "integer": {"type": "integer"},
            "float": {"type": "number"},
            "number": {"type": "number"},
            "bool": {"type": "boolean"},
            "boolean": {"type": "boolean"},
            "list": {"type": "array", "items": {"type": "string"}},
            "array": {"type": "array", "items": {"type": "string"}},
            "dict": {"type": "object"},
            "object": {"type": "object"},
            "uuid": {"type": "string", "format": "uuid"},
            "date": {"type": "string", "format": "date"},
            "datetime": {"type": "string", "format": "date-time"},
            "email": {"type": "string", "format": "email"},
            "url": {"type": "string", "format": "uri"},
            "slug": {"type": "string", "pattern": "^[a-z0-9-]+$"},
            "path": {"type": "string"},
        }
        return type_map.get(type_str.lower(), {"type": "string"})


def extract_route_params(path: str) -> List[dict]:
    """Extract parameter info from route path pattern."""
    params = []
    for match in re.finditer(r'\{(\w+)(?::(\w+))?\}', path):
        name = match.group(1)
        param_type = match.group(2) or "str"
        params.append({
            "name": name,
            "type": param_type,
            "required": True,
            "description": f"Path parameter: {name}",
            "example": _get_example_for_param(name, param_type)
        })
    return params


def _get_example_for_param(name: str, param_type: str) -> Any:
    """Generate example value based on parameter name and type."""
    name_examples = {
        "user_id": 1, "product_id": 42, "id": 1,
        "slug": "example-post", "category": "electronics",
        "query": "python", "name": "alice", "username": "johndoe",
        "email": "user@example.com", "page": 1, "limit": 10,
        "room": "general", "token": "abc123",
        "tag": "programming", "status": "active",
    }
    
    type_examples = {
        "int": 1, "integer": 1, "float": 3.14,
        "bool": True, "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "date": "2025-01-19", "email": "user@example.com",
        "slug": "example-slug",
    }
    
    return name_examples.get(name.lower(), type_examples.get(param_type, f"example_{name}"))


def extract_function_info(func) -> dict:
    """Extract documentation info from a function."""
    info = {
        "name": func.__name__,
        "description": "",
        "parameters": {},
        "return_type": None,
    }
    
    # Get docstring
    if func.__doc__:
        lines = func.__doc__.strip().split("\n")
        info["description"] = lines[0].strip()
    
    # Get type hints
    try:
        hints = get_type_hints(func)
        for param_name, param_type in hints.items():
            if param_name == "return":
                info["return_type"] = str(param_type)
            else:
                info["parameters"][param_name] = str(param_type)
    except Exception:
        pass
    
    # Get default values from signature
    try:
        sig = inspect.signature(func)
        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls", "request", "websocket", "ws", "background_tasks"):
                continue
            if param.default != inspect.Parameter.empty:
                if param_name not in info["parameters"]:
                    info["parameters"][param_name] = {}
                if isinstance(info["parameters"][param_name], str):
                    info["parameters"][param_name] = {"type": info["parameters"][param_name]}
                info["parameters"][param_name]["default"] = param.default
    except Exception:
        pass
    
    return info
