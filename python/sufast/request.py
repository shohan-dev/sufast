"""
Request and Response objects for Sufast framework.
"""
import json
import mimetypes
from typing import Dict, Any, Optional, Union, List, IO
from urllib.parse import parse_qs, unquote
from http.cookies import SimpleCookie


class Request:
    """HTTP Request object with all request data."""
    
    def __init__(self, method: str, path: str, headers: Dict[str, str], 
                 body: Union[bytes, str], query_string: str = "",
                 path_params: Optional[Dict[str, str]] = None,
                 query_params: Optional[Dict[str, str]] = None):
        self.method = method.upper()
        self.path = path
        self.headers = {k.lower(): v for k, v in headers.items()}  # Normalize headers
        
        # Handle body as bytes or string
        if isinstance(body, str):
            self.body = body.encode('utf-8')
        else:
            self.body = body
            
        self.query_string = query_string
        self._query_params = query_params  # Pre-parsed from Rust
        self._json_data = None
        self._form_data = None
        self._cookies = None
        self.path_params = path_params or {}  # Pre-extracted from Rust
        self.remote_addr = headers.get('x-forwarded-for', '127.0.0.1')
    
    @property
    def query_params(self) -> Dict[str, str]:
        """Parse and return query parameters."""
        if self._query_params is None:
            if self.query_string:
                parsed = parse_qs(self.query_string, keep_blank_values=True)
                # Convert list values to single values
                self._query_params = {k: v[0] if v else "" for k, v in parsed.items()}
            else:
                self._query_params = {}
        return self._query_params
    
    @property
    def json(self) -> Optional[Dict[str, Any]]:
        """Parse request body as JSON."""
        if self._json_data is None and self.body:
            content_type = self.headers.get('content-type', '')
            if 'application/json' in content_type:
                try:
                    self._json_data = json.loads(self.body.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return None
        return self._json_data
    
    @property
    def form(self) -> Dict[str, str]:
        """Parse form data from request body."""
        if self._form_data is None:
            content_type = self.headers.get('content-type', '')
            if 'application/x-www-form-urlencoded' in content_type:
                try:
                    form_string = self.body.decode('utf-8')
                    parsed = parse_qs(form_string, keep_blank_values=True)
                    self._form_data = {k: v[0] if v else "" for k, v in parsed.items()}
                except UnicodeDecodeError:
                    self._form_data = {}
            else:
                self._form_data = {}
        return self._form_data
    
    @property
    def cookies(self) -> Dict[str, str]:
        """Parse cookies from request headers."""
        if self._cookies is None:
            cookie_header = self.headers.get('cookie', '')
            if cookie_header:
                cookie = SimpleCookie()
                cookie.load(cookie_header)
                self._cookies = {key: morsel.value for key, morsel in cookie.items()}
            else:
                self._cookies = {}
        return self._cookies
    
    def get_header(self, name: str, default: str = None) -> Optional[str]:
        """Get header value by name (case-insensitive)."""
        return self.headers.get(name.lower(), default)
    
    @property
    def content_type(self) -> str:
        """Get content type of request."""
        return self.headers.get('content-type', '')
    
    @property
    def content_length(self) -> int:
        """Get content length of request."""
        try:
            return int(self.headers.get('content-length', '0'))
        except ValueError:
            return 0
    
    @property
    def is_json(self) -> bool:
        """Check if request has JSON content type."""
        return 'application/json' in self.content_type
    
    @property
    def is_form(self) -> bool:
        """Check if request has form content type."""
        return 'application/x-www-form-urlencoded' in self.content_type
    
    @property
    def user_agent(self) -> str:
        """Get user agent string."""
        return self.headers.get('user-agent', '')


class Response:
    """HTTP Response object for building responses."""
    
    def __init__(self, content: Any = None, status: int = 200, 
                 headers: Optional[Dict[str, str]] = None, 
                 content_type: str = 'application/json'):
        self.content = content
        self.status = status
        self.headers = headers or {}
        self.content_type = content_type
        self._cookies = SimpleCookie()
    
    def set_header(self, name: str, value: str) -> 'Response':
        """Set response header."""
        self.headers[name] = value
        return self
    
    def set_cookie(self, name: str, value: str, max_age: Optional[int] = None,
                   expires: Optional[str] = None, path: str = '/',
                   domain: Optional[str] = None, secure: bool = False,
                   httponly: bool = False, samesite: Optional[str] = None) -> 'Response':
        """Set cookie in response."""
        self._cookies[name] = value
        if max_age is not None:
            self._cookies[name]['max-age'] = max_age
        if expires is not None:
            self._cookies[name]['expires'] = expires
        self._cookies[name]['path'] = path
        if domain is not None:
            self._cookies[name]['domain'] = domain
        if secure:
            self._cookies[name]['secure'] = True
        if httponly:
            self._cookies[name]['httponly'] = True
        if samesite is not None:
            self._cookies[name]['samesite'] = samesite
        return self
    
    def delete_cookie(self, name: str, path: str = '/') -> 'Response':
        """Delete cookie by setting it to expire."""
        self.set_cookie(name, '', max_age=0, path=path)
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for Rust."""
        headers = self.headers.copy()
        headers['content-type'] = self.content_type
        
        # Add cookies to headers
        for cookie in self._cookies.values():
            if 'set-cookie' not in headers:
                headers['set-cookie'] = []
            elif not isinstance(headers['set-cookie'], list):
                headers['set-cookie'] = [headers['set-cookie']]
            headers['set-cookie'].append(cookie.OutputString())
        
        # Serialize content based on type
        if self.content_type == 'application/json':
            if self.content is None:
                body = 'null'
            else:
                body = json.dumps(self.content, default=str)
        elif isinstance(self.content, str):
            body = self.content
        elif isinstance(self.content, bytes):
            body = self.content.decode('utf-8', errors='replace')
        else:
            body = str(self.content)
        
        return {
            'status': self.status,
            'headers': headers,
            'body': body
        }


# Convenience response builders
def json_response(data: Any, status: int = 200, headers: Optional[Dict[str, str]] = None) -> Response:
    """Create JSON response."""
    return Response(data, status, headers, 'application/json')

def html_response(html: str, status: int = 200, headers: Optional[Dict[str, str]] = None) -> Response:
    """Create HTML response."""
    return Response(html, status, headers, 'text/html')

def text_response(text: str, status: int = 200, headers: Optional[Dict[str, str]] = None) -> Response:
    """Create plain text response."""
    return Response(text, status, headers, 'text/plain')

def redirect_response(url: str, status: int = 302) -> Response:
    """Create redirect response."""
    return Response('', status, {'location': url})

def file_response(file_path: str, filename: Optional[str] = None) -> Response:
    """Create file download response."""
    import os
    if not os.path.exists(file_path):
        return Response({'error': 'File not found'}, 404)
    
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'
    
    headers = {}
    if filename:
        headers['content-disposition'] = f'attachment; filename="{filename}"'
    
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        return Response(content, 200, headers, mime_type)
    except Exception as e:
        return Response({'error': f'Error reading file: {str(e)}'}, 500)
