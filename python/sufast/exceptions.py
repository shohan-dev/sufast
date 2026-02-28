"""
Sufast HTTP Exceptions - FastAPI-compatible exception handling.
"""

from typing import Any, Dict, Optional


class HTTPException(Exception):
    """HTTP exception with status code and detail message.
    
    Usage:
        raise HTTPException(status_code=404, detail="Item not found")
        raise HTTPException(404, "Not found", headers={"X-Error": "missing"})
    """
    
    def __init__(
        self,
        status_code: int = 500,
        detail: Any = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.status_code = status_code
        self.detail = detail or self._default_detail(status_code)
        self.headers = headers or {}
        super().__init__(self.detail)
    
    @staticmethod
    def _default_detail(status_code: int) -> str:
        defaults = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            408: "Request Timeout",
            409: "Conflict",
            410: "Gone",
            413: "Payload Too Large",
            415: "Unsupported Media Type",
            422: "Unprocessable Entity",
            429: "Too Many Requests",
            500: "Internal Server Error",
            501: "Not Implemented",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout",
        }
        return defaults.get(status_code, "Error")
    
    def to_dict(self) -> dict:
        return {"detail": self.detail, "status_code": self.status_code}


class WebSocketException(Exception):
    """WebSocket-specific exception."""
    
    def __init__(self, code: int = 1008, reason: str = ""):
        self.code = code
        self.reason = reason
        super().__init__(reason)


class RequestValidationError(HTTPException):
    """Raised when request validation fails."""
    
    def __init__(self, errors: list, body: Any = None):
        self.errors = errors
        self.body = body
        detail = {"errors": errors}
        if body is not None:
            detail["body"] = str(body)
        super().__init__(status_code=422, detail=detail)


# Convenience factory functions
def bad_request(detail: str = "Bad Request") -> HTTPException:
    return HTTPException(400, detail)

def unauthorized(detail: str = "Unauthorized") -> HTTPException:
    return HTTPException(401, detail)

def forbidden(detail: str = "Forbidden") -> HTTPException:
    return HTTPException(403, detail)

def not_found(detail: str = "Not Found") -> HTTPException:
    return HTTPException(404, detail)

def method_not_allowed(detail: str = "Method Not Allowed") -> HTTPException:
    return HTTPException(405, detail)

def conflict(detail: str = "Conflict") -> HTTPException:
    return HTTPException(409, detail)

def unprocessable(detail: str = "Unprocessable Entity") -> HTTPException:
    return HTTPException(422, detail)

def too_many_requests(detail: str = "Too Many Requests") -> HTTPException:
    return HTTPException(429, detail)

def internal_error(detail: str = "Internal Server Error") -> HTTPException:
    return HTTPException(500, detail)

def service_unavailable(detail: str = "Service Unavailable") -> HTTPException:
    return HTTPException(503, detail)


# HTTP status code descriptions
STATUS_PHRASES = {
    100: "Continue",
    101: "Switching Protocols",
    102: "Processing",
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    304: "Not Modified",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    413: "Payload Too Large",
    415: "Unsupported Media Type",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}
