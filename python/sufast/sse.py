"""
Sufast Server-Sent Events (SSE) - Real-time streaming support.
================================================================
Push real-time updates to clients over HTTP using the SSE protocol.

Usage:
    from sufast.sse import EventSource, SSEResponse

    @app.get("/events")
    async def stream_events(request: Request):
        async def event_generator():
            for i in range(10):
                yield {"event": "update", "data": {"count": i}}
                await asyncio.sleep(1)

        return SSEResponse(event_generator())
"""

import asyncio
import json
import time
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Union


class SSEEvent:
    """A single Server-Sent Event.
    
    Attributes:
        data: Event data (string or dict)
        event: Event type/name
        id: Event ID for client reconnection
        retry: Reconnection delay in milliseconds
        comment: SSE comment line
    """
    
    def __init__(
        self,
        data: Any = "",
        event: Optional[str] = None,
        id: Optional[str] = None,
        retry: Optional[int] = None,
        comment: Optional[str] = None,
    ):
        self.data = data
        self.event = event
        self.id = id
        self.retry = retry
        self.comment = comment
    
    def encode(self) -> str:
        """Encode as SSE wire format."""
        lines = []
        
        if self.comment is not None:
            for line in str(self.comment).split("\n"):
                lines.append(f": {line}")
        
        if self.id is not None:
            lines.append(f"id: {self.id}")
        
        if self.event is not None:
            lines.append(f"event: {self.event}")
        
        if self.retry is not None:
            lines.append(f"retry: {self.retry}")
        
        if self.data is not None:
            if isinstance(self.data, (dict, list)):
                data_str = json.dumps(self.data, default=str)
            else:
                data_str = str(self.data)
            
            for line in data_str.split("\n"):
                lines.append(f"data: {line}")
        
        return "\n".join(lines) + "\n\n"


class SSEResponse:
    """Server-Sent Events response that streams events to the client.
    
    Works as a special response type that the server handles by
    keeping the connection open and streaming events.
    
    Usage:
        @app.get("/stream")
        async def stream(request: Request):
            async def generate():
                for i in range(100):
                    yield {"event": "tick", "data": {"n": i}}
                    await asyncio.sleep(0.1)
            
            return SSEResponse(generate())
    """
    
    def __init__(
        self,
        generator: AsyncIterator,
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
        ping_interval: int = 15,
    ):
        self.generator = generator
        self.status = status
        self.headers = headers or {}
        self.ping_interval = ping_interval
        
        # SSE-required headers
        self.headers.update({
            "content-type": "text/event-stream",
            "cache-control": "no-cache",
            "connection": "keep-alive",
            "x-accel-buffering": "no",  # Disable nginx buffering
        })
    
    def to_dict(self) -> dict:
        """Convert to response dict. The server will detect SSEResponse and handle streaming."""
        return {
            "status": self.status,
            "headers": self.headers,
            "body": "",
            "_sse_generator": self.generator,
            "_sse_ping_interval": self.ping_interval,
        }


class EventSource:
    """Server-side event source for broadcasting events to multiple clients.
    
    Usage:
        events = EventSource()
        
        @app.get("/stream")
        async def stream(request: Request):
            return SSEResponse(events.subscribe())
        
        # From anywhere in your code:
        await events.publish({"type": "update", "data": "new data"})
    """
    
    def __init__(self, max_history: int = 100):
        self._subscribers: List[asyncio.Queue] = []
        self._history: List[SSEEvent] = []
        self._max_history = max_history
        self._event_id = 0
        self._lock = asyncio.Lock()
    
    async def subscribe(self, last_event_id: Optional[str] = None) -> AsyncIterator[dict]:
        """Subscribe to events. Returns an async iterator for SSEResponse.
        
        Args:
            last_event_id: Resume from this event ID (for reconnection)
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=256)
        
        async with self._lock:
            self._subscribers.append(queue)
        
        try:
            # Send missed events if reconnecting
            if last_event_id is not None:
                try:
                    start_id = int(last_event_id) + 1
                    for event in self._history:
                        if event.id is not None and int(event.id) >= start_id:
                            yield {
                                "event": event.event,
                                "data": event.data,
                                "id": event.id,
                            }
                except (ValueError, TypeError):
                    pass
            
            # Stream new events
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    yield event
                except asyncio.TimeoutError:
                    # Send keepalive comment
                    yield {"comment": "keepalive"}
                    
        except asyncio.CancelledError:
            pass
        finally:
            async with self._lock:
                try:
                    self._subscribers.remove(queue)
                except ValueError:
                    pass
    
    async def publish(
        self,
        data: Any = "",
        event: Optional[str] = None,
        id: Optional[str] = None,
    ):
        """Publish an event to all subscribers.
        
        Args:
            data: Event data (string or dict, will be JSON-serialized)
            event: Event type name
            id: Event ID (auto-generated if None)
        """
        async with self._lock:
            self._event_id += 1
            if id is None:
                id = str(self._event_id)
            
            sse_event = SSEEvent(data=data, event=event, id=id)
            
            # Store in history
            self._history.append(sse_event)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]
            
            event_dict = {"event": event, "data": data, "id": id}
            
            # Send to all subscribers
            dead = []
            for queue in self._subscribers:
                try:
                    queue.put_nowait(event_dict)
                except asyncio.QueueFull:
                    dead.append(queue)
            
            for q in dead:
                try:
                    self._subscribers.remove(q)
                except ValueError:
                    pass
    
    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)
