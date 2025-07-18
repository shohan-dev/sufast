# Sufast Rust Core

The high-performance Rust engine that powers Sufast Python web framework.

## Architecture

This crate provides:

- **FFI Interface**: C-compatible functions for Python integration
- **HTTP Server**: Asynchronous HTTP server built on Axum/Tokio
- **Route Management**: Thread-safe route storage and dynamic dispatching
- **Performance**: Optimized for high throughput and low latency

## Building

```bash
cargo build --release
```

The resulting shared library (`libsufast_server.so` on Linux, `sufast_server.dll` on Windows) 
is used by the Python package.

## Testing

```bash
cargo test
```

## Benchmarking

```bash
cargo bench
```

## FFI Interface

### Functions

- `set_routes(json_ptr: *const u8, len: usize) -> bool`
- `start_server(production: bool, port: u16) -> bool`

### Safety

All FFI functions are marked as `unsafe` where appropriate and include proper 
null-pointer checks and error handling.
