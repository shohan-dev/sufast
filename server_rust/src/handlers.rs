// src/handlers.rs

use crate::routes::get_routes;
use axum::{
    body::{boxed, Body},
    http::{Request, StatusCode},
    response::{IntoResponse, Response},
};
use std::collections::HashMap; // <-- Import the helper that returns Option<&SharedRoutes>

/// Match a request path like `/user/Bob` against a pattern `/user/{name}`
/// Returns a map of parameters if matched (e.g., `{ "name": "Bob" }`)
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

/// Handles all incoming HTTP requests.
/// 1. Looks up exact (static) match first.
/// 2. If not found, tries each dynamic pattern in turn (e.g. `/user/{name}`).
/// 3. If still not found, returns a JSON‐formatted 404 error.
///
/// Always returns a JSON response (with `Content-Type: application/json`).
pub async fn dynamic_handler(req: Request<Body>) -> impl IntoResponse {
    let method = req.method().clone();
    let path = req.uri().path().to_string();

    // Retrieve the globally shared routes (if they've been initialized)
    if let Some(routes_arc) = get_routes() {
        // Acquire a read lock on the inner HashMap<Method, HashMap<path, response>>
        if let Ok(read_guard) = routes_arc.read() {
            // Attempt to get the map for this HTTP method
            if let Some(inner_map) = read_guard.get(&method) {
                // 1. Exact (static) match?
                if let Some(static_response) = inner_map.get(&path) {
                    return json_response(200, static_response.clone());
                }

                // 2. Dynamic (pattern) match?
                for (pattern, response_template) in inner_map.iter() {
                    if let Some(captures) = match_path(pattern, &path) {
                        // Replace all `{param}` placeholders in the stored template
                        let mut dyn_resp = response_template.clone();
                        for (key, value) in captures {
                            dyn_resp = dyn_resp.replace(&format!("{{{}}}", key), &value);
                        }
                        return json_response(200, dyn_resp);
                    }
                }
            }
        }
        // If the read lock itself failed (poisoned lock, etc.), fall through to 404 response
    }

    // 3. Not found → return 404 JSON error
    let error_body = format!(
        r#"{{"error":"Route not found","method":"{}","path":"{}"}}"#,
        method, path
    );
    json_response(404, error_body)
}

/// Helper to build a JSON response with given status code and raw body string.
/// Always sets `Content-Type: application/json`.
fn json_response(status_code: u16, body: String) -> Response {
    // Convert u16 to a valid StatusCode (default to 200 if invalid)
    let status = StatusCode::from_u16(status_code).unwrap_or(StatusCode::OK);
    Response::builder()
        .status(status)
        .header("Content-Type", "application/json")
        .body(boxed(Body::from(body)))
        .unwrap()
}
