"""
Sufast Test Client
==================
Test your Sufast application without starting a server.
Works like FastAPI/Starlette TestClient.

Usage:
    from sufast import Sufast
    from sufast.testclient import TestClient
    
    app = Sufast()
    
    @app.get("/hello")
    async def hello():
        return {"message": "Hello World"}
    
    client = TestClient(app)
    
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
"""

import asyncio
import json
from typing import Any, Dict, Optional, Union
from urllib.parse import urlencode, urlparse, parse_qs

from .request import Request, Response
from .exceptions import HTTPException


class TestResponse:
    """Response object returned by TestClient."""
    
    def __init__(self, status_code: int, headers: Dict[str, str], body: Any):
        self.status_code = status_code
        self.headers = headers
        self._body = body
        
        self.ok = 200 <= status_code < 300
        self.is_success = self.ok
        self.is_redirect = 300 <= status_code < 400
        self.is_client_error = 400 <= status_code < 500
        self.is_server_error = 500 <= status_code < 600
    
    @property
    def text(self) -> str:
        """Response body as text."""
        if isinstance(self._body, bytes):
            return self._body.decode('utf-8', errors='replace')
        return str(self._body)
    
    @property
    def content(self) -> bytes:
        """Response body as bytes."""
        if isinstance(self._body, bytes):
            return self._body
        if isinstance(self._body, str):
            return self._body.encode('utf-8')
        return str(self._body).encode('utf-8')
    
    def json(self) -> Any:
        """Parse response body as JSON."""
        return json.loads(self.text)
    
    def raise_for_status(self):
        """Raise an exception if status >= 400."""
        if self.status_code >= 400:
            raise HTTPException(self.status_code, self.text)
    
    def __repr__(self):
        return f"<TestResponse [{self.status_code}]>"


class TestClient:
    """Test client for Sufast applications.
    
    Makes requests directly to the application without starting a server.
    
    Args:
        app: Sufast application instance
        base_url: Base URL for requests (default: "http://testserver")
    """
    
    def __init__(self, app, base_url: str = "http://testserver"):
        self.app = app
        self.base_url = base_url.rstrip("/")
        self._loop = None
        self._cookies: Dict[str, str] = {}
        self._default_headers: Dict[str, str] = {
            "User-Agent": "Sufast-TestClient/1.0",
            "Accept": "application/json",
        }
    
    def _get_loop(self):
        """Get or create event loop."""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_event_loop()
                if self._loop.is_closed():
                    raise RuntimeError
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop
    
    def _prepare_request(self, method: str, url: str, 
                          headers: Dict[str, str] = None,
                          params: Dict[str, Any] = None,
                          json_data: Any = None,
                          data: Any = None,
                          content: bytes = None) -> tuple:
        """Prepare a request. Returns (method, path, headers, body, query_string)."""
        # Parse URL
        if url.startswith("/"):
            path = url
        elif url.startswith("http"):
            parsed = urlparse(url)
            path = parsed.path
            if parsed.query:
                if params:
                    existing = parse_qs(parsed.query)
                    existing.update({k: [v] for k, v in params.items()})
                    params = {k: v[0] if len(v) == 1 else v for k, v in existing.items()}
                else:
                    params = {k: v[0] if len(v) == 1 else v 
                             for k, v in parse_qs(parsed.query).items()}
        else:
            path = "/" + url
        
        # Build query string
        query_string = ""
        if params:
            query_string = urlencode(params, doseq=True)
        
        # Build headers
        req_headers = dict(self._default_headers)
        if headers:
            req_headers.update(headers)
        
        # Add cookies
        if self._cookies:
            cookie_str = "; ".join(f"{k}={v}" for k, v in self._cookies.items())
            req_headers["Cookie"] = cookie_str
        
        # Build body
        body = b""
        if json_data is not None:
            body = json.dumps(json_data, default=str).encode('utf-8')
            req_headers.setdefault("Content-Type", "application/json")
        elif data is not None:
            if isinstance(data, dict):
                body = urlencode(data).encode('utf-8')
                req_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
            elif isinstance(data, str):
                body = data.encode('utf-8')
            elif isinstance(data, bytes):
                body = data
        elif content is not None:
            body = content
        
        return method, path, req_headers, body, query_string
    
    def _make_request(self, method: str, url: str, **kwargs) -> TestResponse:
        """Make a request to the application."""
        method, path, headers, body, query_string = self._prepare_request(
            method, url, **kwargs
        )
        
        loop = self._get_loop()
        
        try:
            result = loop.run_until_complete(
                self.app._handle_request(
                    method=method,
                    path=path,
                    headers=headers,
                    body=body,
                    query_string=query_string,
                )
            )
        except HTTPException as exc:
            result = {
                "status": exc.status_code,
                "headers": {"Content-Type": "application/json", **exc.headers},
                "body": json.dumps({"detail": exc.detail})
            }
        except Exception as exc:
            result = {
                "status": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"detail": str(exc)})
            }
        
        status = result.get("status", 200)
        resp_headers = result.get("headers", {})
        resp_body = result.get("body", "")
        
        # Process set-cookie headers
        if "Set-Cookie" in resp_headers:
            cookie_str = resp_headers["Set-Cookie"]
            parts = cookie_str.split(";")[0].strip()
            if "=" in parts:
                k, v = parts.split("=", 1)
                self._cookies[k.strip()] = v.strip()
        
        return TestResponse(status, resp_headers, resp_body)
    
    def get(self, url: str, **kwargs) -> TestResponse:
        """Send a GET request."""
        return self._make_request("GET", url, **kwargs)
    
    def post(self, url: str, **kwargs) -> TestResponse:
        """Send a POST request."""
        return self._make_request("POST", url, **kwargs)
    
    def put(self, url: str, **kwargs) -> TestResponse:
        """Send a PUT request."""
        return self._make_request("PUT", url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> TestResponse:
        """Send a DELETE request."""
        return self._make_request("DELETE", url, **kwargs)
    
    def patch(self, url: str, **kwargs) -> TestResponse:
        """Send a PATCH request."""
        return self._make_request("PATCH", url, **kwargs)
    
    def head(self, url: str, **kwargs) -> TestResponse:
        """Send a HEAD request."""
        return self._make_request("HEAD", url, **kwargs)
    
    def options(self, url: str, **kwargs) -> TestResponse:
        """Send an OPTIONS request."""
        return self._make_request("OPTIONS", url, **kwargs)
    
    def set_cookie(self, name: str, value: str):
        """Set a cookie for subsequent requests."""
        self._cookies[name] = value
    
    def clear_cookies(self):
        """Clear all cookies."""
        self._cookies.clear()
    
    def close(self):
        """Close the test client."""
        if self._loop and not self._loop.is_closed():
            self._loop.close()
            self._loop = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
    
    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
