"""
Sufast Security Module - Production-grade security utilities.
==============================================================
JWT authentication, CSRF protection, signed cookies, password hashing,
API key management, and security scanning.

Usage:
    from sufast.security import JWTAuth, CSRFProtection, hash_password, verify_password

    jwt = JWTAuth(secret_key="your-secret-key")
    token = jwt.create_token({"user_id": 123})
    payload = jwt.verify_token(token)
"""

import hashlib
import hmac
import json
import os
import base64
import time
import secrets
import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta


# ======================================================
# JWT Implementation (HMAC-SHA256, no external deps)
# ======================================================

class JWTAuth:
    """JSON Web Token authentication using HMAC-SHA256.
    
    Fully self-contained JWT implementation — no PyJWT dependency required.
    Supports access tokens, refresh tokens, and token blacklisting.
    
    Args:
        secret_key: Secret key for signing tokens (min 32 chars recommended)
        algorithm: Signing algorithm (currently only HS256)
        access_token_expire: Access token TTL in seconds (default 30 min)
        refresh_token_expire: Refresh token TTL in seconds (default 7 days)
        issuer: Token issuer claim
    
    Usage:
        jwt = JWTAuth(secret_key="super-secret-key-min-32-chars-long!")
        
        # Create token
        token = jwt.create_token({"user_id": 42, "role": "admin"})
        
        # Verify token
        payload = jwt.verify_token(token)
        # Returns: {"user_id": 42, "role": "admin", "iat": ..., "exp": ...}
        
        # Refresh token
        refresh = jwt.create_refresh_token({"user_id": 42})
        new_access = jwt.refresh_access_token(refresh)
    """
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire: int = 1800,      # 30 minutes
        refresh_token_expire: int = 604800,    # 7 days
        issuer: Optional[str] = None,
    ):
        if len(secret_key) < 16:
            raise ValueError("Secret key must be at least 16 characters for security")
        self.secret_key = secret_key.encode("utf-8") if isinstance(secret_key, str) else secret_key
        self.algorithm = algorithm
        self.access_token_expire = access_token_expire
        self.refresh_token_expire = refresh_token_expire
        self.issuer = issuer
        self._blacklist: set = set()
    
    @staticmethod
    def _base64url_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")
    
    @staticmethod
    def _base64url_decode(s: str) -> bytes:
        padding = 4 - len(s) % 4
        if padding != 4:
            s += "=" * padding
        return base64.urlsafe_b64decode(s)
    
    def _sign(self, message: str) -> str:
        sig = hmac.new(self.secret_key, message.encode("ascii"), hashlib.sha256).digest()
        return self._base64url_encode(sig)
    
    def create_token(self, payload: Dict[str, Any], expire_seconds: Optional[int] = None) -> str:
        """Create a signed JWT access token.
        
        Args:
            payload: Claims to include in the token
            expire_seconds: Custom expiration (overrides default)
        
        Returns:
            Signed JWT string
        """
        now = int(time.time())
        expire = expire_seconds if expire_seconds is not None else self.access_token_expire
        
        token_payload = {
            **payload,
            "iat": now,
            "exp": now + expire,
            "type": "access",
            "jti": secrets.token_hex(16),
        }
        if self.issuer:
            token_payload["iss"] = self.issuer
        
        header = {"alg": self.algorithm, "typ": "JWT"}
        header_b64 = self._base64url_encode(json.dumps(header, separators=(",", ":")).encode())
        payload_b64 = self._base64url_encode(json.dumps(token_payload, separators=(",", ":"), default=str).encode())
        
        message = f"{header_b64}.{payload_b64}"
        signature = self._sign(message)
        
        return f"{message}.{signature}"
    
    def create_refresh_token(self, payload: Dict[str, Any]) -> str:
        """Create a refresh token with longer expiration."""
        now = int(time.time())
        token_payload = {
            **payload,
            "iat": now,
            "exp": now + self.refresh_token_expire,
            "type": "refresh",
            "jti": secrets.token_hex(16),
        }
        if self.issuer:
            token_payload["iss"] = self.issuer
        
        header = {"alg": self.algorithm, "typ": "JWT"}
        header_b64 = self._base64url_encode(json.dumps(header, separators=(",", ":")).encode())
        payload_b64 = self._base64url_encode(json.dumps(token_payload, separators=(",", ":"), default=str).encode())
        
        message = f"{header_b64}.{payload_b64}"
        signature = self._sign(message)
        
        return f"{message}.{signature}"
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            token_type: Expected token type ("access" or "refresh")
        
        Returns:
            Decoded payload dict
        
        Raises:
            InvalidTokenError: If token is invalid, expired, or blacklisted
        """
        try:
            parts = token.split(".")
            if len(parts) != 3:
                raise InvalidTokenError("Invalid token format")
            
            header_b64, payload_b64, signature = parts
            
            # Verify signature
            expected_sig = self._sign(f"{header_b64}.{payload_b64}")
            if not hmac.compare_digest(signature, expected_sig):
                raise InvalidTokenError("Invalid signature")
            
            # Decode payload
            payload = json.loads(self._base64url_decode(payload_b64))
            
            # Check expiration
            if "exp" in payload and payload["exp"] < int(time.time()):
                raise TokenExpiredError("Token has expired")
            
            # Check token type
            if payload.get("type") != token_type:
                raise InvalidTokenError(f"Expected {token_type} token, got {payload.get('type')}")
            
            # Check issuer
            if self.issuer and payload.get("iss") != self.issuer:
                raise InvalidTokenError("Invalid issuer")
            
            # Check blacklist
            jti = payload.get("jti")
            if jti and jti in self._blacklist:
                raise InvalidTokenError("Token has been revoked")
            
            return payload
            
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError) as e:
            raise InvalidTokenError(f"Token decode error: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """Create a new access token from a valid refresh token.
        
        Args:
            refresh_token: Valid refresh token
        
        Returns:
            New access token string
        """
        payload = self.verify_token(refresh_token, token_type="refresh")
        
        # Remove JWT-specific fields
        new_payload = {k: v for k, v in payload.items() 
                       if k not in ("iat", "exp", "type", "jti", "iss")}
        
        return self.create_token(new_payload)
    
    def revoke_token(self, token: str):
        """Revoke a token by adding its JTI to the blacklist."""
        try:
            parts = token.split(".")
            if len(parts) == 3:
                payload = json.loads(self._base64url_decode(parts[1]))
                jti = payload.get("jti")
                if jti:
                    self._blacklist.add(jti)
        except Exception:
            pass
    
    def extract_bearer_token(self, authorization: str) -> Optional[str]:
        """Extract token from 'Bearer <token>' header."""
        if authorization and authorization.startswith("Bearer "):
            return authorization[7:].strip()
        return None


class InvalidTokenError(Exception):
    """Raised when a JWT token is invalid."""
    pass


class TokenExpiredError(InvalidTokenError):
    """Raised when a JWT token has expired."""
    pass


# ======================================================
# CSRF Protection
# ======================================================

class CSRFProtection:
    """Cross-Site Request Forgery protection.
    
    Generates and validates CSRF tokens using double-submit cookie pattern.
    
    Usage:
        csrf = CSRFProtection(secret_key="your-secret")
        token = csrf.generate_token(session_id="user123")
        is_valid = csrf.validate_token(token, session_id="user123")
    """
    
    def __init__(self, secret_key: str, token_length: int = 32):
        self.secret_key = secret_key.encode("utf-8") if isinstance(secret_key, str) else secret_key
        self.token_length = token_length
    
    def generate_token(self, session_id: str = "") -> str:
        """Generate a CSRF token."""
        random_part = secrets.token_hex(self.token_length)
        timestamp = str(int(time.time()))
        message = f"{random_part}:{timestamp}:{session_id}"
        signature = hmac.new(self.secret_key, message.encode(), hashlib.sha256).hexdigest()
        return f"{random_part}:{timestamp}:{signature}"
    
    def validate_token(self, token: str, session_id: str = "", max_age: int = 3600) -> bool:
        """Validate a CSRF token."""
        try:
            parts = token.split(":")
            if len(parts) != 3:
                return False
            
            random_part, timestamp, signature = parts
            
            # Check age
            token_age = int(time.time()) - int(timestamp)
            if token_age > max_age or token_age < 0:
                return False
            
            # Verify signature
            message = f"{random_part}:{timestamp}:{session_id}"
            expected = hmac.new(self.secret_key, message.encode(), hashlib.sha256).hexdigest()
            return hmac.compare_digest(signature, expected)
            
        except (ValueError, TypeError):
            return False


# ======================================================
# Password Hashing (PBKDF2-SHA256)
# ======================================================

def hash_password(password: str, salt: Optional[bytes] = None, iterations: int = 100_000) -> str:
    """Hash a password using PBKDF2-SHA256.
    
    Args:
        password: Plain text password
        salt: Optional salt (auto-generated if None)
        iterations: Number of PBKDF2 iterations
    
    Returns:
        Formatted hash string: "pbkdf2:sha256:<iterations>$<salt>$<hash>"
    """
    if salt is None:
        salt = os.urandom(16)
    
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    salt_b64 = base64.b64encode(salt).decode("ascii")
    hash_b64 = base64.b64encode(dk).decode("ascii")
    
    return f"pbkdf2:sha256:{iterations}${salt_b64}${hash_b64}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a hash.
    
    Args:
        password: Plain text password to verify
        password_hash: Hash string from hash_password()
    
    Returns:
        True if password matches
    """
    try:
        parts = password_hash.split("$")
        if len(parts) != 3:
            return False
        
        method_parts = parts[0].split(":")
        if len(method_parts) < 3:
            return False
        
        iterations = int(method_parts[2])
        salt = base64.b64decode(parts[1])
        stored_hash = base64.b64decode(parts[2])
        
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(dk, stored_hash)
        
    except Exception:
        return False


# ======================================================
# API Key Management
# ======================================================

class APIKeyManager:
    """Simple API key management for server-to-server auth.
    
    Usage:
        keys = APIKeyManager()
        key = keys.generate_key("service-a")
        is_valid = keys.validate_key(key)
    """
    
    def __init__(self):
        self._keys: Dict[str, Dict[str, Any]] = {}
    
    def generate_key(self, name: str, scopes: List[str] = None, 
                     expires_in: Optional[int] = None) -> str:
        """Generate a new API key."""
        key = f"sk_{secrets.token_hex(24)}"
        self._keys[key] = {
            "name": name,
            "scopes": scopes or ["*"],
            "created_at": time.time(),
            "expires_at": time.time() + expires_in if expires_in else None,
            "active": True,
        }
        return key
    
    def validate_key(self, key: str, required_scope: str = None) -> Optional[Dict[str, Any]]:
        """Validate an API key and return its metadata."""
        info = self._keys.get(key)
        if not info or not info["active"]:
            return None
        
        if info["expires_at"] and info["expires_at"] < time.time():
            return None
        
        if required_scope and "*" not in info["scopes"] and required_scope not in info["scopes"]:
            return None
        
        return info
    
    def revoke_key(self, key: str):
        """Revoke an API key."""
        if key in self._keys:
            self._keys[key]["active"] = False


# ======================================================
# Signed Value Utility
# ======================================================

def sign_value(value: str, secret_key: str, timestamp: Optional[int] = None) -> str:
    """Sign a value with HMAC-SHA256.
    
    Returns: "value|timestamp|signature"
    """
    ts = timestamp or int(time.time())
    key = secret_key.encode("utf-8") if isinstance(secret_key, str) else secret_key
    message = f"{value}|{ts}"
    sig = hmac.new(key, message.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{value}|{ts}|{sig}"


def verify_signed_value(signed: str, secret_key: str, max_age: int = 86400) -> Optional[str]:
    """Verify a signed value. Returns the original value or None if invalid."""
    try:
        parts = signed.split("|")
        if len(parts) != 3:
            return None
        
        value, ts_str, signature = parts
        ts = int(ts_str)
        
        # Check age
        if time.time() - ts > max_age:
            return None
        
        # Verify signature
        key = secret_key.encode("utf-8") if isinstance(secret_key, str) else secret_key
        message = f"{value}|{ts_str}"
        expected = hmac.new(key, message.encode("utf-8"), hashlib.sha256).hexdigest()
        
        if hmac.compare_digest(signature, expected):
            return value
        return None
        
    except (ValueError, TypeError):
        return None


# ======================================================
# Security Scanner
# ======================================================

class SecurityScanner:
    """Basic security checks for request validation.
    
    Prevents common attacks: SQL injection, XSS, path traversal, etc.
    """
    
    # Patterns that indicate potential attacks
    SQL_INJECTION_PATTERNS = [
        r"(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|EXEC)\b.*\b(FROM|INTO|TABLE|SET|WHERE)\b)",
        r"(--|;|\/\*|\*\/|xp_|sp_|0x)",
        r"(\b(OR|AND)\b\s+\d+\s*=\s*\d+)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript\s*:",
        r"on\w+\s*=\s*['\"]",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e",
        r"%252e%252e",
    ]
    
    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """Check for potential SQL injection. Returns True if suspicious."""
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def check_xss(cls, value: str) -> bool:
        """Check for potential XSS. Returns True if suspicious."""
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def check_path_traversal(cls, value: str) -> bool:
        """Check for path traversal. Returns True if suspicious."""
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def sanitize_html(cls, html: str) -> str:
        """Basic HTML sanitization - strips all tags."""
        return re.sub(r"<[^>]+>", "", html)
    
    @classmethod
    def scan_request(cls, method: str, path: str, headers: dict, 
                     body: str = "") -> List[str]:
        """Scan a request for security issues. Returns list of warnings."""
        warnings = []
        
        if cls.check_path_traversal(path):
            warnings.append("Path traversal detected in URL")
        
        if cls.check_sql_injection(path):
            warnings.append("SQL injection pattern detected in URL")
        
        if body:
            if cls.check_sql_injection(body):
                warnings.append("SQL injection pattern detected in body")
            if cls.check_xss(body):
                warnings.append("XSS pattern detected in body")
        
        return warnings
