"""
Sufast Structured Logging - Production-grade logging system.
==============================================================
JSON-structured logging with request correlation, log levels,
and configurable output.

Usage:
    from sufast.logging import Logger, get_logger, configure_logging

    logger = get_logger("myapp")
    logger.info("Server started", port=8000)
    logger.error("Query failed", query="SELECT...", error=str(e))
"""

import json
import sys
import time
import threading
import os
import traceback as tb_module
from typing import Any, Callable, Dict, List, Optional, IO
from datetime import datetime, timezone
from enum import IntEnum


class LogLevel(IntEnum):
    """Log levels ordered by severity."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


# String -> LogLevel mapping
LEVEL_NAMES = {
    "debug": LogLevel.DEBUG,
    "info": LogLevel.INFO,
    "warning": LogLevel.WARNING,
    "warn": LogLevel.WARNING,
    "error": LogLevel.ERROR,
    "critical": LogLevel.CRITICAL,
    "fatal": LogLevel.CRITICAL,
}

LEVEL_LABELS = {
    LogLevel.DEBUG: "DEBUG",
    LogLevel.INFO: "INFO",
    LogLevel.WARNING: "WARN",
    LogLevel.ERROR: "ERROR",
    LogLevel.CRITICAL: "CRITICAL",
}

# ANSI colors for terminal output
LEVEL_COLORS = {
    LogLevel.DEBUG: "\033[90m",      # gray
    LogLevel.INFO: "\033[36m",       # cyan
    LogLevel.WARNING: "\033[33m",    # yellow
    LogLevel.ERROR: "\033[31m",      # red
    LogLevel.CRITICAL: "\033[1;31m", # bold red
}
RESET = "\033[0m"


class LogRecord:
    """A single log record."""
    
    __slots__ = ("level", "message", "logger_name", "timestamp", "extra", "exc_info")
    
    def __init__(self, level: LogLevel, message: str, logger_name: str,
                 extra: Dict[str, Any] = None, exc_info: Optional[str] = None):
        self.level = level
        self.message = message
        self.logger_name = logger_name
        self.timestamp = datetime.now(timezone.utc)
        self.extra = extra or {}
        self.exc_info = exc_info


class LogFormatter:
    """Base log formatter."""
    
    def format(self, record: LogRecord) -> str:
        raise NotImplementedError


class JSONFormatter(LogFormatter):
    """JSON-structured log formatter for production."""
    
    def __init__(self, include_timestamp: bool = True, include_logger: bool = True):
        self.include_timestamp = include_timestamp
        self.include_logger = include_logger
    
    def format(self, record: LogRecord) -> str:
        data = {
            "level": LEVEL_LABELS.get(record.level, "UNKNOWN"),
            "message": record.message,
        }
        
        if self.include_timestamp:
            data["timestamp"] = record.timestamp.isoformat()
        
        if self.include_logger:
            data["logger"] = record.logger_name
        
        if record.extra:
            data.update(record.extra)
        
        if record.exc_info:
            data["exception"] = record.exc_info
        
        return json.dumps(data, default=str)


class ConsoleFormatter(LogFormatter):
    """Human-readable console formatter for development."""
    
    def __init__(self, colorize: bool = True, show_timestamp: bool = True):
        self.colorize = colorize and sys.stdout.isatty()
        self.show_timestamp = show_timestamp
    
    def format(self, record: LogRecord) -> str:
        parts = []
        
        if self.show_timestamp:
            ts = record.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            parts.append(f"\033[90m{ts}\033[0m" if self.colorize else ts)
        
        level_label = LEVEL_LABELS.get(record.level, "???").ljust(8)
        if self.colorize:
            color = LEVEL_COLORS.get(record.level, "")
            parts.append(f"{color}{level_label}{RESET}")
        else:
            parts.append(level_label)
        
        if record.logger_name:
            if self.colorize:
                parts.append(f"\033[90m[{record.logger_name}]\033[0m")
            else:
                parts.append(f"[{record.logger_name}]")
        
        parts.append(record.message)
        
        if record.extra:
            extra_str = " ".join(f"{k}={v!r}" for k, v in record.extra.items())
            if self.colorize:
                parts.append(f"\033[90m{extra_str}\033[0m")
            else:
                parts.append(extra_str)
        
        line = " ".join(parts)
        
        if record.exc_info:
            line += f"\n{record.exc_info}"
        
        return line


class LogHandler:
    """Base log handler."""
    
    def __init__(self, formatter: Optional[LogFormatter] = None, level: LogLevel = LogLevel.DEBUG):
        self.formatter = formatter or ConsoleFormatter()
        self.level = level
    
    def emit(self, record: LogRecord):
        raise NotImplementedError
    
    def should_handle(self, record: LogRecord) -> bool:
        return record.level >= self.level


class StreamHandler(LogHandler):
    """Writes logs to a stream (stdout/stderr)."""
    
    def __init__(self, stream: IO = None, **kwargs):
        super().__init__(**kwargs)
        self.stream = stream or sys.stderr
        self._lock = threading.Lock()
    
    def emit(self, record: LogRecord):
        if not self.should_handle(record):
            return
        try:
            msg = self.formatter.format(record)
            with self._lock:
                self.stream.write(msg + "\n")
                self.stream.flush()
        except Exception:
            pass


class FileHandler(LogHandler):
    """Writes logs to a file with optional rotation."""
    
    def __init__(self, filename: str, max_bytes: int = 10 * 1024 * 1024,
                 backup_count: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.filename = filename
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self._lock = threading.Lock()
        self._file: Optional[IO] = None
        self._open_file()
    
    def _open_file(self):
        os.makedirs(os.path.dirname(self.filename) or ".", exist_ok=True)
        self._file = open(self.filename, "a", encoding="utf-8")
    
    def _rotate(self):
        if self._file:
            self._file.close()
        
        # Rotate existing files
        for i in range(self.backup_count - 1, 0, -1):
            src = f"{self.filename}.{i}"
            dst = f"{self.filename}.{i + 1}"
            if os.path.exists(src):
                if os.path.exists(dst):
                    os.remove(dst)
                os.rename(src, dst)
        
        if os.path.exists(self.filename):
            dst = f"{self.filename}.1"
            if os.path.exists(dst):
                os.remove(dst)
            os.rename(self.filename, dst)
        
        self._open_file()
    
    def emit(self, record: LogRecord):
        if not self.should_handle(record):
            return
        try:
            msg = self.formatter.format(record)
            with self._lock:
                if self._file:
                    self._file.write(msg + "\n")
                    self._file.flush()
                    
                    # Check rotation
                    if self.max_bytes > 0 and self._file.tell() >= self.max_bytes:
                        self._rotate()
        except Exception:
            pass
    
    def close(self):
        if self._file:
            self._file.close()
            self._file = None


class Logger:
    """Structured logger with context support.
    
    Usage:
        logger = Logger("myapp")
        logger.info("Request processed", method="GET", path="/api", duration_ms=12.5)
        logger.error("Database error", query="SELECT...", exc_info=True)
    """
    
    def __init__(self, name: str = "", level: LogLevel = LogLevel.DEBUG,
                 handlers: List[LogHandler] = None):
        self.name = name
        self.level = level
        self.handlers: List[LogHandler] = handlers or []
        self._context: Dict[str, Any] = {}
    
    def bind(self, **kwargs) -> 'Logger':
        """Create a new logger with additional context fields."""
        new_logger = Logger(self.name, self.level, self.handlers)
        new_logger._context = {**self._context, **kwargs}
        return new_logger
    
    def _log(self, level: LogLevel, message: str, exc_info: bool = False, **kwargs):
        if level < self.level:
            return
        
        extra = {**self._context, **kwargs}
        
        exc_text = None
        if exc_info:
            exc_text = tb_module.format_exc()
            if exc_text == "NoneType: None\n":
                exc_text = None
        
        record = LogRecord(level, message, self.name, extra, exc_text)
        
        for handler in self.handlers:
            try:
                handler.emit(record)
            except Exception:
                pass
    
    def debug(self, message: str, **kwargs):
        """Log a debug message."""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log an info message."""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log a warning message."""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log an error message."""
        self._log(LogLevel.ERROR, message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc_info: bool = False, **kwargs):
        """Log a critical message."""
        self._log(LogLevel.CRITICAL, message, exc_info=exc_info, **kwargs)


# ======================================================
# Global Logging Configuration
# ======================================================

_loggers: Dict[str, Logger] = {}
_default_handlers: List[LogHandler] = []
_default_level: LogLevel = LogLevel.INFO


def configure_logging(
    level: str = "info",
    format: str = "console",   # "console" or "json"
    log_file: Optional[str] = None,
    colorize: bool = True,
):
    """Configure the global logging system.
    
    Args:
        level: Minimum log level ("debug", "info", "warning", "error", "critical")
        format: Output format ("console" for dev, "json" for production)
        log_file: Optional file path for file logging
        colorize: Whether to use ANSI colors (console format only)
    
    Usage:
        # Development
        configure_logging(level="debug", format="console")
        
        # Production
        configure_logging(level="info", format="json", log_file="logs/app.log")
    """
    global _default_handlers, _default_level
    
    _default_level = LEVEL_NAMES.get(level.lower(), LogLevel.INFO)
    _default_handlers.clear()
    
    if format == "json":
        formatter = JSONFormatter()
    else:
        formatter = ConsoleFormatter(colorize=colorize)
    
    _default_handlers.append(StreamHandler(stream=sys.stderr, formatter=formatter, level=_default_level))
    
    if log_file:
        file_formatter = JSONFormatter()  # Always JSON for files
        _default_handlers.append(FileHandler(log_file, formatter=file_formatter, level=_default_level))
    
    # Update existing loggers
    for logger in _loggers.values():
        logger.handlers = list(_default_handlers)
        logger.level = _default_level


def get_logger(name: str = "sufast") -> Logger:
    """Get or create a named logger.
    
    Usage:
        logger = get_logger("myapp.routes")
        logger.info("Route registered", path="/api/users")
    """
    global _loggers
    
    if name not in _loggers:
        if not _default_handlers:
            # Auto-configure with defaults
            configure_logging()
        
        _loggers[name] = Logger(
            name=name,
            level=_default_level,
            handlers=list(_default_handlers)
        )
    
    return _loggers[name]


# ======================================================
# Request Logging Middleware Helper
# ======================================================

class AccessLogger:
    """Logs HTTP access in structured format.
    
    Usage in middleware:
        access_log = AccessLogger(get_logger("access"))
        
        @app.middleware("http")
        async def log_requests(request, call_next):
            return await access_log.log_request(request, call_next)
    """
    
    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or get_logger("sufast.access")
    
    async def log_request(self, request, call_next):
        """Log an HTTP request/response cycle."""
        start = time.time()
        request_id = request.state.get("request_id", "-") if hasattr(request, "state") else "-"
        
        try:
            response = await call_next(request)
            duration = (time.time() - start) * 1000  # ms
            
            status = response.status if hasattr(response, "status") else 200
            
            self.logger.info(
                f"{request.method} {request.path} {status}",
                method=request.method,
                path=request.path,
                status=status,
                duration_ms=round(duration, 2),
                request_id=request_id,
                client=getattr(request, "remote_addr", "-"),
                user_agent=request.headers.get("user-agent", "-")[:100],
            )
            
            return response
            
        except Exception as e:
            duration = (time.time() - start) * 1000
            self.logger.error(
                f"{request.method} {request.path} 500",
                method=request.method,
                path=request.path,
                status=500,
                duration_ms=round(duration, 2),
                request_id=request_id,
                error=str(e),
                exc_info=True,
            )
            raise
