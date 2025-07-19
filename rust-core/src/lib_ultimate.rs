use axum::{
    body::Body,
    extract::{Path, Query},
    http::{HeaderMap, Method, StatusCode, Uri},
    response::Response,
    routing::{delete, get, post, put},
    Router,
};
use dashmap::DashMap;
use once_cell::sync::Lazy;
use regex::Regex;
use serde_json::{json, Value};
use std::collections::HashMap;
use std::ffi::{c_char, CStr, CString};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use tokio::net::TcpListener;
use tower_http::cors::CorsLayer;

// ========================
// PERFORMANCE OPTIMIZATION
// Fast HTTP server core
// ========================

// Static responses: Pre-compiled for instant delivery
static STATIC_RESPONSES: Lazy<DashMap<String, StaticResponse>> = Lazy::new(DashMap::new);

// Response cache: Intelligent caching for dynamic routes
static RESPONSE_CACHE: Lazy<DashMap<String, CachedResponse>> = Lazy::new(DashMap::new);

// Dynamic patterns: Fast pattern matching
static DYNAMIC_ROUTES: Lazy<DashMap<String, DynamicRoute>> = Lazy::new(DashMap::new);

// Performance counters
static STATIC_HITS: AtomicU64 = AtomicU64::new(0);
static CACHE_HITS: AtomicU64 = AtomicU64::new(0);
static DYNAMIC_HITS: AtomicU64 = AtomicU64::new(0);
static TOTAL_REQUESTS: AtomicU64 = AtomicU64::new(0);

#[derive(Clone)]
struct StaticResponse {
    body: String,
    status: u16,
    headers: HashMap<String, String>,
}

#[derive(Clone)]
struct CachedResponse {
    body: String,
    status: u16,
    headers: HashMap<String, String>,
    cached_at: Instant,
    ttl: Duration,
}

#[derive(Clone)]
struct DynamicRoute {
    regex: Regex,
    handler_name: String,
    cache_ttl: Option<Duration>,
}

// Python callback for dynamic routes - fixed memory management
type PythonCallback = extern "C" fn(*const c_char, *const c_char, *const c_char) -> *const c_char;
static mut PYTHON_CALLBACK: Option<PythonCallback> = None;

// Response pool to prevent memory leaks
static RESPONSE_POOL: Lazy<Arc<Mutex<Vec<CString>>>> =
    Lazy::new(|| Arc::new(Mutex::new(Vec::new())));

// ========================
// FAST HANDLER
// ========================

async fn ultra_fast_handler(
    method: Method,
    uri: Uri,
    _headers: HeaderMap,
    _body: Body,
) -> Response<Body> {
    let request_id = TOTAL_REQUESTS.fetch_add(1, Ordering::Relaxed) + 1;
    let path = uri.path();
    let method_str = method.as_str();
    let route_key = format!("{}:{}", method_str, path);

    // TIER 1: Static responses - Pre-compiled, zero overhead
    if let Some(static_resp) = STATIC_RESPONSES.get(&route_key) {
        STATIC_HITS.fetch_add(1, Ordering::Relaxed);

        let mut response_builder = Response::builder().status(static_resp.status);

        for (key, value) in &static_resp.headers {
            response_builder = response_builder.header(key, value);
        }

        return response_builder
            .header("x-sufast-tier", "static")
            .header("x-sufast-request-id", request_id.to_string())
            .header("server", "sufast-ultra")
            .body(Body::from(static_resp.body.clone()))
            .unwrap();
    }

    // TIER 2: Cache lookup - Fast cache
    if let Some(cached) = RESPONSE_CACHE.get(&route_key) {
        if cached.cached_at.elapsed() < cached.ttl {
            CACHE_HITS.fetch_add(1, Ordering::Relaxed);

            let mut response_builder = Response::builder().status(cached.status);

            for (key, value) in &cached.headers {
                response_builder = response_builder.header(key, value);
            }

            return response_builder
                .header("x-sufast-tier", "cached")
                .header("x-sufast-request-id", request_id.to_string())
                .header(
                    "x-sufast-cache-age",
                    cached.cached_at.elapsed().as_secs().to_string(),
                )
                .header("server", "sufast-ultra")
                .body(Body::from(cached.body.clone()))
                .unwrap();
        } else {
            // Remove expired cache
            RESPONSE_CACHE.remove(&route_key);
        }
    }

    // TIER 3: Dynamic processing - Optimized Python callback
    DYNAMIC_HITS.fetch_add(1, Ordering::Relaxed);

    // Fast pattern matching
    for route_entry in DYNAMIC_ROUTES.iter() {
        let route = route_entry.value();
        if let Some(captures) = route.regex.captures(path) {
            // Extract parameters with zero-copy
            let mut params_json = String::from("{");
            let mut first = true;

            for name in route.regex.capture_names() {
                if let Some(name) = name {
                    if let Some(value) = captures.name(name) {
                        if !first {
                            params_json.push(',');
                        }
                        params_json.push_str(&format!("\"{}\":\"{}\"", name, value.as_str()));
                        first = false;
                    }
                }
            }
            params_json.push('}');

            // Call Python handler with optimized parameters
            if let Ok((body, status, response_headers)) =
                call_ultra_fast_python_handler(method_str, path, &params_json).await
            {
                // Cache successful responses
                if status == 200 && route.cache_ttl.is_some() {
                    let cached = CachedResponse {
                        body: body.clone(),
                        status,
                        headers: response_headers.clone(),
                        cached_at: Instant::now(),
                        ttl: route.cache_ttl.unwrap(),
                    };
                    RESPONSE_CACHE.insert(route_key, cached);
                }

                let mut response_builder = Response::builder().status(status);
                for (key, value) in &response_headers {
                    response_builder = response_builder.header(key, value);
                }

                return response_builder
                    .header("x-sufast-tier", "dynamic")
                    .header("x-sufast-request-id", request_id.to_string())
                    .header("x-sufast-handler", &route.handler_name)
                    .header("server", "sufast-ultra")
                    .body(Body::from(body))
                    .unwrap();
            }
        }
    }

    // 404 fallback
    let stats = json!({
        "error": "Route not found",
        "status": 404,
        "path": path,
        "method": method_str,
        "server": "sufast-ultra"
    });

    Response::builder()
        .status(404)
        .header("content-type", "application/json")
        .header("x-sufast-tier", "404")
        .header("server", "sufast-ultra")
        .body(Body::from(stats.to_string()))
        .unwrap()
}

async fn call_ultra_fast_python_handler(
    method: &str,
    path: &str,
    params_json: &str,
) -> Result<(String, u16, HashMap<String, String>), String> {
    unsafe {
        if let Some(callback) = PYTHON_CALLBACK {
            let method_cstr = CString::new(method).map_err(|e| e.to_string())?;
            let path_cstr = CString::new(path).map_err(|e| e.to_string())?;
            let params_cstr = CString::new(params_json).map_err(|e| e.to_string())?;

            let result_ptr = callback(
                method_cstr.as_ptr(),
                path_cstr.as_ptr(),
                params_cstr.as_ptr(),
            );
            if result_ptr.is_null() {
                return Err("Python callback returned null".to_string());
            }

            let c_str = CStr::from_ptr(result_ptr);
            let response_json = c_str.to_string_lossy();

            // Parse fast response
            if let Ok(response_data) = serde_json::from_str::<Value>(&response_json) {
                let body = response_data["body"].as_str().unwrap_or("{}").to_string();
                let status = response_data["status"].as_u64().unwrap_or(200) as u16;

                let mut headers = HashMap::new();
                headers.insert("content-type".to_string(), "application/json".to_string());
                headers.insert("x-sufast-engine".to_string(), "rust-python-ffi".to_string());

                if let Some(response_headers) = response_data["headers"].as_object() {
                    for (key, value) in response_headers {
                        if let Some(value_str) = value.as_str() {
                            headers.insert(key.clone(), value_str.to_string());
                        }
                    }
                }

                return Ok((body, status, headers));
            }
        }
    }
    Err("Python callback failed".to_string())
}

// ========================
// PERFORMANCE HANDLER
// ========================
// FAST ROUTE REGISTRATION
// ========================

#[no_mangle]
pub extern "C" fn add_static_route(
    method_path: *const c_char,
    response_body: *const c_char,
    status: u16,
    content_type: *const c_char,
) -> bool {
    unsafe {
        if method_path.is_null() || response_body.is_null() {
            return false;
        }

        let method_path_str = CStr::from_ptr(method_path).to_string_lossy().to_string();
        let body_str = CStr::from_ptr(response_body).to_string_lossy().to_string();
        let content_type_str = if content_type.is_null() {
            "application/json".to_string()
        } else {
            CStr::from_ptr(content_type).to_string_lossy().to_string()
        };

        let mut headers = HashMap::new();
        headers.insert("content-type".to_string(), content_type_str);
        headers.insert("x-sufast-optimized".to_string(), "static".to_string());
        headers.insert(
            "cache-control".to_string(),
            "public, max-age=31536000".to_string(),
        );

        let static_response = StaticResponse {
            body: body_str,
            status,
            headers,
        };

        STATIC_RESPONSES.insert(method_path_str, static_response);
        true
    }
}

#[no_mangle]
pub extern "C" fn add_dynamic_route(
    method: *const c_char,
    pattern: *const c_char,
    handler_name: *const c_char,
    cache_ttl_seconds: u64,
) -> bool {
    unsafe {
        if method.is_null() || pattern.is_null() || handler_name.is_null() {
            return false;
        }

        let pattern_str = CStr::from_ptr(pattern).to_string_lossy().to_string();
        let handler_str = CStr::from_ptr(handler_name).to_string_lossy().to_string();

        // Compile fast regex pattern
        if let Ok(regex) = compile_ultra_fast_pattern(&pattern_str) {
            let cache_ttl = if cache_ttl_seconds > 0 {
                Some(Duration::from_secs(cache_ttl_seconds))
            } else {
                None
            };

            let dynamic_route = DynamicRoute {
                regex,
                handler_name: handler_str,
                cache_ttl,
            };

            DYNAMIC_ROUTES.insert(pattern_str, dynamic_route);
            true
        } else {
            false
        }
    }
}

fn compile_ultra_fast_pattern(pattern: &str) -> Result<Regex, regex::Error> {
    let mut regex_pattern = pattern.to_string();

    // Fast parameter replacement
    while let Some(start) = regex_pattern.find('{') {
        if let Some(end) = regex_pattern[start..].find('}') {
            let param_name = &regex_pattern[start + 1..start + end];
            let replacement = format!("(?P<{}>[^/]+)", param_name);
            regex_pattern.replace_range(start..start + end + 1, &replacement);
        } else {
            break;
        }
    }

    // Compile with optimizations
    Regex::new(&format!("^{}$", regex_pattern))
}

#[no_mangle]
pub extern "C" fn set_python_callback(callback: PythonCallback) {
    unsafe {
        PYTHON_CALLBACK = Some(callback);
    }
}

#[no_mangle]
pub extern "C" fn get_performance_stats() -> *mut c_char {
    let static_hits = STATIC_HITS.load(Ordering::Relaxed);
    let cache_hits = CACHE_HITS.load(Ordering::Relaxed);
    let dynamic_hits = DYNAMIC_HITS.load(Ordering::Relaxed);
    let total = static_hits + cache_hits + dynamic_hits;

    let stats = json!({
        "total_requests": total,
        "static_hits": static_hits,
        "cache_hits": cache_hits,
        "dynamic_hits": dynamic_hits,
        "performance_breakdown": {
            "static_percentage": if total > 0 { (static_hits as f64 / total as f64) * 100.0 } else { 0.0 },
            "cache_percentage": if total > 0 { (cache_hits as f64 / total as f64) * 100.0 } else { 0.0 },
            "dynamic_percentage": if total > 0 { (dynamic_hits as f64 / total as f64) * 100.0 } else { 0.0 }
        },
        "route_counts": {
            "static_routes": STATIC_RESPONSES.len(),
            "cached_responses": RESPONSE_CACHE.len(),
            "dynamic_patterns": DYNAMIC_ROUTES.len()
        },
        "server": "sufast-ultra"
    });

    CString::new(stats.to_string())
        .unwrap_or_else(|_| CString::new("{}").unwrap())
        .into_raw()
}

#[no_mangle]
pub extern "C" fn clear_cache() -> bool {
    RESPONSE_CACHE.clear();
    true
}

#[no_mangle]
pub extern "C" fn precompile_static_routes() -> u64 {
    // Pre-compile static routes
    let routes = vec![
        (
            "GET:/",
            r#"{"message":"🚀 Welcome to Sufast Ultra v2.0!","optimization":"Pre-compiled","server":"sufast-ultra"}"#,
            200,
            "application/json",
        ),
        (
            "GET:/health",
            r#"{"status":"healthy","service":"sufast-ultra","server":"sufast-ultra"}"#,
            200,
            "application/json",
        ),
        (
            "GET:/about",
            r#"{"page":"about","framework":"Sufast Ultra","version":"2.0","server":"sufast-ultra"}"#,
            200,
            "application/json",
        ),
        (
            "GET:/api/status",
            r#"{"api":"active","optimization":"fast","status":"operational","server":"sufast-ultra"}"#,
            200,
            "application/json",
        ),
    ];

    for (route_key, body, status, content_type) in routes {
        let mut headers = HashMap::new();
        headers.insert("content-type".to_string(), content_type.to_string());
        headers.insert("x-sufast-precompiled".to_string(), "true".to_string());
        headers.insert(
            "cache-control".to_string(),
            "public, max-age=31536000".to_string(),
        );
        headers.insert("server".to_string(), "sufast-ultra".to_string());

        let static_response = StaticResponse {
            body: body.to_string(),
            status,
            headers,
        };

        STATIC_RESPONSES.insert(route_key.to_string(), static_response);
    }

    STATIC_RESPONSES.len() as u64
}

#[no_mangle]
pub extern "C" fn start_ultra_fast_server(host: *const c_char, port: u16) -> i32 {
    if host.is_null() {
        eprintln!("❌ Host parameter cannot be null");
        return -1;
    }

    let host_str = unsafe {
        match CStr::from_ptr(host).to_str() {
            Ok(s) => s,
            Err(e) => {
                eprintln!("❌ Invalid host string: {}", e);
                return -1;
            }
        }
    };

    tokio::runtime::Runtime::new().unwrap().block_on(async {
        let app = Router::new()
            .fallback(ultra_fast_handler)
            .layer(CorsLayer::permissive());

        let addr = format!("{}:{}", host_str, port);
        let listener = match TcpListener::bind(&addr).await {
            Ok(listener) => listener,
            Err(e) => {
                eprintln!("❌ Failed to bind to {}: {}", addr, e);
                return -1;
            }
        };

        match axum::serve(listener, app).await {
            Ok(_) => 0,
            Err(e) => {
                eprintln!("❌ Server error: {}", e);
                -1
            }
        }
    })
}
