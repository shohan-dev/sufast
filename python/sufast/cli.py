"""
Sufast CLI - Command-line tool for Sufast framework.
======================================================
Provides commands for development, testing, and deployment.

Usage (from terminal):
    python -m sufast run app:app --port 8000 --reload
    python -m sufast new myproject
    python -m sufast routes app:app
    python -m sufast version
"""

import argparse
import importlib
import os
import sys
import time
import signal


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="sufast",
        description="Sufast - Hybrid Rust+Python Web Framework CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sufast run app:app                    Start server with default settings
  sufast run app:app --port 8000        Start on port 8000
  sufast run app:app --reload           Start with auto-reload
  sufast run app:app --host 0.0.0.0     Bind to all interfaces
  sufast routes app:app                 Show all registered routes
  sufast new myproject                  Create new project scaffold
  sufast version                        Show version info
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # run command
    run_parser = subparsers.add_parser("run", help="Start the development server")
    run_parser.add_argument("app", help="Application import path (e.g., 'app:app' or 'myapp.main:app')")
    run_parser.add_argument("--host", "-H", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    run_parser.add_argument("--port", "-p", type=int, default=8000, help="Port to bind to (default: 8000)")
    run_parser.add_argument("--reload", "-r", action="store_true", help="Auto-reload on file changes")
    run_parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode")
    run_parser.add_argument("--workers", "-w", type=int, default=1, help="Number of worker processes")
    run_parser.add_argument("--no-docs", action="store_true", help="Disable documentation endpoints")
    run_parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"], help="Log level")
    
    # routes command
    routes_parser = subparsers.add_parser("routes", help="List all registered routes")
    routes_parser.add_argument("app", help="Application import path")
    routes_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    # new command
    new_parser = subparsers.add_parser("new", help="Create a new Sufast project")
    new_parser.add_argument("name", help="Project name")
    new_parser.add_argument("--template", choices=["minimal", "full", "api"], default="full", help="Project template")
    
    # version command
    subparsers.add_parser("version", help="Show version information")
    
    # openapi command
    openapi_parser = subparsers.add_parser("openapi", help="Export OpenAPI JSON spec")
    openapi_parser.add_argument("app", help="Application import path")
    openapi_parser.add_argument("--output", "-o", default="-", help="Output file (- for stdout)")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    if args.command == "version":
        cmd_version()
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "routes":
        cmd_routes(args)
    elif args.command == "new":
        cmd_new(args)
    elif args.command == "openapi":
        cmd_openapi(args)
    else:
        parser.print_help()


def _import_app(app_path: str):
    """Import an app from a module:attribute path."""
    if ":" not in app_path:
        print(f"Error: Invalid app path '{app_path}'. Use format 'module:attribute' (e.g., 'app:app')")
        sys.exit(1)
    
    module_path, attr_name = app_path.rsplit(":", 1)
    
    # Add cwd to sys.path
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
    
    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        print(f"Error: Could not import module '{module_path}': {e}")
        sys.exit(1)
    
    app = getattr(module, attr_name, None)
    if app is None:
        print(f"Error: Module '{module_path}' has no attribute '{attr_name}'")
        sys.exit(1)
    
    return app


def cmd_version():
    """Show version information."""
    from sufast import __version__
    
    print(f"\n  Sufast v{__version__}")
    print(f"  Hybrid Rust+Python Web Framework")
    print(f"  Python {sys.version.split()[0]}")
    
    try:
        from sufast.app import Sufast
        test_app = Sufast.__new__(Sufast)
        test_app._rust_core = None
        test_app._rust_available = False
        test_app._try_load_rust_core = lambda: None
        print(f"  Rust core: checking...")
    except Exception:
        pass
    
    print()


def cmd_run(args):
    """Run the development server."""
    app = _import_app(args.app)
    
    if args.reload:
        _run_with_reload(args)
    else:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            docs=not args.no_docs,
            workers=args.workers,
        )


def _run_with_reload(args):
    """Run with auto-reload by watching for file changes."""
    import subprocess
    
    print(f"  \033[1;36m⚡ Sufast\033[0m auto-reload enabled")
    print(f"  \033[90mWatching for file changes...\033[0m\n")
    
    watched_extensions = {".py", ".json", ".yaml", ".yml", ".toml", ".env"}
    watched_dirs = [os.getcwd()]
    
    def get_file_mtimes():
        mtimes = {}
        for watch_dir in watched_dirs:
            for root, dirs, files in os.walk(watch_dir):
                # Skip hidden and cache dirs
                dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__" 
                          and d != "node_modules" and d != ".git"]
                for f in files:
                    ext = os.path.splitext(f)[1]
                    if ext in watched_extensions:
                        path = os.path.join(root, f)
                        try:
                            mtimes[path] = os.path.getmtime(path)
                        except OSError:
                            pass
        return mtimes
    
    # Run in subprocess loop
    while True:
        mtimes = get_file_mtimes()
        
        # Build command without --reload flag
        cmd = [sys.executable, "-m", "sufast", "run", args.app,
               "--host", args.host, "--port", str(args.port)]
        if args.debug:
            cmd.append("--debug")
        if args.no_docs:
            cmd.append("--no-docs")
        
        proc = subprocess.Popen(cmd)
        
        try:
            while True:
                time.sleep(1)
                
                # Check if process died
                if proc.poll() is not None:
                    print(f"\n  \033[33mServer exited (code {proc.returncode}). Restarting...\033[0m\n")
                    time.sleep(1)
                    break
                
                # Check for file changes
                new_mtimes = get_file_mtimes()
                changed = False
                for path, mtime in new_mtimes.items():
                    if path not in mtimes or mtimes[path] != mtime:
                        rel = os.path.relpath(path)
                        print(f"\n  \033[33m⟳ Detected change: {rel}\033[0m")
                        changed = True
                        break
                
                if changed:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    print(f"  \033[36mRestarting server...\033[0m\n")
                    time.sleep(0.5)
                    break
                
                mtimes = new_mtimes
                
        except KeyboardInterrupt:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
            print("\n  \033[90mStopped.\033[0m")
            break


def cmd_routes(args):
    """List all registered routes."""
    import json as json_module
    
    app = _import_app(args.app)
    routes = app.get_routes()
    
    if args.json:
        print(json_module.dumps(routes, indent=2, default=str))
        return
    
    print(f"\n  \033[1mRegistered Routes ({len(routes)} total)\033[0m\n")
    print(f"  {'Method':<8} {'Path':<35} {'Name':<25} {'Tags'}")
    print(f"  {'─' * 8} {'─' * 35} {'─' * 25} {'─' * 20}")
    
    # Sort by path
    routes.sort(key=lambda r: (r.get("path", ""), r.get("method", "")))
    
    method_colors = {
        "GET": "\033[32m",     # green
        "POST": "\033[33m",    # yellow
        "PUT": "\033[34m",     # blue
        "DELETE": "\033[31m",  # red
        "PATCH": "\033[35m",   # magenta
        "HEAD": "\033[90m",    # gray
        "OPTIONS": "\033[90m", # gray
    }
    
    for route in routes:
        method = route.get("method", "?")
        path = route.get("path", "?")
        name = route.get("function_name", "?")
        tags = ", ".join(route.get("tags", []))
        
        color = method_colors.get(method, "")
        reset = "\033[0m" if color else ""
        
        print(f"  {color}{method:<8}{reset} {path:<35} {name:<25} {tags}")
    
    print()


def cmd_new(args):
    """Create a new project scaffold."""
    project_name = args.name
    
    if os.path.exists(project_name):
        print(f"Error: Directory '{project_name}' already exists")
        sys.exit(1)
    
    print(f"\n  Creating new Sufast project: {project_name}")
    
    os.makedirs(project_name)
    os.makedirs(os.path.join(project_name, "static"), exist_ok=True)
    os.makedirs(os.path.join(project_name, "templates"), exist_ok=True)
    
    # Create main app file
    if args.template == "minimal":
        app_content = _TEMPLATE_MINIMAL
    elif args.template == "api":
        app_content = _TEMPLATE_API
    else:
        app_content = _TEMPLATE_FULL
    
    with open(os.path.join(project_name, "app.py"), "w") as f:
        f.write(app_content)
    
    # Create .env
    with open(os.path.join(project_name, ".env"), "w") as f:
        f.write(f"# {project_name} Configuration\n")
        f.write(f"SECRET_KEY={os.urandom(32).hex()}\n")
        f.write("DEBUG=true\n")
        f.write("HOST=127.0.0.1\n")
        f.write("PORT=8000\n")
    
    # Create .gitignore
    with open(os.path.join(project_name, ".gitignore"), "w") as f:
        f.write("__pycache__/\n*.pyc\n.env\n*.db\n.sessions/\nlogs/\n")
    
    # Create requirements.txt
    with open(os.path.join(project_name, "requirements.txt"), "w") as f:
        f.write("sufast>=3.0.0\n")
    
    print(f"  ✓ Created project structure")
    print(f"\n  To get started:")
    print(f"    cd {project_name}")
    print(f"    python -m sufast run app:app --reload\n")


def cmd_openapi(args):
    """Export OpenAPI spec."""
    import json as json_module
    
    app = _import_app(args.app)
    spec = app._generate_openapi_spec()
    
    output = json_module.dumps(spec, indent=2, default=str)
    
    if args.output == "-":
        print(output)
    else:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"  OpenAPI spec written to {args.output}")


# ======================================================
# Project Templates
# ======================================================

_TEMPLATE_MINIMAL = '''"""Minimal Sufast application."""
from sufast import Sufast

app = Sufast(title="My App")

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    app.run()
'''

_TEMPLATE_API = '''"""Sufast REST API application."""
from sufast import Sufast, APIRouter, Request, HTTPException

app = Sufast(title="My API", version="1.0.0", description="REST API powered by Sufast")

# In-memory store (replace with database in production)
items = {}
next_id = 1

router = APIRouter(prefix="/api/v1", tags=["Items"])

@router.get("/items")
async def list_items():
    """List all items."""
    return {"items": list(items.values()), "total": len(items)}

@router.get("/items/{item_id}")
async def get_item(item_id: int):
    """Get item by ID."""
    if item_id not in items:
        raise HTTPException(404, f"Item {item_id} not found")
    return items[item_id]

@router.post("/items", status_code=201)
async def create_item(request: Request):
    """Create a new item."""
    global next_id
    data = request.json
    item = {"id": next_id, **data}
    items[next_id] = item
    next_id += 1
    return item

@router.put("/items/{item_id}")
async def update_item(item_id: int, request: Request):
    """Update an item."""
    if item_id not in items:
        raise HTTPException(404, f"Item {item_id} not found")
    data = request.json
    items[item_id].update(data)
    return items[item_id]

@router.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """Delete an item."""
    if item_id not in items:
        raise HTTPException(404, f"Item {item_id} not found")
    deleted = items.pop(item_id)
    return {"deleted": deleted}

app.include_router(router)

@app.get("/health", tags=["System"])
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    app.run(debug=True)
'''

_TEMPLATE_FULL = '''"""Full Sufast application with all features."""
from sufast import (
    Sufast, APIRouter, Request, Response, HTTPException,
    json_response, BackgroundTasks, CORSMiddleware,
)
from sufast.security import JWTAuth, hash_password, verify_password
from sufast.sessions import SessionMiddleware, InMemorySessionStore
from sufast.compression import CompressionMiddleware
from sufast.logging import get_logger, configure_logging

# Configure logging
configure_logging(level="debug", format="console")
logger = get_logger("app")

# Create app
app = Sufast(
    title="My App",
    version="1.0.0",
    description="Full-featured Sufast application",
)

# Middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"])
app.add_middleware(CompressionMiddleware, minimum_size=1024)
app.add_middleware(
    SessionMiddleware,
    secret_key="change-this-in-production!",
    store=InMemorySessionStore(),
)

# JWT auth
jwt = JWTAuth(secret_key="change-this-secret-key!!")

# Startup/shutdown events
@app.on_event("startup")
async def startup():
    logger.info("Application starting...")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Application shutting down...")

# Routes
@app.get("/", tags=["General"])
async def root():
    """Welcome page."""
    return {"message": "Welcome to My App!", "docs": "/docs"}

@app.get("/health", tags=["System"])
async def health():
    """Health check."""
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/auth/login", tags=["Auth"])
async def login(request: Request):
    """Login and get JWT token."""
    data = request.json
    # TODO: Validate credentials against database
    token = jwt.create_token({"user_id": 1, "role": "admin"})
    refresh = jwt.create_refresh_token({"user_id": 1})
    return {"access_token": token, "refresh_token": refresh, "token_type": "bearer"}

# API Router
api = APIRouter(prefix="/api/v1", tags=["API"])

@api.get("/items")
async def list_items():
    """List items."""
    return {"items": []}

app.include_router(api)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
'''


if __name__ == "__main__":
    main()
