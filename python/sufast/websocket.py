"""
Sufast WebSocket Support - Full WebSocket protocol implementation.
Supports both Python asyncio and Rust-accelerated WebSocket handling.
"""

import asyncio
import hashlib
import base64
import struct
import json
import os
from typing import Any, Optional, Callable, Dict, List, Union
from enum import IntEnum


class WebSocketState(IntEnum):
    CONNECTING = 0
    OPEN = 1
    CLOSING = 2
    CLOSED = 3


class WebSocketCloseCode(IntEnum):
    NORMAL = 1000
    GOING_AWAY = 1001
    PROTOCOL_ERROR = 1002
    UNSUPPORTED_DATA = 1003
    NO_STATUS = 1005
    ABNORMAL = 1006
    INVALID_DATA = 1007
    POLICY_VIOLATION = 1008
    MESSAGE_TOO_BIG = 1009
    MANDATORY_EXTENSION = 1010
    INTERNAL_ERROR = 1011
    SERVICE_RESTART = 1012
    TRY_AGAIN_LATER = 1013


class WebSocketMessage:
    """Represents a WebSocket message."""
    
    def __init__(self, type: str, data: Any = None):
        self.type = type  # "text", "bytes", "close", "ping", "pong"
        self.data = data
    
    def __repr__(self):
        return f"WebSocketMessage(type={self.type!r}, data={self.data!r})"


class WebSocket:
    """WebSocket connection handler - FastAPI compatible API.
    
    Usage:
        @app.websocket("/ws")
        async def ws_handler(websocket: WebSocket):
            await websocket.accept()
            while True:
                data = await websocket.receive_text()
                await websocket.send_text(f"Echo: {data}")
    """
    
    GUID = "258EAFA5-E914-47DA-95CA-5AB5DC65C3"
    
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, 
                 path: str = "/", headers: Dict[str, str] = None,
                 query_params: Dict[str, str] = None):
        self.reader = reader
        self.writer = writer
        self.path = path
        self.headers = headers or {}
        self.query_params = query_params or {}
        self.state = WebSocketState.CONNECTING
        self.client_address = None
        self._close_code: Optional[int] = None
        self._close_reason: str = ""
        self._message_handlers: List[Callable] = []
        self._max_message_size = 64 * 1024 * 1024  # 64MB
        
        try:
            peername = writer.get_extra_info('peername')
            if peername:
                self.client_address = f"{peername[0]}:{peername[1]}"
        except Exception:
            pass
    
    @staticmethod
    def compute_accept_key(key: str) -> str:
        """Compute the Sec-WebSocket-Accept value."""
        guid = "258EAFA5-E914-47DA-95CA-5AB5DC65C3"
        sha1 = hashlib.sha1((key + guid).encode()).digest()
        return base64.b64encode(sha1).decode()
    
    async def accept(self, subprotocol: Optional[str] = None, 
                     headers: Optional[Dict[str, str]] = None):
        """Accept the WebSocket connection and send upgrade response."""
        if self.state != WebSocketState.CONNECTING:
            raise RuntimeError("WebSocket is not in CONNECTING state")
        
        ws_key = self.headers.get("sec-websocket-key", "")
        accept_key = self.compute_accept_key(ws_key)
        
        response_lines = [
            "HTTP/1.1 101 Switching Protocols",
            "Upgrade: websocket",
            "Connection: Upgrade",
            f"Sec-WebSocket-Accept: {accept_key}",
        ]
        
        if subprotocol:
            response_lines.append(f"Sec-WebSocket-Protocol: {subprotocol}")
        
        if headers:
            for key, value in headers.items():
                response_lines.append(f"{key}: {value}")
        
        response_lines.append("")
        response_lines.append("")
        
        response = "\r\n".join(response_lines)
        self.writer.write(response.encode())
        await self.writer.drain()
        
        self.state = WebSocketState.OPEN
    
    async def close(self, code: int = WebSocketCloseCode.NORMAL, reason: str = ""):
        """Close the WebSocket connection."""
        if self.state not in (WebSocketState.OPEN, WebSocketState.CLOSING):
            return
        
        self.state = WebSocketState.CLOSING
        self._close_code = code
        self._close_reason = reason
        
        # Send close frame
        payload = struct.pack("!H", code)
        if reason:
            payload += reason.encode("utf-8")
        
        await self._send_frame(0x8, payload)
        self.state = WebSocketState.CLOSED
        
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception:
            pass
    
    async def send_text(self, data: str):
        """Send a text message."""
        if self.state != WebSocketState.OPEN:
            raise RuntimeError("WebSocket is not open")
        await self._send_frame(0x1, data.encode("utf-8"))
    
    async def send_bytes(self, data: bytes):
        """Send a binary message."""
        if self.state != WebSocketState.OPEN:
            raise RuntimeError("WebSocket is not open")
        await self._send_frame(0x2, data)
    
    async def send_json(self, data: Any, mode: str = "text"):
        """Send JSON data."""
        text = json.dumps(data, default=str)
        if mode == "text":
            await self.send_text(text)
        else:
            await self.send_bytes(text.encode("utf-8"))
    
    async def receive(self) -> WebSocketMessage:
        """Receive the next WebSocket message."""
        if self.state != WebSocketState.OPEN:
            raise RuntimeError("WebSocket is not open")
        
        while True:
            opcode, payload = await self._read_frame()
            
            if opcode == 0x1:  # Text
                return WebSocketMessage("text", payload.decode("utf-8"))
            elif opcode == 0x2:  # Binary
                return WebSocketMessage("bytes", payload)
            elif opcode == 0x8:  # Close
                if len(payload) >= 2:
                    code = struct.unpack("!H", payload[:2])[0]
                    reason = payload[2:].decode("utf-8", errors="replace")
                else:
                    code = WebSocketCloseCode.NO_STATUS
                    reason = ""
                self._close_code = code
                self._close_reason = reason
                # Send close frame back
                await self._send_frame(0x8, payload)
                self.state = WebSocketState.CLOSED
                return WebSocketMessage("close", {"code": code, "reason": reason})
            elif opcode == 0x9:  # Ping
                await self._send_frame(0xA, payload)  # Pong
                continue
            elif opcode == 0xA:  # Pong
                continue
            else:
                raise RuntimeError(f"Unknown opcode: {opcode}")
    
    async def receive_text(self) -> str:
        """Receive a text message."""
        msg = await self.receive()
        if msg.type == "close":
            raise RuntimeError(f"WebSocket closed: {msg.data}")
        if msg.type != "text":
            raise RuntimeError(f"Expected text message, got {msg.type}")
        return msg.data
    
    async def receive_bytes(self) -> bytes:
        """Receive a binary message."""
        msg = await self.receive()
        if msg.type == "close":
            raise RuntimeError(f"WebSocket closed: {msg.data}")
        if msg.type != "bytes":
            raise RuntimeError(f"Expected binary message, got {msg.type}")
        return msg.data
    
    async def receive_json(self, mode: str = "text") -> Any:
        """Receive and parse JSON data."""
        if mode == "text":
            text = await self.receive_text()
            return json.loads(text)
        else:
            data = await self.receive_bytes()
            return json.loads(data)
    
    async def iter_text(self):
        """Async iterator for text messages."""
        try:
            while self.state == WebSocketState.OPEN:
                try:
                    yield await self.receive_text()
                except RuntimeError:
                    break
        except Exception:
            pass
    
    async def iter_bytes(self):
        """Async iterator for binary messages."""
        try:
            while self.state == WebSocketState.OPEN:
                try:
                    yield await self.receive_bytes()
                except RuntimeError:
                    break
        except Exception:
            pass
    
    async def iter_json(self):
        """Async iterator for JSON messages."""
        try:
            while self.state == WebSocketState.OPEN:
                try:
                    yield await self.receive_json()
                except RuntimeError:
                    break
        except Exception:
            pass
    
    async def _send_frame(self, opcode: int, payload: bytes):
        """Send a WebSocket frame."""
        header = bytearray()
        header.append(0x80 | opcode)  # FIN + opcode
        
        length = len(payload)
        if length < 126:
            header.append(length)
        elif length < 65536:
            header.append(126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(127)
            header.extend(struct.pack("!Q", length))
        
        self.writer.write(bytes(header) + payload)
        await self.writer.drain()
    
    async def _read_frame(self) -> tuple:
        """Read a WebSocket frame."""
        # Read first 2 bytes
        header = await self.reader.readexactly(2)
        fin = (header[0] >> 7) & 1
        opcode = header[0] & 0x0F
        masked = (header[1] >> 7) & 1
        payload_length = header[1] & 0x7F
        
        # Extended payload length
        if payload_length == 126:
            data = await self.reader.readexactly(2)
            payload_length = struct.unpack("!H", data)[0]
        elif payload_length == 127:
            data = await self.reader.readexactly(8)
            payload_length = struct.unpack("!Q", data)[0]
        
        if payload_length > self._max_message_size:
            raise RuntimeError(f"Message too large: {payload_length}")
        
        # Read mask (if present)
        mask = None
        if masked:
            mask = await self.reader.readexactly(4)
        
        # Read payload
        payload = await self.reader.readexactly(payload_length)
        
        # Unmask payload
        if mask:
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        
        # Handle fragmentation
        if not fin and opcode != 0x0:
            # Start of fragmented message
            fragments = [payload]
            while True:
                next_header = await self.reader.readexactly(2)
                next_fin = (next_header[0] >> 7) & 1
                next_opcode = next_header[0] & 0x0F
                next_masked = (next_header[1] >> 7) & 1
                next_length = next_header[1] & 0x7F
                
                if next_length == 126:
                    data = await self.reader.readexactly(2)
                    next_length = struct.unpack("!H", data)[0]
                elif next_length == 127:
                    data = await self.reader.readexactly(8)
                    next_length = struct.unpack("!Q", data)[0]
                
                next_mask = None
                if next_masked:
                    next_mask = await self.reader.readexactly(4)
                
                fragment = await self.reader.readexactly(next_length)
                if next_mask:
                    fragment = bytes(b ^ next_mask[i % 4] for i, b in enumerate(fragment))
                
                fragments.append(fragment)
                
                if next_fin:
                    break
            
            payload = b"".join(fragments)
        
        return opcode, payload


class WebSocketRoute:
    """Stores a WebSocket route definition."""
    
    def __init__(self, path: str, handler: Callable, name: Optional[str] = None):
        self.path = path
        self.handler = handler
        self.name = name or handler.__name__
        self._path_regex = None
        self._param_names = []
        self._compile_pattern()
    
    def _compile_pattern(self):
        """Compile path pattern for matching."""
        import re
        pattern = self.path
        self._param_names = []
        
        for match in re.finditer(r'\{(\w+)\}', pattern):
            param_name = match.group(1)
            self._param_names.append(param_name)
            pattern = pattern.replace(f'{{{param_name}}}', f'(?P<{param_name}>[^/]+)')
        
        self._path_regex = re.compile(f'^{pattern}$')
    
    def match(self, path: str) -> Optional[Dict[str, str]]:
        """Check if path matches this route."""
        m = self._path_regex.match(path)
        if m:
            return m.groupdict()
        return None


class ConnectionManager:
    """Manages WebSocket connections for broadcasting.
    
    Usage:
        manager = ConnectionManager()
        
        @app.websocket("/ws/{room}")
        async def ws_handler(websocket: WebSocket, room: str):
            await manager.connect(websocket, room)
            try:
                async for message in websocket.iter_text():
                    await manager.broadcast(message, room)
            except:
                manager.disconnect(websocket, room)
    """
    
    def __init__(self):
        self._connections: Dict[str, List[WebSocket]] = {}
        self._all_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket, group: str = "default"):
        """Accept and track a WebSocket connection."""
        await websocket.accept()
        if group not in self._connections:
            self._connections[group] = []
        self._connections[group].append(websocket)
        self._all_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket, group: str = "default"):
        """Remove a WebSocket connection."""
        if group in self._connections:
            self._connections[group] = [
                ws for ws in self._connections[group] if ws != websocket
            ]
            if not self._connections[group]:
                del self._connections[group]
        self._all_connections = [ws for ws in self._all_connections if ws != websocket]
    
    async def send_personal(self, message: str, websocket: WebSocket):
        """Send a message to a specific connection."""
        await websocket.send_text(message)
    
    async def broadcast(self, message: str, group: str = "default", 
                       exclude: Optional[WebSocket] = None):
        """Broadcast a message to all connections in a group."""
        connections = self._connections.get(group, [])
        disconnected = []
        for ws in connections:
            if ws == exclude:
                continue
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.append(ws)
        
        # Clean up disconnected
        for ws in disconnected:
            self.disconnect(ws, group)
    
    async def broadcast_json(self, data: Any, group: str = "default",
                            exclude: Optional[WebSocket] = None):
        """Broadcast JSON data to all connections in a group."""
        message = json.dumps(data, default=str)
        await self.broadcast(message, group, exclude)
    
    async def broadcast_all(self, message: str, exclude: Optional[WebSocket] = None):
        """Broadcast to ALL connections across all groups."""
        disconnected = []
        for ws in self._all_connections:
            if ws == exclude:
                continue
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.append(ws)
        
        for ws in disconnected:
            for group in list(self._connections.keys()):
                self.disconnect(ws, group)
    
    def get_connections(self, group: str = "default") -> List[WebSocket]:
        """Get all connections in a group."""
        return self._connections.get(group, [])
    
    def get_connection_count(self, group: Optional[str] = None) -> int:
        """Get connection count for a group or all groups."""
        if group:
            return len(self._connections.get(group, []))
        return len(self._all_connections)
    
    def get_groups(self) -> List[str]:
        """Get all active groups."""
        return list(self._connections.keys())
