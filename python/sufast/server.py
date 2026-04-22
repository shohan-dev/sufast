"""
Sufast Pure Python Asyncio HTTP Server - Production-grade fallback server.
Used when Rust core is not available. Supports HTTP/1.1, WebSocket, SSE, TLS.
"""

import asyncio
import contextlib
import json
import ssl
import time
import traceback
import signal
import os
import sys
import secrets
import multiprocessing
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs, unquote
from datetime import datetime, timezone

from .exceptions import HTTPException, STATUS_PHRASES
from .websocket import WebSocket, WebSocketState


def _safe_console_print(message: str) -> None:
    """Print safely on terminals that cannot encode unicode/emoji."""
    try:
        print(message)
    except UnicodeEncodeError:
        out_encoding = sys.stdout.encoding or "utf-8"
        safe_message = message.encode(out_encoding, errors="replace").decode(
            out_encoding, errors="replace"
        )
        print(safe_message)


class HTTPServer:
    """Pure Python asyncio HTTP server with WebSocket, SSE, and TLS support.
    
    Production-grade HTTP/1.1 server features:
    - Keep-alive connections with configurable timeout
    - WebSocket upgrade support
    - Server-Sent Events (SSE) streaming
    - Chunked transfer encoding
    - TLS/SSL encryption
    - Request body size limits
    - Graceful shutdown with connection draining
    - Request ID generation and tracking
    - Static file serving
    """
    
    def __init__(self, app=None, host: str = "127.0.0.1", port: int = 8000,
                 ssl_certfile: Optional[str] = None, ssl_keyfile: Optional[str] = None,
                 max_request_size: int = 10 * 1024 * 1024,  # 10MB
                 keep_alive_timeout: int = 30,
                 request_timeout: int = 60,
                 shutdown_timeout: int = 10):
        self.app = app
        self.host = host
        self.port = port
        self.ssl_certfile = ssl_certfile
        self.ssl_keyfile = ssl_keyfile
        self.max_request_size = max_request_size
        self.keep_alive_timeout = keep_alive_timeout
        self.request_timeout = request_timeout
        self.shutdown_timeout = shutdown_timeout
        self._running = False
        self._server = None
        self._connections: set = set()
        self._request_count = 0
        self._start_time = None
        self._ssl_context: Optional[ssl.SSLContext] = None
        self._shutting_down = False
    
    def _create_ssl_context(self) -> Optional[ssl.SSLContext]:
        """Create SSL context for HTTPS."""
        if not self.ssl_certfile:
            return None
        
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.set_ciphers(
            "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20"
            ":ECDH+AESGCM:DH+AESGCM:ECDH+AES:DH+AES"
            ":!aNULL:!MD5:!DSS:!RC4"
        )
        ctx.load_cert_chain(self.ssl_certfile, self.ssl_keyfile)
        return ctx
    
    async def start(self):
        """Start the HTTP server."""
        self._running = True
        self._start_time = time.time()
        
        self._ssl_context = self._create_ssl_context()
        scheme = "https" if self._ssl_context else "http"
        
        self._server = await asyncio.start_server(
            self._handle_connection,
            self.host,
            self.port,
            reuse_address=True,
            ssl=self._ssl_context,
        )
        
        addr = self._server.sockets[0].getsockname()
        _safe_console_print(
            f"\n  \033[1;36m⚡ Sufast\033[0m running on \033[1m{scheme}://{addr[0]}:{addr[1]}\033[0m"
        )
        if self._ssl_context:
            _safe_console_print(f"  \033[1;32m🔒 TLS enabled\033[0m")
        _safe_console_print(
            f"  \033[90mPython asyncio server (install Rust core for 10x speed)\033[0m"
        )
        if self.app and self.app.docs_url:
            _safe_console_print(
                f"  \033[90m📖 Docs:\033[0m \033[4m{scheme}://{addr[0]}:{addr[1]}{self.app.docs_url}\033[0m"
            )
        _safe_console_print(f"  \033[90mPress Ctrl+C to stop\033[0m\n")
        
        async with self._server:
            await self._server.serve_forever()
    
    async def stop(self):
        """Graceful shutdown: stop accepting, drain connections, then close."""
        self._shutting_down = True
        self._running = False
        
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        
        # Graceful drain: wait for active connections to finish
        if self._connections:
            print(f"  \033[90mDraining {len(self._connections)} active connections...\033[0m")
            deadline = time.time() + self.shutdown_timeout
            while self._connections and time.time() < deadline:
                await asyncio.sleep(0.1)
        
        # Force-close remaining connections
        for writer in list(self._connections):
            try:
                writer.close()
            except Exception:
                pass
        self._connections.clear()
    
    async def _handle_connection(self, reader: asyncio.StreamReader, 
                                  writer: asyncio.StreamWriter):
        """Handle a single client connection with keep-alive support."""
        self._connections.add(writer)
        peer = writer.get_extra_info('peername')
        
        try:
            while self._running:
                try:
                    # Read request with timeout
                    request_data = await asyncio.wait_for(
                        self._read_request(reader), 
                        timeout=self.keep_alive_timeout
                    )
                    
                    if request_data is None:
                        break  # Connection closed
                    
                    self._request_count += 1
                    
                    method, path, version, headers, body = request_data
                    
                    # Check for WebSocket upgrade
                    if (headers.get("upgrade", "").lower() == "websocket" and 
                        "sec-websocket-key" in headers):
                        await self._handle_websocket_upgrade(
                            reader, writer, method, path, headers
                        )
                        return  # WebSocket takes over the connection
                    
                    # Process HTTP request
                    response = await asyncio.wait_for(
                        self._process_request(method, path, version, headers, body, peer),
                        timeout=self.request_timeout
                    )
                    
                    # Check for SSE response
                    if "_sse_generator" in response:
                        await self._handle_sse_response(writer, response, version)
                        return  # SSE keeps connection open
                    
                    # Send response
                    await self._send_response(writer, response, version)
                    
                    # Check keep-alive
                    connection = headers.get("connection", "").lower()
                    if version == "HTTP/1.0" and connection != "keep-alive":
                        break
                    if connection == "close":
                        break
                    
                    # Stop keep-alive during shutdown
                    if self._shutting_down:
                        break
                        
                except asyncio.TimeoutError:
                    break  # Idle timeout
                except asyncio.IncompleteReadError:
                    break
                except ConnectionResetError:
                    break
                except Exception as e:
                    # Send 500 error
                    try:
                        debug = getattr(self.app, 'debug', False) if self.app else False
                        if debug:
                            msg = str(e)
                        else:
                            msg = "Internal Server Error"
                        error_response = self._make_error_response(500, msg)
                        await self._send_response(writer, error_response, "HTTP/1.1")
                    except Exception:
                        pass
                    break
        except Exception:
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            self._connections.discard(writer)
    
    async def _read_request(self, reader: asyncio.StreamReader) -> Optional[tuple]:
        """Read and parse an HTTP request."""
        # Read request line
        try:
            request_line = await reader.readline()
        except Exception:
            return None
            
        if not request_line:
            return None
        
        request_line = request_line.decode("utf-8", errors="replace").strip()
        if not request_line:
            return None
        
        parts = request_line.split(" ", 2)
        if len(parts) < 2:
            return None
        
        method = parts[0].upper()
        raw_path = parts[1]
        version = parts[2] if len(parts) > 2 else "HTTP/1.1"
        
        # Read headers
        headers = {}
        header_size = 0
        while True:
            line = await reader.readline()
            if not line or line == b"\r\n" or line == b"\n":
                break
            header_size += len(line)
            if header_size > 32768:  # 32KB header limit
                return None
            line = line.decode("utf-8", errors="replace").strip()
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip()
        
        # Read body if Content-Length present
        body = b""
        content_length = int(headers.get("content-length", "0"))
        
        # Enforce body size limit
        if content_length > self.max_request_size:
            return method, raw_path, version, headers, b"__TOO_LARGE__"
        
        if content_length > 0:
            body = await reader.readexactly(content_length)
        elif headers.get("transfer-encoding", "").lower() == "chunked":
            body = await self._read_chunked_body(reader)
            if len(body) > self.max_request_size:
                return method, raw_path, version, headers, b"__TOO_LARGE__"
        
        return method, raw_path, version, headers, body
    
    async def _read_chunked_body(self, reader: asyncio.StreamReader) -> bytes:
        """Read chunked transfer-encoding body."""
        body = bytearray()
        while True:
            line = await reader.readline()
            try:
                chunk_size = int(line.strip(), 16)
            except ValueError:
                break
            if chunk_size == 0:
                await reader.readline()  # trailing CRLF
                break
            if len(body) + chunk_size > self.max_request_size:
                # Skip the rest
                await reader.readexactly(chunk_size)
                await reader.readline()
                return b"__TOO_LARGE__"
            chunk = await reader.readexactly(chunk_size)
            body.extend(chunk)
            await reader.readline()  # trailing CRLF
        return bytes(body)
    
    async def _process_request(self, method: str, raw_path: str, version: str,
                                headers: dict, body: bytes, peer) -> dict:
        """Process an HTTP request through the app."""
        # Check for oversized body
        if body == b"__TOO_LARGE__":
            return {
                "status": 413,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"detail": "Request entity too large", 
                                    "max_size": self.max_request_size})
            }
        
        # Parse URL
        parsed = urlparse(raw_path)
        path = unquote(parsed.path)
        query_string = parsed.query
        
        if self.app:
            try:
                response = await self.app._handle_request(
                    method=method,
                    path=path,
                    headers=headers,
                    body=body,
                    query_string=query_string,
                    client_addr=peer
                )
                return response
            except HTTPException as e:
                return {
                    "status": e.status_code,
                    "headers": {
                        "content-type": "application/json",
                        **e.headers
                    },
                    "body": json.dumps({"detail": e.detail}, default=str)
                }
            except Exception as e:
                debug = getattr(self.app, 'debug', False)
                if debug:
                    traceback.print_exc()
                    msg = str(e)
                else:
                    msg = "Internal Server Error"
                return self._make_error_response(500, msg)
        
        return self._make_error_response(404, "No application configured")
    
    async def _handle_websocket_upgrade(self, reader, writer, method, path, headers):
        """Handle WebSocket upgrade request."""
        parsed = urlparse(path)
        ws_path = unquote(parsed.path)
        query_string = parsed.query
        query_params = {}
        if query_string:
            qs = parse_qs(query_string)
            query_params = {k: v[0] for k, v in qs.items()}
        
        ws = WebSocket(reader, writer, ws_path, headers, query_params)
        
        if self.app:
            try:
                await self.app._handle_websocket(ws, ws_path)
            except Exception as e:
                try:
                    await ws.close(1011, str(e))
                except Exception:
                    pass
        else:
            # No app - reject
            response = "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"
            writer.write(response.encode())
            await writer.drain()
    
    async def _handle_sse_response(self, writer: asyncio.StreamWriter, 
                                    response: dict, version: str):
        """Handle Server-Sent Events streaming response."""
        status = response.get("status", 200)
        headers = response.get("headers", {})
        generator = response.get("_sse_generator")
        ping_interval = response.get("_sse_ping_interval", 15)
        
        # Send SSE headers
        status_phrase = STATUS_PHRASES.get(status, "OK")
        lines = [f"{version} {status} {status_phrase}"]
        headers["Cache-Control"] = "no-cache"
        headers["Connection"] = "keep-alive"
        headers["Server"] = "Sufast/3.0"
        headers["Date"] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        for key, value in headers.items():
            lines.append(f"{key}: {value}")
        lines.append("")
        lines.append("")
        
        header_bytes = "\r\n".join(lines).encode("utf-8")
        writer.write(header_bytes)
        await writer.drain()
        
        # Stream events
        try:
            from .sse import SSEEvent
            async for event_data in generator:
                if isinstance(event_data, dict):
                    event = SSEEvent(
                        data=event_data.get("data", ""),
                        event=event_data.get("event"),
                        id=event_data.get("id"),
                        retry=event_data.get("retry"),
                        comment=event_data.get("comment"),
                    )
                    chunk = event.encode()
                else:
                    chunk = f"data: {event_data}\n\n"
                
                writer.write(chunk.encode("utf-8"))
                await writer.drain()
        except (ConnectionResetError, BrokenPipeError, asyncio.CancelledError):
            pass
        except Exception:
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
    
    async def _send_response(self, writer: asyncio.StreamWriter, response: dict,
                              version: str = "HTTP/1.1"):
        """Send an HTTP response."""
        status = response.get("status", 200)
        headers = response.get("headers", {})
        body = response.get("body", "")
        
        # Encode body
        if isinstance(body, str):
            body_bytes = body.encode("utf-8")
        elif isinstance(body, bytes):
            body_bytes = body
        else:
            body_bytes = json.dumps(body, default=str).encode("utf-8")
        
        # Build response
        status_phrase = STATUS_PHRASES.get(status, "Unknown")
        lines = [f"{version} {status} {status_phrase}"]
        
        # Set content-length
        if "content-length" not in {k.lower() for k in headers}:
            headers["Content-Length"] = str(len(body_bytes))
        
        # Default headers
        if "server" not in {k.lower() for k in headers}:
            headers["Server"] = "Sufast/3.0"
        if "date" not in {k.lower() for k in headers}:
            headers["Date"] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        for key, value in headers.items():
            if isinstance(value, list):
                for v in value:
                    lines.append(f"{key}: {v}")
            else:
                lines.append(f"{key}: {value}")
        
        lines.append("")
        lines.append("")
        
        header_bytes = "\r\n".join(lines).encode("utf-8")
        
        writer.write(header_bytes + body_bytes)
        await writer.drain()
    
    def _make_error_response(self, status: int, message: str) -> dict:
        """Create an error response dict."""
        return {
            "status": status,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "detail": message,
                "status_code": status
            })
        }
    
    @property
    def stats(self) -> dict:
        """Get server statistics."""
        uptime = time.time() - self._start_time if self._start_time else 0
        return {
            "requests": self._request_count,
            "active_connections": len(self._connections),
            "uptime_seconds": round(uptime, 1),
            "tls_enabled": self._ssl_context is not None,
        }


def run_server(app, host: str = "127.0.0.1", port: int = 8000,
               ssl_certfile: str = None, ssl_keyfile: str = None,
               workers: int = 1):
    """Run the Python asyncio HTTP server.
    
    This is the main entry point for the fallback Python server.
    Supports multi-worker mode via process forking (Unix) or spawning (Windows).
    
    Args:
        app: Sufast application instance
        host: Bind address
        port: Bind port
        ssl_certfile: Path to SSL certificate file
        ssl_keyfile: Path to SSL private key file
        workers: Number of worker processes (1 = single process)
    """
    if workers > 1:
        _run_multiprocess(app, host, port, ssl_certfile, ssl_keyfile, workers)
    else:
        _run_single(app, host, port, ssl_certfile, ssl_keyfile)


def _run_single(app, host, port, ssl_certfile=None, ssl_keyfile=None):
    """Run server in a single process."""
    server = HTTPServer(
        app, host, port,
        ssl_certfile=ssl_certfile,
        ssl_keyfile=ssl_keyfile,
    )
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Setup signal handlers for graceful shutdown
    shutdown_event = asyncio.Event()
    shutdown_requested = False
    
    def signal_handler():
        nonlocal shutdown_requested
        if shutdown_requested:
            return
        shutdown_requested = True
        _safe_console_print("\n\033[90m  Graceful shutdown initiated...\033[0m")
        try:
            if loop.is_running():
                loop.call_soon_threadsafe(shutdown_event.set)
            else:
                shutdown_event.set()
        except RuntimeError:
            pass
    
    try:
        # Use signal handlers if on main thread
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, signal_handler)
            except (NotImplementedError, RuntimeError):
                # Windows doesn't support add_signal_handler on event loop
                signal.signal(sig, lambda s, f: signal_handler())
    except Exception:
        pass
    
    async def _serve_until_shutdown():
        server_task = asyncio.create_task(server.start())
        try:
            await shutdown_event.wait()
        finally:
            await server.stop()
            if not server_task.done():
                server_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await server_task

    try:
        loop.run_until_complete(_serve_until_shutdown())
    except KeyboardInterrupt:
        signal_handler()
        loop.run_until_complete(server.stop())
    finally:
        loop.close()


def _run_multiprocess(app, host, port, ssl_certfile, ssl_keyfile, workers):
    """Run server with multiple worker processes."""
    _safe_console_print(f"\n  \033[1;36m⚡ Sufast\033[0m starting {workers} workers...")
    
    processes = []
    
    def spawn_worker(worker_id):
        """Worker process main function."""
        _run_single(app, host, port, ssl_certfile, ssl_keyfile)
    
    try:
        for i in range(workers):
            p = multiprocessing.Process(target=spawn_worker, args=(i,), daemon=True)
            p.start()
            processes.append(p)
        
        # Wait for signal
        try:
            for p in processes:
                p.join()
        except KeyboardInterrupt:
            print("\n\033[90m  Stopping workers...\033[0m")
    finally:
        for p in processes:
            if p.is_alive():
                p.terminate()
        for p in processes:
            p.join(timeout=5)
