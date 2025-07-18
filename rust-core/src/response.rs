// Enhanced response handling with full HTTP support

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HttpResponse {
    pub status: u16,
    pub headers: HashMap<String, String>,
    pub body: String,
}

impl HttpResponse {
    pub fn new() -> Self {
        Self {
            status: 200,
            headers: HashMap::new(),
            body: String::new(),
        }
    }

    pub fn json(data: &serde_json::Value) -> Self {
        let mut response = Self::new();
        response
            .headers
            .insert("content-type".to_string(), "application/json".to_string());
        response.body = data.to_string();
        response
    }

    pub fn html(content: &str) -> Self {
        let mut response = Self::new();
        response.headers.insert(
            "content-type".to_string(),
            "text/html; charset=utf-8".to_string(),
        );
        response.body = content.to_string();
        response
    }

    pub fn text(content: &str) -> Self {
        let mut response = Self::new();
        response.headers.insert(
            "content-type".to_string(),
            "text/plain; charset=utf-8".to_string(),
        );
        response.body = content.to_string();
        response
    }

    pub fn redirect(location: &str) -> Self {
        let mut response = Self::new();
        response.status = 302;
        response
            .headers
            .insert("location".to_string(), location.to_string());
        response
    }

    pub fn file(content: Vec<u8>, content_type: &str, filename: Option<&str>) -> Self {
        let mut response = Self::new();
        response
            .headers
            .insert("content-type".to_string(), content_type.to_string());

        if let Some(name) = filename {
            response.headers.insert(
                "content-disposition".to_string(),
                format!("attachment; filename=\"{}\"", name),
            );
        }

        // Convert binary content to base64 for JSON transport
        response.body = base64::encode(content);
        response
            .headers
            .insert("x-binary-content".to_string(), "base64".to_string());
        response
    }

    pub fn with_status(mut self, status: u16) -> Self {
        self.status = status;
        self
    }

    pub fn with_header(mut self, name: &str, value: &str) -> Self {
        self.headers.insert(name.to_lowercase(), value.to_string());
        self
    }

    pub fn with_cookie(mut self, name: &str, value: &str, options: Option<CookieOptions>) -> Self {
        let mut cookie = format!("{}={}", name, value);

        if let Some(opts) = options {
            if let Some(max_age) = opts.max_age {
                cookie.push_str(&format!("; Max-Age={}", max_age));
            }
            if let Some(domain) = opts.domain {
                cookie.push_str(&format!("; Domain={}", domain));
            }
            if let Some(path) = opts.path {
                cookie.push_str(&format!("; Path={}", path));
            }
            if opts.secure {
                cookie.push_str("; Secure");
            }
            if opts.http_only {
                cookie.push_str("; HttpOnly");
            }
            if let Some(same_site) = opts.same_site {
                cookie.push_str(&format!("; SameSite={}", same_site));
            }
        }

        // Handle multiple Set-Cookie headers
        let header_name = "set-cookie".to_string();
        if let Some(existing) = self.headers.get(&header_name) {
            self.headers
                .insert(header_name, format!("{}, {}", existing, cookie));
        } else {
            self.headers.insert(header_name, cookie);
        }

        self
    }

    pub fn with_cors(mut self) -> Self {
        self.headers
            .insert("access-control-allow-origin".to_string(), "*".to_string());
        self.headers.insert(
            "access-control-allow-methods".to_string(),
            "GET, POST, PUT, DELETE, OPTIONS".to_string(),
        );
        self.headers
            .insert("access-control-allow-headers".to_string(), "*".to_string());
        self
    }

    pub fn with_cache_control(mut self, directive: &str) -> Self {
        self.headers
            .insert("cache-control".to_string(), directive.to_string());
        self
    }

    pub fn no_cache(mut self) -> Self {
        self.headers.insert(
            "cache-control".to_string(),
            "no-cache, no-store, must-revalidate".to_string(),
        );
        self.headers
            .insert("pragma".to_string(), "no-cache".to_string());
        self.headers.insert("expires".to_string(), "0".to_string());
        self
    }
}

#[derive(Debug, Clone)]
pub struct CookieOptions {
    pub max_age: Option<i64>,
    pub domain: Option<String>,
    pub path: Option<String>,
    pub secure: bool,
    pub http_only: bool,
    pub same_site: Option<String>, // "Strict", "Lax", or "None"
}

impl Default for CookieOptions {
    fn default() -> Self {
        Self {
            max_age: None,
            domain: None,
            path: Some("/".to_string()),
            secure: false,
            http_only: true,
            same_site: Some("Lax".to_string()),
        }
    }
}

// Common response builders
impl HttpResponse {
    pub fn ok() -> Self {
        Self::new()
    }

    pub fn created() -> Self {
        Self::new().with_status(201)
    }

    pub fn no_content() -> Self {
        Self::new().with_status(204)
    }

    pub fn bad_request(message: &str) -> Self {
        Self::json(&serde_json::json!({"error": message})).with_status(400)
    }

    pub fn unauthorized(message: &str) -> Self {
        Self::json(&serde_json::json!({"error": message})).with_status(401)
    }

    pub fn forbidden(message: &str) -> Self {
        Self::json(&serde_json::json!({"error": message})).with_status(403)
    }

    pub fn not_found(message: &str) -> Self {
        Self::json(&serde_json::json!({"error": message})).with_status(404)
    }

    pub fn method_not_allowed(message: &str) -> Self {
        Self::json(&serde_json::json!({"error": message})).with_status(405)
    }

    pub fn conflict(message: &str) -> Self {
        Self::json(&serde_json::json!({"error": message})).with_status(409)
    }

    pub fn unprocessable_entity(message: &str) -> Self {
        Self::json(&serde_json::json!({"error": message})).with_status(422)
    }

    pub fn too_many_requests(message: &str) -> Self {
        Self::json(&serde_json::json!({"error": message})).with_status(429)
    }

    pub fn internal_server_error(message: &str) -> Self {
        Self::json(&serde_json::json!({"error": message})).with_status(500)
    }

    pub fn not_implemented(message: &str) -> Self {
        Self::json(&serde_json::json!({"error": message})).with_status(501)
    }

    pub fn service_unavailable(message: &str) -> Self {
        Self::json(&serde_json::json!({"error": message})).with_status(503)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_json_response() {
        let data = serde_json::json!({"message": "Hello, World!"});
        let response = HttpResponse::json(&data);

        assert_eq!(response.status, 200);
        assert_eq!(
            response.headers.get("content-type"),
            Some(&"application/json".to_string())
        );
        assert!(response.body.contains("Hello, World!"));
    }

    #[test]
    fn test_html_response() {
        let response = HttpResponse::html("<h1>Hello</h1>");

        assert_eq!(response.status, 200);
        assert_eq!(
            response.headers.get("content-type"),
            Some(&"text/html; charset=utf-8".to_string())
        );
        assert_eq!(response.body, "<h1>Hello</h1>");
    }

    #[test]
    fn test_redirect_response() {
        let response = HttpResponse::redirect("/home");

        assert_eq!(response.status, 302);
        assert_eq!(response.headers.get("location"), Some(&"/home".to_string()));
    }

    #[test]
    fn test_response_chaining() {
        let response = HttpResponse::ok()
            .with_status(201)
            .with_header("x-custom", "value")
            .with_cors();

        assert_eq!(response.status, 201);
        assert_eq!(response.headers.get("x-custom"), Some(&"value".to_string()));
        assert_eq!(
            response.headers.get("access-control-allow-origin"),
            Some(&"*".to_string())
        );
    }

    #[test]
    fn test_cookie_setting() {
        let options = CookieOptions {
            max_age: Some(3600),
            secure: true,
            ..Default::default()
        };

        let response = HttpResponse::ok().with_cookie("session", "abc123", Some(options));

        let cookie_header = response.headers.get("set-cookie").unwrap();
        assert!(cookie_header.contains("session=abc123"));
        assert!(cookie_header.contains("Max-Age=3600"));
        assert!(cookie_header.contains("Secure"));
    }

    #[test]
    fn test_error_responses() {
        let response = HttpResponse::not_found("Resource not found");
        assert_eq!(response.status, 404);
        assert!(response.body.contains("Resource not found"));

        let response = HttpResponse::internal_server_error("Something went wrong");
        assert_eq!(response.status, 500);
        assert!(response.body.contains("Something went wrong"));
    }
}
