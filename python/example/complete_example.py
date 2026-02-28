"""
Sufast Complete Example Application
====================================
Demonstrates all major features of the Sufast framework:
- REST API (GET, POST, PUT, DELETE, PATCH)
- Path parameters with type validation
- Query parameters
- Request body parsing (JSON, form)
- WebSocket real-time communication
- Socket.IO with rooms/namespaces
- Middleware (CORS, logging, timing)
- Background tasks
- API Router for modular code
- Static file serving
- Custom exception handlers
- Startup/shutdown events
- OpenAPI docs at /docs

Run with:
    cd python
    python -m example.complete_example

Then visit:  
    http://127.0.0.1:8000/docs   for Swagger UI
    http://127.0.0.1:8000/redoc  for ReDoc
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import time
from sufast import (
    Sufast, APIRouter, Request, Response,
    json_response, html_response, text_response,
    HTTPException, BackgroundTasks, WebSocket,
    CORSMiddleware,
)
from sufast.socketio_support import SocketIOManager

# ============================================================
# Create the application
# ============================================================

app = Sufast(
    title="Sufast Demo API",
    description="A complete demo of the Sufast hybrid Rust+Python framework featuring REST, WebSocket, Socket.IO, and more.",
    version="3.0.0",
    debug=True,
)

# ============================================================
# Middleware
# ============================================================

app.add_middleware(CORSMiddleware, allow_origins=["*"])

@app.middleware("http")
async def timing_middleware(request, call_next):
    """Add request timing header."""
    start = time.time()
    response = await call_next(request)
    elapsed = time.time() - start
    if isinstance(response, Response):
        response.headers["X-Process-Time"] = f"{elapsed:.4f}s"
    elif isinstance(response, dict) and 'headers' in response:
        response['headers']['X-Process-Time'] = f"{elapsed:.4f}s"
    return response

# ============================================================
# Events
# ============================================================

@app.on_event("startup")
async def on_startup():
    print("  Application startup complete!")

@app.on_event("shutdown")
async def on_shutdown():
    print("  Application shutting down...")

# ============================================================
# Basic Routes
# ============================================================

@app.get("/", tags=["General"], summary="Home")
async def root():
    """Welcome endpoint with server info."""
    return {
        "message": "Welcome to Sufast!",
        "version": "3.0.0",
        "docs": "/docs",
        "rust_accelerated": app.is_rust_accelerated,
    }

@app.get("/health", tags=["System"], summary="Health Check")
async def health():
    """Server health status."""
    return {"status": "healthy", "uptime": "ok"}

@app.get("/stats", tags=["System"], summary="Performance Stats")
async def performance_stats():
    """Server performance statistics."""
    return app.get_performance_stats()

# ============================================================
# Users CRUD API
# ============================================================

# In-memory "database"
users_db = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com", "role": "admin"},
    2: {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "user"},
    3: {"id": 3, "name": "Charlie", "email": "charlie@example.com", "role": "user"},
}
next_user_id = 4

@app.get("/api/users", tags=["Users"], summary="List all users")
async def list_users(request: Request):
    """Get all users with optional role filter.
    
    Query params:
        role: Filter by role (admin/user)
        limit: Max results (default 10)
    """
    role = request.query_params.get("role")
    limit = int(request.query_params.get("limit", "10"))
    
    users = list(users_db.values())
    if role:
        users = [u for u in users if u["role"] == role]
    
    return {
        "users": users[:limit],
        "total": len(users),
        "limit": limit,
    }

@app.get("/api/users/{user_id}", tags=["Users"], summary="Get user by ID")
async def get_user(user_id: int):
    """Get a specific user by their ID."""
    if user_id not in users_db:
        raise HTTPException(404, f"User {user_id} not found")
    return users_db[user_id]

@app.post("/api/users", tags=["Users"], summary="Create user", status_code=201)
async def create_user(request: Request):
    """Create a new user.
    
    Request body (JSON):
        name: User's full name
        email: Email address  
        role: User role (admin/user)
    """
    global next_user_id
    data = request.json
    if not data:
        raise HTTPException(400, "Request body must be JSON")
    
    if not data.get("name") or not data.get("email"):
        raise HTTPException(422, "name and email are required")
    
    user = {
        "id": next_user_id,
        "name": data["name"],
        "email": data["email"],
        "role": data.get("role", "user"),
    }
    users_db[next_user_id] = user
    next_user_id += 1
    
    return user

@app.put("/api/users/{user_id}", tags=["Users"], summary="Update user")
async def update_user(user_id: int, request: Request):
    """Update an existing user."""
    if user_id not in users_db:
        raise HTTPException(404, f"User {user_id} not found")
    
    data = request.json
    if not data:
        raise HTTPException(400, "Request body must be JSON")
    
    user = users_db[user_id]
    user.update({k: v for k, v in data.items() if k != "id"})
    return user

@app.patch("/api/users/{user_id}", tags=["Users"], summary="Partial update user")
async def patch_user(user_id: int, request: Request):
    """Partially update a user (only provided fields)."""
    if user_id not in users_db:
        raise HTTPException(404, f"User {user_id} not found")
    
    data = request.json or {}
    user = users_db[user_id]
    for key, value in data.items():
        if key != "id":
            user[key] = value
    return user

@app.delete("/api/users/{user_id}", tags=["Users"], summary="Delete user")
async def delete_user(user_id: int):
    """Delete a user by ID."""
    if user_id not in users_db:
        raise HTTPException(404, f"User {user_id} not found")
    
    user = users_db.pop(user_id)
    return {"deleted": True, "user": user}

# ============================================================
# Products API (using APIRouter)
# ============================================================

products_router = APIRouter(prefix="/api/products", tags=["Products"])

products_db = {
    1: {"id": 1, "name": "Laptop", "price": 999.99, "stock": 50},
    2: {"id": 2, "name": "Phone", "price": 699.99, "stock": 100},
    3: {"id": 3, "name": "Tablet", "price": 449.99, "stock": 75},
}

@products_router.get("/", summary="List products")
async def list_products():
    """Get all products."""
    return {"products": list(products_db.values())}

@products_router.get("/{product_id}", summary="Get product")
async def get_product(product_id: int):
    """Get a product by ID."""
    if product_id not in products_db:
        raise HTTPException(404, f"Product {product_id} not found")
    return products_db[product_id]

@products_router.post("/", summary="Create product", status_code=201)
async def create_product(request: Request):
    """Create a new product."""
    data = request.json
    if not data:
        raise HTTPException(400, "JSON body required")
    
    pid = max(products_db.keys()) + 1 if products_db else 1
    product = {"id": pid, **data}
    products_db[pid] = product
    return product

app.include_router(products_router)

# ============================================================
# Background Tasks
# ============================================================

async def send_welcome_email(email: str, name: str):
    """Simulate sending a welcome email."""
    import asyncio
    await asyncio.sleep(0.1)  # Simulate IO
    print(f"  [Background] Sent welcome email to {email} for {name}")

@app.post("/api/register", tags=["Auth"], summary="Register user with background task")
async def register(request: Request, background_tasks: BackgroundTasks):
    """Register a user and send welcome email in the background."""
    data = request.json or {}
    name = data.get("name", "User")
    email = data.get("email", "user@example.com")
    
    background_tasks.add_task(send_welcome_email, email, name)
    
    return {"message": f"Registration started for {name}", "email": email}

# ============================================================
# Custom Exception Handlers
# ============================================================

@app.exception_handler(404)
async def custom_404(request, exc):
    return json_response(
        {"error": "Not Found", "path": request.path if request else "unknown",
         "hint": "Check /docs for available endpoints"},
        status=404
    )

# ============================================================
# Response Types Demo
# ============================================================

@app.get("/html", tags=["Demo"], summary="HTML Response")
async def html_demo():
    """Returns an HTML response."""
    return html_response("""
    <!DOCTYPE html>
    <html>
    <head><title>Sufast HTML Demo</title></head>
    <body style="font-family: sans-serif; padding: 2rem; background: #0f172a; color: #e2e8f0;">
        <h1 style="color: #818cf8;">Sufast HTML Response</h1>
        <p>This is a server-rendered HTML page from Sufast.</p>
        <a href="/docs" style="color: #38bdf8;">View API Docs</a>
    </body>
    </html>
    """)

@app.get("/text", tags=["Demo"], summary="Plain Text Response")
async def text_demo():
    """Returns a plain text response."""
    return text_response("Hello from Sufast! This is plain text.")

# ============================================================
# Sync Handler Demo
# ============================================================

@app.get("/sync", tags=["Demo"], summary="Synchronous Handler")
def sync_handler():
    """Demonstrates that sync handlers also work."""
    return {"type": "sync", "message": "This handler is not async - and it works!"}

# ============================================================
# WebSocket
# ============================================================

@app.websocket("/ws")
async def websocket_echo(websocket: WebSocket):
    """WebSocket echo server. Send a message and get it back."""
    await websocket.accept()
    try:
        async for message in websocket.iter_text():
            await websocket.send_json({
                "type": "echo",
                "data": message,
                "timestamp": time.time(),
            })
    except Exception:
        pass

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """Simple chat WebSocket. Messages are JSON with 'username' and 'message'."""
    await websocket.accept()
    await websocket.send_json({"type": "system", "message": "Welcome to chat!"})
    try:
        async for data in websocket.iter_json():
            response = {
                "type": "chat",
                "username": data.get("username", "Anonymous"),
                "message": data.get("message", ""),
                "timestamp": time.time(),
            }
            await websocket.send_json(response)
    except Exception:
        pass

# ============================================================
# Socket.IO
# ============================================================

sio = SocketIOManager(app, path="/socket.io")

@sio.on("connect")
async def sio_connect(sid):
    print(f"  [Socket.IO] Client connected: {sid}")

@sio.on("message")
async def sio_message(sid, data):
    print(f"  [Socket.IO] Message from {sid}: {data}")
    await sio.emit("response", {"echo": data, "from": sid}, to=sid)

@sio.on("join_room")
async def sio_join(sid, data):
    room = data.get("room", "general") if isinstance(data, dict) else str(data)
    await sio.enter_room(sid, room)
    await sio.emit("system", {"message": f"Joined room: {room}"}, to=sid)

@sio.on("disconnect")
async def sio_disconnect(sid):
    print(f"  [Socket.IO] Client disconnected: {sid}")

# ============================================================
# Start Server
# ============================================================

if __name__ == "__main__":
    print("\n  Starting Sufast Demo API...")
    print("  Try these endpoints:")
    print("    GET  http://127.0.0.1:8000/              - Home")
    print("    GET  http://127.0.0.1:8000/docs           - Swagger UI")
    print("    GET  http://127.0.0.1:8000/redoc          - ReDoc")
    print("    GET  http://127.0.0.1:8000/api/users      - List users")
    print("    POST http://127.0.0.1:8000/api/users      - Create user")
    print("    GET  http://127.0.0.1:8000/api/products   - List products")
    print("    WS   ws://127.0.0.1:8000/ws               - WebSocket echo")
    print()
    
    app.run(host="127.0.0.1", port=8000, debug=True)
