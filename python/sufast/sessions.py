"""
Sufast Session Management - Server-side sessions with pluggable backends.
==========================================================================
Cookie-based session management with in-memory and file-based backends.

Usage:
    from sufast.sessions import SessionMiddleware, InMemorySessionStore

    app.add_middleware(
        SessionMiddleware,
        secret_key="your-secret-key",
        store=InMemorySessionStore(),
    )

    @app.get("/dashboard")
    async def dashboard(request: Request):
        session = request.state.get("session", {})
        username = session.get("username", "Guest")
        return {"hello": username}
"""

import hashlib
import hmac
import json
import os
import time
import secrets
import threading
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod


# ======================================================
# Session Stores
# ======================================================

class SessionStore(ABC):
    """Abstract session storage backend."""
    
    @abstractmethod
    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data."""
        pass
    
    @abstractmethod
    def set(self, session_id: str, data: Dict[str, Any], ttl: int = 3600):
        """Store session data."""
        pass
    
    @abstractmethod
    def delete(self, session_id: str):
        """Delete a session."""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Remove expired sessions."""
        pass


class InMemorySessionStore(SessionStore):
    """In-memory session store. Fast but not persistent across restarts.
    
    Suitable for development and small applications.
    For production, consider FileSessionStore or a Redis-backed store.
    """
    
    def __init__(self, max_sessions: int = 10000):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._expiry: Dict[str, float] = {}
        self._lock = threading.Lock()
        self.max_sessions = max_sessions
    
    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            if session_id in self._expiry:
                if time.time() > self._expiry[session_id]:
                    self._remove(session_id)
                    return None
            return self._sessions.get(session_id)
    
    def set(self, session_id: str, data: Dict[str, Any], ttl: int = 3600):
        with self._lock:
            # Evict oldest if at capacity
            if len(self._sessions) >= self.max_sessions and session_id not in self._sessions:
                self._evict_oldest()
            
            self._sessions[session_id] = data
            self._expiry[session_id] = time.time() + ttl
    
    def delete(self, session_id: str):
        with self._lock:
            self._remove(session_id)
    
    def cleanup(self):
        now = time.time()
        with self._lock:
            expired = [sid for sid, exp in self._expiry.items() if now > exp]
            for sid in expired:
                self._remove(sid)
    
    def _remove(self, session_id: str):
        self._sessions.pop(session_id, None)
        self._expiry.pop(session_id, None)
    
    def _evict_oldest(self):
        if self._expiry:
            oldest = min(self._expiry, key=self._expiry.get)
            self._remove(oldest)


class FileSessionStore(SessionStore):
    """File-based session store. Persistent across restarts.
    
    Stores each session as a JSON file in the specified directory.
    """
    
    def __init__(self, directory: str = ".sessions"):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)
        self._lock = threading.Lock()
    
    def _path(self, session_id: str) -> str:
        # Sanitize to prevent path traversal
        safe_id = hashlib.sha256(session_id.encode()).hexdigest()
        return os.path.join(self.directory, f"{safe_id}.json")
    
    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        path = self._path(session_id)
        with self._lock:
            try:
                if not os.path.exists(path):
                    return None
                with open(path, "r") as f:
                    record = json.load(f)
                if record.get("expires_at", 0) < time.time():
                    os.remove(path)
                    return None
                return record.get("data")
            except (json.JSONDecodeError, IOError):
                return None
    
    def set(self, session_id: str, data: Dict[str, Any], ttl: int = 3600):
        path = self._path(session_id)
        record = {
            "data": data,
            "expires_at": time.time() + ttl,
            "created_at": time.time(),
        }
        with self._lock:
            try:
                with open(path, "w") as f:
                    json.dump(record, f)
            except IOError:
                pass
    
    def delete(self, session_id: str):
        path = self._path(session_id)
        with self._lock:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass
    
    def cleanup(self):
        now = time.time()
        with self._lock:
            try:
                for fname in os.listdir(self.directory):
                    if not fname.endswith(".json"):
                        continue
                    path = os.path.join(self.directory, fname)
                    try:
                        with open(path, "r") as f:
                            record = json.load(f)
                        if record.get("expires_at", 0) < now:
                            os.remove(path)
                    except (json.JSONDecodeError, IOError):
                        pass
            except IOError:
                pass


# ======================================================
# Session Middleware
# ======================================================

class SessionMiddleware:
    """Session middleware for Sufast.
    
    Manages cookie-based server-side sessions with HMAC-signed session IDs.
    
    Args:
        secret_key: Secret key for signing session cookies
        store: Session storage backend (default: InMemorySessionStore)
        cookie_name: Session cookie name (default: "sufast_session")
        max_age: Session TTL in seconds (default: 3600)
        cookie_path: Cookie path (default: "/")
        cookie_secure: Secure cookie flag (default: False)
        cookie_httponly: HttpOnly cookie flag (default: True)
        cookie_samesite: SameSite cookie attribute (default: "Lax")
    """
    
    def __init__(
        self,
        secret_key: str = "",
        store: Optional[SessionStore] = None,
        cookie_name: str = "sufast_session",
        max_age: int = 3600,
        cookie_path: str = "/",
        cookie_secure: bool = False,
        cookie_httponly: bool = True,
        cookie_samesite: str = "Lax",
    ):
        if not secret_key:
            raise ValueError("secret_key is required for SessionMiddleware")
        self.secret_key = secret_key.encode("utf-8") if isinstance(secret_key, str) else secret_key
        self.store = store or InMemorySessionStore()
        self.cookie_name = cookie_name
        self.max_age = max_age
        self.cookie_path = cookie_path
        self.cookie_secure = cookie_secure
        self.cookie_httponly = cookie_httponly
        self.cookie_samesite = cookie_samesite
    
    def _sign_session_id(self, session_id: str) -> str:
        """Sign a session ID with HMAC."""
        sig = hmac.new(self.secret_key, session_id.encode(), hashlib.sha256).hexdigest()[:16]
        return f"{session_id}.{sig}"
    
    def _verify_session_id(self, signed: str) -> Optional[str]:
        """Verify and extract a session ID."""
        if "." not in signed:
            return None
        session_id, sig = signed.rsplit(".", 1)
        expected = hmac.new(self.secret_key, session_id.encode(), hashlib.sha256).hexdigest()[:16]
        if hmac.compare_digest(sig, expected):
            return session_id
        return None
    
    def process_request(self, request) -> None:
        """Load session data into request.state."""
        session_data = {}
        
        # Get session ID from cookie
        cookie_value = request.cookies.get(self.cookie_name, "")
        session_id = None
        
        if cookie_value:
            session_id = self._verify_session_id(cookie_value)
            if session_id:
                data = self.store.get(session_id)
                if data:
                    session_data = data
                else:
                    session_id = None  # Session expired
        
        if not session_id:
            session_id = secrets.token_hex(24)
        
        request.state["session"] = session_data
        request.state["_session_id"] = session_id
        request.state["_session_modified"] = False
        
        return None  # Continue to handler
    
    def process_response(self, request, response) -> 'Response':
        """Save session and set cookie."""
        session_data = request.state.get("session", {})
        session_id = request.state.get("_session_id")
        
        if session_id and session_data:
            self.store.set(session_id, session_data, self.max_age)
            
            # Set cookie
            signed = self._sign_session_id(session_id)
            response.set_cookie(
                self.cookie_name,
                signed,
                max_age=self.max_age,
                path=self.cookie_path,
                secure=self.cookie_secure,
                httponly=self.cookie_httponly,
                samesite=self.cookie_samesite,
            )
        
        return response
