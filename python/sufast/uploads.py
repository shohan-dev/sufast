"""
Sufast File Upload Support - Multipart form data parsing.
===========================================================
Parse multipart/form-data requests for file uploads.

Usage:
    from sufast.uploads import UploadFile, parse_multipart

    @app.post("/upload")
    async def upload(request: Request):
        form = parse_multipart(request)
        file = form.files.get("avatar")
        if file:
            await file.save(f"uploads/{file.filename}")
        return {"filename": file.filename, "size": file.size}
"""

import os
import re
import tempfile
from typing import Any, Dict, List, Optional, BinaryIO
from io import BytesIO


class UploadFile:
    """Represents an uploaded file.
    
    Attributes:
        filename: Original filename from the client
        content_type: MIME type of the file
        size: File size in bytes
        headers: Multipart headers for this part
    """
    
    def __init__(
        self,
        filename: str,
        content_type: str = "application/octet-stream",
        content: bytes = b"",
        headers: Dict[str, str] = None,
    ):
        self.filename = self._sanitize_filename(filename)
        self.content_type = content_type
        self._content = content
        self.headers = headers or {}
        self.size = len(content)
    
    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal and other attacks."""
        # Remove path separators
        filename = filename.replace("/", "").replace("\\", "")
        # Remove null bytes
        filename = filename.replace("\x00", "")
        # Strip leading/trailing whitespace and dots
        filename = filename.strip().strip(".")
        # Remove control characters
        filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255 - len(ext)] + ext
        return filename or "unnamed"
    
    @property
    def content(self) -> bytes:
        """Get file content as bytes."""
        return self._content
    
    def read(self) -> bytes:
        """Read file content."""
        return self._content
    
    async def save(self, path: str, create_dirs: bool = True):
        """Save uploaded file to disk.
        
        Args:
            path: Destination file path
            create_dirs: Create parent directories if needed
        """
        if create_dirs:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        
        # Prevent path traversal
        abs_path = os.path.abspath(path)
        
        with open(abs_path, "wb") as f:
            f.write(self._content)
    
    def __repr__(self):
        return f"UploadFile(filename={self.filename!r}, size={self.size}, content_type={self.content_type!r})"


class FormData:
    """Parsed multipart form data container.
    
    Attributes:
        fields: Regular form fields (name -> value)
        files: Uploaded files (name -> UploadFile)
    """
    
    def __init__(self):
        self.fields: Dict[str, str] = {}
        self.files: Dict[str, UploadFile] = {}
        self._file_list: Dict[str, List[UploadFile]] = {}
    
    def get(self, name: str, default: Any = None) -> Any:
        """Get a field value or file."""
        if name in self.fields:
            return self.fields[name]
        if name in self.files:
            return self.files[name]
        return default
    
    def get_list(self, name: str) -> List[UploadFile]:
        """Get all files with a given field name (for multiple file uploads)."""
        return self._file_list.get(name, [])
    
    def __repr__(self):
        return f"FormData(fields={list(self.fields.keys())}, files={list(self.files.keys())})"


def parse_multipart(request) -> FormData:
    """Parse multipart/form-data from a Request object.
    
    Args:
        request: Sufast Request object
    
    Returns:
        FormData with parsed fields and files
    
    Usage:
        @app.post("/upload")
        async def upload(request: Request):
            form = parse_multipart(request)
            name = form.fields.get("name", "")
            avatar = form.files.get("avatar")
            if avatar:
                await avatar.save(f"uploads/{avatar.filename}")
            return {"name": name, "file": avatar.filename if avatar else None}
    """
    content_type = request.headers.get("content-type", "")
    body = request.body if isinstance(request.body, bytes) else request.body.encode("utf-8")
    
    form = FormData()
    
    if "multipart/form-data" in content_type:
        boundary = _extract_boundary(content_type)
        if boundary:
            _parse_multipart_body(body, boundary, form)
    elif "application/x-www-form-urlencoded" in content_type:
        from urllib.parse import parse_qs
        parsed = parse_qs(body.decode("utf-8", errors="replace"), keep_blank_values=True)
        for k, v in parsed.items():
            form.fields[k] = v[0] if v else ""
    
    return form


def _extract_boundary(content_type: str) -> Optional[str]:
    """Extract boundary from Content-Type header."""
    match = re.search(r'boundary=([^\s;]+)', content_type)
    if match:
        boundary = match.group(1).strip('"')
        return boundary
    return None


def _parse_multipart_body(body: bytes, boundary: str, form: FormData):
    """Parse multipart body into FormData."""
    boundary_bytes = f"--{boundary}".encode()
    end_boundary = f"--{boundary}--".encode()
    
    # Split body by boundary
    parts = body.split(boundary_bytes)
    
    for part in parts:
        if not part or part.strip() == b"" or part.strip() == b"--":
            continue
        
        # Remove leading \r\n and trailing boundary markers
        part = part.strip(b"\r\n")
        if part == b"--" or part == b"":
            continue
        
        # Split headers from body
        header_end = part.find(b"\r\n\r\n")
        if header_end == -1:
            continue
        
        header_data = part[:header_end].decode("utf-8", errors="replace")
        body_data = part[header_end + 4:]
        
        # Remove trailing \r\n
        if body_data.endswith(b"\r\n"):
            body_data = body_data[:-2]
        
        # Parse headers
        headers = {}
        for line in header_data.split("\r\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip()
        
        # Parse Content-Disposition
        disposition = headers.get("content-disposition", "")
        name_match = re.search(r'name="([^"]*)"', disposition)
        filename_match = re.search(r'filename="([^"]*)"', disposition)
        
        if not name_match:
            continue
        
        field_name = name_match.group(1)
        
        if filename_match:
            # File upload
            filename = filename_match.group(1)
            file_content_type = headers.get("content-type", "application/octet-stream")
            
            upload = UploadFile(
                filename=filename,
                content_type=file_content_type,
                content=body_data,
                headers=headers,
            )
            
            form.files[field_name] = upload
            if field_name not in form._file_list:
                form._file_list[field_name] = []
            form._file_list[field_name].append(upload)
        else:
            # Regular field
            form.fields[field_name] = body_data.decode("utf-8", errors="replace")
