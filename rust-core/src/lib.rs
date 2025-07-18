// Enhanced Sufast Rust Core v2.0 - Complete Dynamic Routing Implementation
// This implements dynamic routing with Python callbacks for maximum performance

pub mod middleware;
pub mod routing;
pub mod request;
pub mod response;
pub mod security;
pub mod rate_limiting;

use axum::{
    extract::{State, Path as AxumPath, Query, Request as AxumRequest},
    http::{Method, StatusCode, HeaderMap, Uri},
    response::{Response as AxumResponse, Json},
    routing::{any, get, post, put, patch, delete},
    Router, body::{Body, to_bytes},
};
use serde_json::{Value, Map};
use std::collections::HashMap;
use std::ffi::{CStr, CString};
use std::os::raw::c_char;
use std::sync::{Arc, Mutex};
use tokio::net::TcpListener;
use tower_http::cors::CorsLayer;
use dashmap::DashMap;
use chrono::{DateTime, Utc};

use crate::routing::{RouteDefinition, RoutePattern, extract_path_params};
use crate::rate_limiting::RateLimiter;
use crate::security::SecurityHeaders;

// Core application state with complete features
#[derive(Debug, Clone)]
pub struct AppState {
    pub routes: Arc<DashMap<String, Vec<RouteDefinition>>>,
    pub route_patterns: Arc<DashMap<String, RoutePattern>>,
    pub python_handler: Arc<Mutex<Option<PythonHandler>>>,
    pub rate_limiter: Arc<RateLimiter>,
    pub security: Arc<SecurityHeaders>,
    pub request_count: Arc<Mutex<u64>>,
    pub start_time: DateTime<Utc>,
}

impl AppState {
    pub fn new() -> Self {
        Self {
            routes: Arc::new(DashMap::new()),
            route_patterns: Arc::new(DashMap::new()),
            python_handler: Arc::new(Mutex::new(None)),
            rate_limiter: Arc::new(RateLimiter::new(100, 60)),
            security: Arc::new(SecurityHeaders::new()),
            request_count: Arc::new(Mutex::new(0)),
            start_time: Utc::now(),
        }
    }
    
    pub fn increment_request_count(&self) -> u64 {
        let mut count = self.request_count.lock().unwrap();
        *count += 1;
        *count
    }

    // Find matching route pattern for a given path and method
    pub fn find_matching_route(&self, method: &str, path: &str) -> Option<(RouteDefinition, HashMap<String, String>)> {
        if let Some(routes) = self.routes.get(method) {
            for route in routes.iter() {
                // Check if this route has parameters (contains {})
                if route.path.contains('{') {
                    // Get the compiled pattern for this route
                    let pattern_key = format!("{}:{}", method, route.path);
                    if let Some(pattern) = self.route_patterns.get(&pattern_key) {
                        if let Some(params) = extract_path_params(&pattern, path) {
                            return Some((route.clone(), params));
                        }
                    }
                } else {
                    // Exact match for static routes
                    if route.path == path {
                        return Some((route.clone(), HashMap::new()));
                    }
                }
            }
        }
        None
    }
}

// Request data structure for Python callbacks
#[derive(serde::Serialize)]
struct RequestData {
    method: String,
    path: String,
    path_params: HashMap<String, String>,
    query_params: HashMap<String, String>,
    headers: HashMap<String, String>,
    body: String,
    handler_name: String,
}

type PythonHandler = extern "C" fn(*const c_char) -> *mut c_char;

static mut APP_STATE: Option<AppState> = None;

fn get_app_state() -> &'static AppState {
    unsafe {
        APP_STATE.get_or_insert_with(|| AppState::new())
    }
}

// Dynamic request handler that matches routes and calls Python
async fn dynamic_handler(
    State(state): State<AppState>, 
    method: Method,
    uri: Uri,
    headers: HeaderMap,
    request: AxumRequest<Body>
) -> Result<AxumResponse, StatusCode> {
    let request_id = state.increment_request_count();
    let path = uri.path();
    let method_str = method.as_str();
    
    println!("🔍 [{}] {} {} (Request #{})", method_str, path, uri.query().unwrap_or(""), request_id);
    
    // Extract body
    let body_bytes = match to_bytes(request.into_body(), usize::MAX).await {
        Ok(bytes) => bytes,
        Err(_) => return Err(StatusCode::BAD_REQUEST),
    };
    let body = String::from_utf8_lossy(&body_bytes).to_string();
    
    // Try to find a matching route
    if let Some((route, path_params)) = state.find_matching_route(method_str, path) {
        println!("✅ Route matched: {} -> {}", route.path, route.handler_name);
        println!("📋 Path params: {:?}", path_params);
        
        // Parse query parameters
        let query_params: HashMap<String, String> = uri.query()
            .map(|q| serde_urlencoded::from_str(q).unwrap_or_default())
            .unwrap_or_default();
        
        // Convert headers to HashMap
        let headers_map: HashMap<String, String> = headers
            .iter()
            .map(|(k, v)| (k.as_str().to_string(), v.to_str().unwrap_or("").to_string()))
            .collect();
        
        // Prepare request data for Python
        let request_data = RequestData {
            method: method_str.to_string(),
            path: path.to_string(),
            path_params,
            query_params,
            headers: headers_map,
            body,
            handler_name: route.handler_name.clone(),
        };
        
        // Call Python handler
        if let Some(handler) = state.python_handler.lock().unwrap().as_ref() {
            let json_request = serde_json::to_string(&request_data).unwrap();
            let c_request = CString::new(json_request).unwrap();
            
            let response_ptr = handler(c_request.as_ptr());
            
            if !response_ptr.is_null() {
                unsafe {
                    let c_response = CStr::from_ptr(response_ptr);
                    if let Ok(response_str) = c_response.to_str() {
                        // Parse Python response
                        if let Ok(response_data) = serde_json::from_str::<Value>(response_str) {
                            let status = response_data.get("status_code")
                                .and_then(|v| v.as_u64())
                                .unwrap_or(200) as u16;
                            
                            let body = response_data.get("body")
                                .and_then(|v| v.as_str())
                                .unwrap_or("")
                                .to_string();
                        
                            let mut response = AxumResponse::builder()
                                .status(StatusCode::from_u16(status).unwrap_or(StatusCode::OK));
                            
                            // Add headers from Python response
                            if let Some(headers_obj) = response_data.get("headers").and_then(|v| v.as_object()) {
                                for (key, value) in headers_obj {
                                    if let Some(value_str) = value.as_str() {
                                        response = response.header(key, value_str);
                                    }
                                }
                            }
                            
                            // Build response
                            let mut final_response = response.body(Body::from(body)).unwrap();
                            final_response = state.security.apply_headers(final_response);
                            
                            return Ok(final_response);
                        }
                    }
                }
            }
        }
        
        // Fallback if Python handler fails
        let error_response = AxumResponse::builder()
            .status(StatusCode::INTERNAL_SERVER_ERROR)
            .body(Body::from(r#"{"error":"Python handler failed"}"#))
            .unwrap();
        return Ok(error_response);
    }
    
    // No matching route found - let it fall through to fallback
    Err(StatusCode::NOT_FOUND)
}

// Basic fallback handler for unmatched routes
async fn fallback_handler(State(state): State<AppState>) -> Json<Value> {
    let request_id = state.increment_request_count();
    let uptime = Utc::now().timestamp() - state.start_time.timestamp();
    
    Json(serde_json::json!({
        "error": "Route not found",
        "status": "404",
        "request_count": request_id,
        "uptime_seconds": uptime,
        "version": "2.0.0",
        "rust_core": true
    }))
}

// Build router with dynamic routing support
fn build_router(state: AppState) -> Router {
    Router::new()
        .route("/", any(dynamic_handler))
        .route("/*path", any(dynamic_handler))
        .fallback(fallback_handler)
        .layer(CorsLayer::permissive())
        .with_state(state)
}

// FFI Functions for Python integration

#[no_mangle]
pub extern "C" fn set_python_handler(handler: PythonHandler) -> bool {
    let state = get_app_state();
    let mut python_handler = state.python_handler.lock().unwrap();
    *python_handler = Some(handler);
    println!("🐍 Python handler registered successfully");
    true
}

#[no_mangle]
pub extern "C" fn set_routes(data: *const u8, len: usize) -> bool {
    if data.is_null() || len == 0 {
        return false;
    }
    
    let state = get_app_state();
    
    unsafe {
        let slice = std::slice::from_raw_parts(data, len);
        if let Ok(json_str) = std::str::from_utf8(slice) {
            if let Ok(routes_data) = serde_json::from_str::<Value>(json_str) {
                println!("📍 Processing route definitions...");
                
                // Parse routes by HTTP method
                if let Some(routes_obj) = routes_data.as_object() {
                    for (method, routes_array) in routes_obj {
                        if let Some(routes) = routes_array.as_array() {
                            let mut method_routes = Vec::new();
                            
                            for route_value in routes {
                                if let Ok(route) = serde_json::from_value::<RouteDefinition>(route_value.clone()) {
                                    println!("📋 Route: {} {} -> {}", method, route.path, route.handler_name);
                                    
                                    // Compile route pattern if it has parameters
                                    if route.path.contains('{') {
                                        let pattern = RoutePattern::compile(&route.path);
                                        let pattern_key = format!("{}:{}", method, route.path);
                                        state.route_patterns.insert(pattern_key, pattern);
                                        println!("🔧 Compiled dynamic route pattern: {}", route.path);
                                    }
                                    
                                    method_routes.push(route);
                                }
                            }
                            
                            state.routes.insert(method.clone(), method_routes);
                            println!("✅ Registered {} routes for method {}", routes.len(), method);
                        }
                    }
                    
                    println!("🎉 All routes processed successfully!");
                    return true;
                }
            }
        }
    }
    
    false
}

#[no_mangle]
pub extern "C" fn start_server(production: bool, port: u16) -> bool {
    let rt = match tokio::runtime::Runtime::new() {
        Ok(rt) => rt,
        Err(_) => return false,
    };
    
    rt.block_on(async {
        let state = get_app_state().clone();
        let app = build_router(state);
        
        let addr = if production {
            format!("0.0.0.0:{}", port)
        } else {
            format!("127.0.0.1:{}", port)
        };
        
        let listener = match TcpListener::bind(&addr).await {
            Ok(listener) => listener,
            Err(_) => return false,
        };
        
        println!("🦀 Sufast v2.0 Basic Rust Core listening on {}", addr);
        println!("📊 Basic Features:");
        println!("  ✅ High-performance HTTP server");
        println!("  ✅ CORS support");
        println!("  ✅ Request counting");
        println!("  ✅ Python integration ready");
        
        if let Err(_) = axum::serve(listener, app).await {
            return false;
        }
        
        true
    })
}

#[no_mangle]
pub extern "C" fn get_server_stats() -> *mut c_char {
    let state = get_app_state();
    let request_count = *state.request_count.lock().unwrap();
    let uptime = Utc::now().timestamp() - state.start_time.timestamp();
    
    let stats = serde_json::json!({
        "request_count": request_count,
        "uptime_seconds": uptime,
        "version": "2.0.0",
        "rust_core": true
    });
    
    match CString::new(stats.to_string()) {
        Ok(cstr) => cstr.into_raw(),
        Err(_) => std::ptr::null_mut(),
    }
}

#[no_mangle]
pub extern "C" fn free_string(ptr: *mut c_char) {
    if !ptr.is_null() {
        unsafe {
            drop(CString::from_raw(ptr));
        }
    }
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
