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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::handlers::match_path;
    use crate::routes::set_static_routes;
    use axum::http::Method;

    #[test]
    fn test_match_path_exact() {
        let pattern = "/users";
        let path = "/users";
        let result = match_path(pattern, path);
        assert!(result.is_some());
        assert!(result.unwrap().is_empty());
    }

    #[test]
    fn test_match_path_single_param() {
        let pattern = "/users/{id}";
        let path = "/users/123";
        let result = match_path(pattern, path);
        assert!(result.is_some());
        let params = result.unwrap();
        assert_eq!(params.get("id"), Some(&"123".to_string()));
    }

    #[test]
    fn test_match_path_multiple_params() {
        let pattern = "/users/{id}/posts/{post_id}";
        let path = "/users/123/posts/456";
        let result = match_path(pattern, path);
        assert!(result.is_some());
        let params = result.unwrap();
        assert_eq!(params.get("id"), Some(&"123".to_string()));
        assert_eq!(params.get("post_id"), Some(&"456".to_string()));
    }

    #[test]
    fn test_match_path_no_match() {
        let pattern = "/users/{id}";
        let path = "/posts/123";
        let result = match_path(pattern, path);
        assert!(result.is_none());
    }

    #[test]
    fn test_set_and_get_routes() {
        let mut routes = HashMap::new();
        let mut routes_map = HashMap::new();
        routes_map.insert("/test".to_string(), r#"{"message": "test"}"#.to_string());
        routes.insert(Method::GET, routes_map);

        assert!(set_static_routes(routes));

        let retrieved_routes = crate::routes::get_routes();
        assert!(retrieved_routes.is_some());
    }

    #[test]
    fn test_set_routes_ffi() {
        let json_data = r#"{"GET": {"/test": "{\"message\": \"test\"}"}}"#;
        let bytes = json_data.as_bytes();

        let result = set_routes(bytes.as_ptr(), bytes.len());
        assert!(result);
    }

    #[test]
    fn test_set_routes_invalid_json() {
        let invalid_json = "invalid json";
        let bytes = invalid_json.as_bytes();

        let result = set_routes(bytes.as_ptr(), bytes.len());
        assert!(!result);
    }

    #[test]
    fn test_set_routes_null_pointer() {
        let result = set_routes(std::ptr::null(), 0);
        assert!(!result);
    }
}
