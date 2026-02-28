"""
Socket.IO protocol support for Sufast.
=======================================
Implements Socket.IO v4 protocol on top of WebSocket transport.

Socket.IO adds namespaces, rooms, acknowledgements, and automatic
reconnection on top of the raw WebSocket protocol.

Usage:
    from sufast import Sufast
    from sufast.socketio_support import SocketIOManager
    
    app = Sufast()
    sio = SocketIOManager(app)
    
    @sio.on("connect")
    async def on_connect(sid, environ):
        print(f"Client {sid} connected")
    
    @sio.on("message")
    async def on_message(sid, data):
        await sio.emit("response", {"echo": data}, to=sid)
    
    @sio.on("disconnect")
    async def on_disconnect(sid):
        print(f"Client {sid} disconnected")
"""

import asyncio
import json
import uuid
import time
from typing import Any, Callable, Dict, List, Optional, Set
from .websocket import WebSocket, WebSocketState


# Engine.IO packet types
class EnginePacket:
    OPEN = "0"
    CLOSE = "1"
    PING = "2"
    PONG = "3"
    MESSAGE = "4"
    UPGRADE = "5"
    NOOP = "6"


# Socket.IO packet types
class SIOPacket:
    CONNECT = 0
    DISCONNECT = 1
    EVENT = 2
    ACK = 3
    CONNECT_ERROR = 4
    BINARY_EVENT = 5
    BINARY_ACK = 6


class SocketIOSession:
    """Represents a connected Socket.IO client session."""
    
    def __init__(self, sid: str, websocket: WebSocket, namespace: str = "/"):
        self.sid = sid
        self.websocket = websocket
        self.namespace = namespace
        self.connected = True
        self.rooms: Set[str] = {sid}  # Every client is in its own room
        self.data: Dict[str, Any] = {}
        self.connected_at = time.time()
        self._ack_counter = 0
        self._ack_callbacks: Dict[int, asyncio.Future] = {}
    
    async def emit(self, event: str, data: Any = None, callback: Callable = None):
        """Emit an event to this specific client."""
        ack_id = None
        if callback:
            self._ack_counter += 1
            ack_id = self._ack_counter
            future = asyncio.get_event_loop().create_future()
            self._ack_callbacks[ack_id] = future
        
        payload = [event]
        if data is not None:
            payload.append(data)
        
        ns_prefix = "" if self.namespace == "/" else self.namespace
        
        if ack_id is not None:
            packet = f"{SIOPacket.EVENT}{ns_prefix},{ack_id}{json.dumps(payload)}"
        else:
            if ns_prefix:
                packet = f"{SIOPacket.EVENT}{ns_prefix},{json.dumps(payload)}"
            else:
                packet = f"{SIOPacket.EVENT}{json.dumps(payload)}"
        
        eio_packet = f"{EnginePacket.MESSAGE}{packet}"
        
        if self.websocket.state == WebSocketState.OPEN:
            await self.websocket.send_text(eio_packet)
    
    async def disconnect(self):
        """Disconnect this client."""
        self.connected = False
        ns_prefix = "" if self.namespace == "/" else self.namespace
        packet = f"{SIOPacket.DISCONNECT}{ns_prefix},"
        eio_packet = f"{EnginePacket.MESSAGE}{packet}"
        
        try:
            if self.websocket.state == WebSocketState.OPEN:
                await self.websocket.send_text(eio_packet)
        except Exception:
            pass
    
    def join(self, room: str):
        """Join a room."""
        self.rooms.add(room)
    
    def leave(self, room: str):
        """Leave a room."""
        self.rooms.discard(room)


class SocketIONamespace:
    """A namespace for Socket.IO events."""
    
    def __init__(self, namespace: str = "/"):
        self.namespace = namespace
        self._handlers: Dict[str, List[Callable]] = {}
    
    def on(self, event: str):
        """Decorator to register an event handler."""
        def decorator(func):
            if event not in self._handlers:
                self._handlers[event] = []
            self._handlers[event].append(func)
            return func
        return decorator
    
    async def trigger(self, event: str, *args):
        """Trigger an event."""
        handlers = self._handlers.get(event, [])
        for handler in handlers:
            if asyncio.iscoroutinefunction(handler):
                await handler(*args)
            else:
                handler(*args)


class SocketIOManager:
    """Socket.IO server manager.
    
    Implements Socket.IO v4 protocol over WebSocket transport.
    Provides namespaces, rooms, broadcasting, and acknowledgements.
    
    Args:
        app: Sufast application instance
        path: Socket.IO endpoint path (default: "/socket.io")
        cors_allowed_origins: List of allowed CORS origins
        ping_interval: Seconds between server pings
        ping_timeout: Seconds to wait for pong
    """
    
    def __init__(
        self,
        app=None,
        path: str = "/socket.io",
        cors_allowed_origins: List[str] = None,
        ping_interval: int = 25,
        ping_timeout: int = 20,
        max_buffer_size: int = 1_000_000,
    ):
        self.path = path.rstrip("/")
        self.cors_allowed_origins = cors_allowed_origins or ["*"]
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.max_buffer_size = max_buffer_size
        
        # Session storage
        self._sessions: Dict[str, SocketIOSession] = {}
        self._namespaces: Dict[str, SocketIONamespace] = {"/": SocketIONamespace("/")}
        self._rooms: Dict[str, Set[str]] = {}  # room_name -> set of sids
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Attach Socket.IO to a Sufast application."""
        self.app = app
        
        manager = self
        
        # Register WebSocket handler
        @app.websocket(f"{self.path}/")
        async def socketio_handler(websocket: WebSocket):
            await manager._handle_connection(websocket)
        
        # Also handle without trailing slash
        @app.websocket(self.path)
        async def socketio_handler_noslash(websocket: WebSocket):
            await manager._handle_connection(websocket)
        
        # Register polling fallback endpoint
        @app.get(f"{self.path}/", tags=["Socket.IO"], 
                summary="Socket.IO polling transport")
        async def socketio_polling(request=None):
            """Socket.IO long-polling transport endpoint."""
            sid = str(uuid.uuid4()).replace("-", "")[:20]
            handshake = {
                "sid": sid,
                "upgrades": ["websocket"],
                "pingInterval": self.ping_interval * 1000,
                "pingTimeout": self.ping_timeout * 1000,
                "maxPayload": self.max_buffer_size,
            }
            return f"{EnginePacket.OPEN}{json.dumps(handshake)}"
    
    def namespace(self, ns: str = "/") -> SocketIONamespace:
        """Get or create a namespace."""
        if ns not in self._namespaces:
            self._namespaces[ns] = SocketIONamespace(ns)
        return self._namespaces[ns]
    
    def on(self, event: str, namespace: str = "/"):
        """Decorator to register an event handler on the default namespace.
        
        Usage:
            @sio.on("message")
            async def on_message(sid, data):
                await sio.emit("response", data, to=sid)
        """
        ns = self.namespace(namespace)
        return ns.on(event)
    
    async def emit(self, event: str, data: Any = None, to: str = None,
                   room: str = None, namespace: str = "/", skip_sid: str = None):
        """Emit an event to client(s).
        
        Args:
            event: Event name
            data: Event data
            to: Specific session ID to send to
            room: Room to broadcast to
            namespace: Namespace
            skip_sid: Session ID to skip (for broadcasting)
        """
        if to:
            session = self._sessions.get(to)
            if session and session.connected and session.namespace == namespace:
                await session.emit(event, data)
            return
        
        if room:
            sids = self._rooms.get(room, set())
            for sid in sids:
                if sid == skip_sid:
                    continue
                session = self._sessions.get(sid)
                if session and session.connected and session.namespace == namespace:
                    await session.emit(event, data)
            return
        
        # Broadcast to all in namespace
        for sid, session in self._sessions.items():
            if sid == skip_sid:
                continue
            if session.connected and session.namespace == namespace:
                await session.emit(event, data)
    
    async def send(self, data: Any, to: str = None, room: str = None,
                   namespace: str = "/"):
        """Send a 'message' event."""
        await self.emit("message", data, to=to, room=room, namespace=namespace)
    
    async def enter_room(self, sid: str, room: str):
        """Add a client to a room."""
        session = self._sessions.get(sid)
        if session:
            session.join(room)
            if room not in self._rooms:
                self._rooms[room] = set()
            self._rooms[room].add(sid)
    
    async def leave_room(self, sid: str, room: str):
        """Remove a client from a room."""
        session = self._sessions.get(sid)
        if session:
            session.leave(room)
        if room in self._rooms:
            self._rooms[room].discard(sid)
            if not self._rooms[room]:
                del self._rooms[room]
    
    def rooms(self, sid: str) -> Set[str]:
        """Get rooms for a client."""
        session = self._sessions.get(sid)
        return session.rooms if session else set()
    
    def get_session(self, sid: str) -> Optional[SocketIOSession]:
        """Get a client session."""
        return self._sessions.get(sid)
    
    @property
    def connected_clients(self) -> int:
        """Number of connected clients."""
        return sum(1 for s in self._sessions.values() if s.connected)
    
    async def disconnect(self, sid: str, namespace: str = "/"):
        """Disconnect a specific client."""
        session = self._sessions.get(sid)
        if session:
            await session.disconnect()
            await self._cleanup_session(sid)
    
    async def _handle_connection(self, websocket: WebSocket):
        """Handle a new Socket.IO WebSocket connection."""
        await websocket.accept()
        
        # Generate session ID
        sid = str(uuid.uuid4()).replace("-", "")[:20]
        
        # Send Engine.IO OPEN packet
        handshake = {
            "sid": sid,
            "upgrades": [],
            "pingInterval": self.ping_interval * 1000,
            "pingTimeout": self.ping_timeout * 1000,
            "maxPayload": self.max_buffer_size,
        }
        await websocket.send_text(f"{EnginePacket.OPEN}{json.dumps(handshake)}")
        
        session = SocketIOSession(sid, websocket)
        self._sessions[sid] = session
        
        # Start ping loop
        ping_task = asyncio.create_task(self._ping_loop(session))
        
        try:
            # Wait for Socket.IO CONNECT packet
            while session.connected:
                try:
                    message = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=self.ping_interval + self.ping_timeout
                    )
                except asyncio.TimeoutError:
                    break
                except Exception:
                    break
                
                if not message:
                    break
                
                await self._handle_packet(session, message)
        except Exception:
            pass
        finally:
            ping_task.cancel()
            try:
                await ping_task
            except (asyncio.CancelledError, Exception):
                pass
            await self._cleanup_session(sid)
    
    async def _handle_packet(self, session: SocketIOSession, raw_message: str):
        """Parse and handle an Engine.IO/Socket.IO packet."""
        if not raw_message:
            return
        
        eio_type = raw_message[0]
        
        if eio_type == EnginePacket.PING:
            # Respond with PONG
            await session.websocket.send_text(EnginePacket.PONG)
            return
        
        if eio_type == EnginePacket.PONG:
            # Client responded to our ping
            return
        
        if eio_type == EnginePacket.CLOSE:
            session.connected = False
            return
        
        if eio_type == EnginePacket.MESSAGE:
            # Socket.IO packet
            sio_data = raw_message[1:]
            if not sio_data:
                return
            
            sio_type = int(sio_data[0])
            sio_payload = sio_data[1:]
            
            await self._handle_sio_packet(session, sio_type, sio_payload)
    
    async def _handle_sio_packet(self, session: SocketIOSession, 
                                  packet_type: int, payload: str):
        """Handle a Socket.IO packet."""
        # Parse namespace
        namespace = "/"
        rest = payload
        
        if rest and rest[0] == '/':
            # Has namespace
            comma_idx = rest.find(',')
            if comma_idx >= 0:
                namespace = rest[:comma_idx]
                rest = rest[comma_idx + 1:]
            else:
                namespace = rest
                rest = ""
        elif rest and rest[0] == ',':
            rest = rest[1:]
        
        if packet_type == SIOPacket.CONNECT:
            # Client connecting to namespace
            session.namespace = namespace
            
            ns = self.namespace(namespace)
            
            # Send CONNECT acknowledgment
            ack = {"sid": session.sid}
            ns_prefix = "" if namespace == "/" else namespace
            if ns_prefix:
                await session.websocket.send_text(
                    f"{EnginePacket.MESSAGE}{SIOPacket.CONNECT}{ns_prefix},{json.dumps(ack)}"
                )
            else:
                await session.websocket.send_text(
                    f"{EnginePacket.MESSAGE}{SIOPacket.CONNECT}{json.dumps(ack)}"
                )
            
            # Trigger connect event
            await ns.trigger("connect", session.sid, {})
        
        elif packet_type == SIOPacket.DISCONNECT:
            ns = self.namespace(namespace)
            await ns.trigger("disconnect", session.sid)
            session.connected = False
        
        elif packet_type == SIOPacket.EVENT:
            # Parse ack ID if present
            ack_id = None
            data_str = rest
            
            # Check for ack id (digits before the JSON array)
            match_digits = ""
            idx = 0
            while idx < len(data_str) and data_str[idx].isdigit():
                match_digits += data_str[idx]
                idx += 1
            
            if match_digits and idx < len(data_str) and data_str[idx] == '[':
                ack_id = int(match_digits)
                data_str = data_str[idx:]
            
            try:
                event_data = json.loads(data_str) if data_str else []
            except json.JSONDecodeError:
                return
            
            if isinstance(event_data, list) and len(event_data) >= 1:
                event_name = event_data[0]
                args = event_data[1:] if len(event_data) > 1 else []
                
                ns = self.namespace(namespace)
                
                # If ack requested, collect return value
                if ack_id is not None:
                    result = None
                    handlers = ns._handlers.get(event_name, [])
                    for handler in handlers:
                        if asyncio.iscoroutinefunction(handler):
                            result = await handler(session.sid, *args)
                        else:
                            result = handler(session.sid, *args)
                    
                    # Send ack
                    ack_data = [result] if result is not None else []
                    ns_prefix = "" if namespace == "/" else namespace
                    if ns_prefix:
                        ack_packet = f"{EnginePacket.MESSAGE}{SIOPacket.ACK}{ns_prefix},{ack_id}{json.dumps(ack_data)}"
                    else:
                        ack_packet = f"{EnginePacket.MESSAGE}{SIOPacket.ACK}{ack_id}{json.dumps(ack_data)}"
                    await session.websocket.send_text(ack_packet)
                else:
                    await ns.trigger(event_name, session.sid, *args)
        
        elif packet_type == SIOPacket.ACK:
            # Handle acknowledgement from client
            ack_id_str = ""
            idx = 0
            while idx < len(rest) and rest[idx].isdigit():
                ack_id_str += rest[idx]
                idx += 1
            
            if ack_id_str:
                ack_id = int(ack_id_str)
                try:
                    ack_data = json.loads(rest[idx:]) if rest[idx:] else []
                except json.JSONDecodeError:
                    ack_data = []
                
                future = session._ack_callbacks.pop(ack_id, None)
                if future and not future.done():
                    future.set_result(ack_data)
    
    async def _ping_loop(self, session: SocketIOSession):
        """Periodically ping the client."""
        try:
            while session.connected:
                await asyncio.sleep(self.ping_interval)
                if session.connected and session.websocket.state == WebSocketState.OPEN:
                    try:
                        await session.websocket.send_text(EnginePacket.PING)
                    except Exception:
                        session.connected = False
                        break
        except asyncio.CancelledError:
            pass
    
    async def _cleanup_session(self, sid: str):
        """Clean up a disconnected session."""
        session = self._sessions.pop(sid, None)
        if session:
            session.connected = False
            
            # Remove from all rooms
            for room_name in list(session.rooms):
                if room_name in self._rooms:
                    self._rooms[room_name].discard(sid)
                    if not self._rooms[room_name]:
                        del self._rooms[room_name]
            
            # Trigger disconnect
            ns = self.namespace(session.namespace)
            await ns.trigger("disconnect", sid)
            
            # Close WebSocket
            try:
                if session.websocket.state == WebSocketState.OPEN:
                    await session.websocket.close()
            except Exception:
                pass
