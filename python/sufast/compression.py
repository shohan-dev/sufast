"""
Sufast Response Compression - gzip and deflate compression.
=============================================================
Automatically compresses responses based on Accept-Encoding header.

Usage:
    from sufast.compression import CompressionMiddleware
    
    app.add_middleware(CompressionMiddleware, minimum_size=500)
"""

import gzip
import zlib
from typing import Optional, Set
from .request import Request, Response


class CompressionMiddleware:
    """Response compression middleware supporting gzip and deflate.
    
    Automatically compresses responses when:
    - Client sends Accept-Encoding header
    - Response body exceeds minimum_size
    - Content-Type is compressible (text, json, xml, etc.)
    
    Args:
        minimum_size: Minimum body size to compress (bytes, default 500)
        compression_level: gzip compression level (1-9, default 6)
        compressible_types: Set of compressible content types
    """
    
    # Content types that benefit from compression
    DEFAULT_COMPRESSIBLE = {
        "text/html",
        "text/css",
        "text/plain",
        "text/xml",
        "text/javascript",
        "application/json",
        "application/javascript",
        "application/xml",
        "application/xhtml+xml",
        "application/rss+xml",
        "application/atom+xml",
        "image/svg+xml",
        "application/vnd.api+json",
    }
    
    def __init__(
        self,
        minimum_size: int = 500,
        compression_level: int = 6,
        compressible_types: Optional[Set[str]] = None,
    ):
        self.minimum_size = minimum_size
        self.compression_level = compression_level
        self.compressible_types = compressible_types or self.DEFAULT_COMPRESSIBLE
    
    def process_request(self, request: Request) -> Optional[Response]:
        return None
    
    def process_response(self, request: Request, response: Response) -> Response:
        """Compress response if applicable."""
        accept_encoding = request.headers.get("accept-encoding", "")
        if not accept_encoding:
            return response
        
        # Check content type
        content_type = response.content_type.split(";")[0].strip() if response.content_type else ""
        if content_type not in self.compressible_types:
            return response
        
        # Get body bytes
        body = self._get_body_bytes(response)
        if len(body) < self.minimum_size:
            return response
        
        # Don't double-compress
        if response.headers.get("content-encoding"):
            return response
        
        # Choose encoding
        encodings = self._parse_accept_encoding(accept_encoding)
        
        if "gzip" in encodings:
            compressed = gzip.compress(body, compresslevel=self.compression_level)
            if len(compressed) < len(body):
                response.content = compressed
                response.headers["content-encoding"] = "gzip"
                response.headers["vary"] = "Accept-Encoding"
                # Remove old content-length; will be recalculated
                response.headers.pop("content-length", None)
        elif "deflate" in encodings:
            compressed = zlib.compress(body, self.compression_level)
            if len(compressed) < len(body):
                response.content = compressed
                response.headers["content-encoding"] = "deflate"
                response.headers["vary"] = "Accept-Encoding"
                response.headers.pop("content-length", None)
        
        return response
    
    def _get_body_bytes(self, response: Response) -> bytes:
        """Get response body as bytes."""
        content = response.content
        if isinstance(content, bytes):
            return content
        if isinstance(content, str):
            return content.encode("utf-8")
        if content is None:
            return b""
        return str(content).encode("utf-8")
    
    def _parse_accept_encoding(self, header: str) -> set:
        """Parse Accept-Encoding header into a set of encodings."""
        encodings = set()
        for part in header.split(","):
            encoding = part.strip().split(";")[0].strip().lower()
            if encoding:
                encodings.add(encoding)
        return encodings
