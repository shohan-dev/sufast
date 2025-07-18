pub mod handlers;
pub mod routes;
pub mod server;

use crate::routes::set_static_routes;
use axum::http::Method;
use std::collections::HashMap;
use std::os::raw::c_uchar;

/// Extern C interface for Python / FFI

/// JSON routes parsing helper
#[derive(serde::Deserialize)]
struct RoutesJson(HashMap<String, HashMap<String, String>>);

/// FFI: Set routes from JSON string pointer and length.
/// Returns true on success, false on failure.
#[no_mangle]
pub extern "C" fn set_routes(json_ptr: *const c_uchar, len: usize) -> bool {
    if json_ptr.is_null() || len == 0 {
        return false;
    }
    // Safety: convert pointer to slice
    let bytes = unsafe { std::slice::from_raw_parts(json_ptr, len) };
    let json_str = match std::str::from_utf8(bytes) {
        Ok(s) => s,
        Err(_) => return false,
    };

    let parsed: RoutesJson = match serde_json::from_str(json_str) {
        Ok(p) => p,
        Err(_) => return false,
    };

    let mut new_map: HashMap<Method, HashMap<String, String>> = HashMap::new();

    for (method_str, inner_map) in parsed.0 {
        if let Ok(method) = method_str.parse::<Method>() {
            new_map.insert(method, inner_map);
        }
    }

    set_static_routes(new_map)
}

/// FFI: Start the server with production flag and port
#[no_mangle]
pub extern "C" fn start_server(production: bool, port: u16) -> bool {
    crate::server::start_server(production, port)
}
