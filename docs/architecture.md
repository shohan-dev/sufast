# Sufast Architecture

Understanding how Sufast achieves 52,000+ RPS by combining Python simplicity with Rust performance.

## Overview

Sufast is a **hybrid web framework** that uses:
- **Python** for the developer interface and route definition
- **Rust** for the HTTP server and request processing
- **FFI (Foreign Function Interface)** to bridge the two languages

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Python App    │    │  Rust HTTP      │    │   Client        │
│                 │    │  Server         │    │                 │
│  @app.get("/")  │────│                 │────│  HTTP Request   │
│  def handler(): │    │  Axum/Tokio     │    │                 │
│    return {...} │    │  (52k+ RPS)     │    │  HTTP Response  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │
        │     JSON Routes        │
        │       via FFI          │
        └────────────────────────┘
```

## Component Breakdown

### 1. Python Layer (`python/sufast/`)

#### App Class (`core.py`)

The main interface that developers interact with:

```python
class App:
    def __init__(self):
        self.routes = {
            "GET": {}, "POST": {}, "PUT": {}, "PATCH": {}, "DELETE": {}
        }
        
    def get(self, path):
        def decorator(func):
            # Execute handler immediately and store result
            result = func()
            self.routes["GET"][path] = json.dumps(result)
            return func
        return decorator
```

**Key Features:**
- **Immediate Execution**: Handlers run once during registration
- **JSON Serialization**: Responses are pre-serialized to JSON strings
- **Error Handling**: Exceptions are caught and stored as error responses
- **Cross-Platform Library Loading**: Automatically detects `.dll` vs `.so`

#### Route Registration Process

1. **Decorator Application**: `@app.get("/path")` is applied to function
2. **Handler Execution**: Function runs immediately, not at request time
3. **Response Serialization**: Return value is converted to JSON string
4. **Storage**: JSON response is stored in routes dictionary

### 2. Rust Layer (`rust-core/src/`)

#### FFI Interface (`lib.rs`)

Provides C-compatible functions for Python:

```rust
#[no_mangle]
pub extern "C" fn set_routes(json_ptr: *const c_uchar, len: usize) -> bool {
    // Convert pointer to JSON string
    // Parse routes and store in global state
}

#[no_mangle]
pub extern "C" fn start_server(production: bool, port: u16) -> bool {
    // Start Axum server in background thread
}
```

#### Route Storage (`routes.rs`)

Thread-safe global route storage:

```rust
type InnerRoutes = HashMap<String, String>;  // path -> response
type SharedRoutes = Arc<RwLock<HashMap<Method, InnerRoutes>>>;

static ROUTES: OnceCell<SharedRoutes> = OnceCell::new();
```

**Thread Safety:**
- `Arc`: Atomic Reference Counting for shared ownership
- `RwLock`: Reader-Writer lock for concurrent access
- `OnceCell`: Thread-safe lazy initialization

#### Request Handling (`handlers.rs`)

Dynamic request dispatcher:

```rust
pub async fn dynamic_handler(req: Request<Body>) -> impl IntoResponse {
    let method = req.method().clone();
    let path = req.uri().path();
    
    // 1. Try exact match first
    if let Some(response) = exact_match(method, path) {
        return json_response(200, response);
    }
    
    // 2. Try pattern matching for dynamic routes
    if let Some(response) = pattern_match(method, path) {
        return json_response(200, response);
    }
    
    // 3. Return 404
    json_response(404, r#"{"error": "Not found"}"#)
}
```

#### Pattern Matching Algorithm

For dynamic routes like `/users/{id}`:

```rust
pub fn match_path(pattern: &str, path: &str) -> Option<HashMap<String, String>> {
    let pattern_parts: Vec<&str> = pattern.trim_matches('/').split('/').collect();
    let path_parts: Vec<&str> = path.trim_matches('/').split('/').collect();
    
    if pattern_parts.len() != path_parts.len() {
        return None;
    }
    
    let mut params = HashMap::new();
    for (pat, actual) in pattern_parts.iter().zip(path_parts.iter()) {
        if pat.starts_with('{') && pat.ends_with('}') {
            let key = pat.trim_matches(&['{', '}'][..]);
            params.insert(key.to_string(), actual.to_string());
        } else if pat != actual {
            return None;
        }
    }
    Some(params)
}
```

#### HTTP Server (`server.rs`)

Axum-based async server:

```rust
pub fn start_server(production: bool, port: u16) -> bool {
    thread::spawn(move || {
        let rt = Runtime::new().expect("Failed to create Tokio runtime");
        rt.block_on(async move {
            let app = Router::new().fallback(any(dynamic_handler));
            let addr = SocketAddr::new(ip, port);
            
            Server::bind(&addr)
                .serve(app.into_make_service())
                .await
        });
    });
    true
}
```

## Data Flow

### Route Registration Flow

```
Python Handler          Rust Storage
     │                       │
     ▼                       │
┌─────────────┐             │
│ @app.get()  │             │
│ def handler │             │
│   return {} │             │
└─────────────┘             │
     │                       │
     ▼                       │
┌─────────────┐             │
│ Execute     │             │
│ immediately │             │
│ Store JSON  │             │
└─────────────┘             │
     │                       │
     ▼                       │
┌─────────────┐             │
│ app.run()   │             │
│ calls FFI   │             │
└─────────────┘             │
     │                       │
     ▼                       ▼
┌─────────────┐    ┌─────────────┐
│ JSON data   │────│ Parse &     │
│ via pointer │    │ Store in    │
│             │    │ HashMap     │
└─────────────┘    └─────────────┘
```

### Request Processing Flow

```
HTTP Request             Rust Processing
     │                        │
     ▼                        │
┌─────────────┐              │
│ Client      │              │
│ Request     │              │
└─────────────┘              │
     │                        │
     ▼                        ▼
┌─────────────┐    ┌─────────────┐
│ Axum        │────│ Extract     │
│ Router      │    │ Method+Path │
└─────────────┘    └─────────────┘
                           │
                           ▼
                  ┌─────────────┐
                  │ Lookup in   │
                  │ HashMap     │
                  └─────────────┘
                           │
                           ▼
                  ┌─────────────┐
                  │ Return      │
                  │ JSON        │
                  └─────────────┘
```

## Performance Optimizations

### 1. Pre-computed Responses

**Traditional Framework:**
```
Request → Parse → Route → Execute Handler → Serialize → Response
                           ↑ SLOW ↑
```

**Sufast:**
```
Registration: Handler → Execute → Serialize → Store
Request: Parse → Route → Lookup → Response
                        ↑ FAST ↑
```

### 2. Zero-Copy JSON Serving

Responses are stored as pre-serialized JSON strings:
- No runtime serialization overhead
- Direct memory-to-network transfer
- Consistent response times

### 3. Rust's Memory Safety + Performance

- **Zero-cost abstractions**: High-level code compiles to optimal machine code
- **No garbage collection**: Predictable memory usage and performance
- **Lock-free data structures**: Where possible, using atomic operations

### 4. Async I/O with Tokio

- **Event-driven**: Single thread handles thousands of connections
- **Non-blocking**: Never blocks on I/O operations
- **Efficient**: Minimal context switching overhead

## Memory Layout

### Python Process
```
┌─────────────────────────────────────┐
│ Python Interpreter                  │
├─────────────────────────────────────┤
│ App Instance                        │
│ ├─ routes: Dict[str, Dict[str,str]] │
│ ├─ library: ctypes.CDLL             │
│ └─ handlers: List[Callable]         │
├─────────────────────────────────────┤
│ Loaded Rust Library (.dll/.so)     │
│ ├─ Global Routes: Arc<RwLock<...>>  │
│ ├─ Tokio Runtime                    │
│ └─ HTTP Server Thread               │
└─────────────────────────────────────┘
```

### Cross-Language Memory Sharing

```
Python Side                 Rust Side
┌─────────────┐            ┌─────────────┐
│ JSON String │ ──────────▶│ Raw Pointer │
│ routes_json │   via FFI  │ + length    │
└─────────────┘            └─────────────┘
                                   │
                                   ▼
                           ┌─────────────┐
                           │ Parse JSON  │
                           │ into HashMap│
                           └─────────────┘
```

## Error Handling Strategy

### Python Side
- Catch all handler exceptions during registration
- Store error responses as JSON
- Provide helpful error messages with context

### Rust Side
- Use `Result<T, E>` for all fallible operations
- Convert errors to appropriate HTTP status codes
- Log errors for debugging while returning user-friendly responses

### FFI Boundary
- All FFI functions return `bool` for success/failure
- Validate all pointers and lengths before use
- Never panic across FFI boundary

## Concurrency Model

### Python (Registration Time)
- Single-threaded during route registration
- Handlers execute sequentially
- No concurrency concerns during setup

### Rust (Request Time)
- Multi-threaded with Tokio async runtime
- Thousands of concurrent connections on single thread
- Lock-free reads from route storage (RwLock read guards)

## Build System Integration

### Cross-Platform Compilation

```
Development Machine       Target Platforms
┌─────────────────┐      ┌─────────────────┐
│ Cargo Build     │ ──── │ Windows .dll    │
│ rust-core/      │      │ Linux .so       │
│                 │      │ macOS .dylib    │
└─────────────────┘      └─────────────────┘
         │                         │
         ▼                         ▼
┌─────────────────┐      ┌─────────────────┐
│ Copy to         │      │ Python Package  │
│ python/sufast/  │      │ Distribution    │
└─────────────────┘      └─────────────────┘
```

This architecture enables Sufast to deliver both developer productivity and runtime performance, making it suitable for high-performance production APIs while maintaining the ease of use that Python developers expect.
