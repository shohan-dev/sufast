// Advanced middleware system with security, rate limiting, and validation

use serde::{Deserialize, Serialize};
use serde_json::{Value, Map};
use std::collections::HashMap;
use axum::response::Response;
use crate::request::HttpRequest;
use crate::response::HttpResponse;
use async_trait::async_trait;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MiddlewareDefinition {
    pub name: String,
    pub config: Map<String, Value>,
    pub enabled: bool,
    pub order: i32,
}

#[derive(Debug, Clone)]
pub struct MiddlewareChain {
    pub middleware: Vec<MiddlewareDefinition>,
}

impl MiddlewareChain {
    pub fn new() -> Self {
        Self {
            middleware: Vec::new(),
        }
    }
    
    pub fn add(&mut self, middleware: MiddlewareDefinition) {
        self.middleware.push(middleware);
        // Sort by order
        self.middleware.sort_by_key(|m| m.order);
    }
    
    pub fn clear(&mut self) {
        self.middleware.clear();
    }
}

#[async_trait]
pub trait Middleware: Send + Sync {
    async fn process(&self, request: &HttpRequest) -> Result<(), Response>;
}

// CORS Middleware
pub struct CorsMiddleware {
    pub allow_origins: Vec<String>,
    pub allow_methods: Vec<String>,
    pub allow_headers: Vec<String>,
    pub max_age: Option<u32>,
}

impl CorsMiddleware {
    pub fn new(config: &Map<String, Value>) -> Self {
        let allow_origins = config.get("allow_origins")
            .and_then(|v| v.as_array())
            .map(|arr| arr.iter().filter_map(|v| v.as_str().map(|s| s.to_string())).collect())
            .unwrap_or_else(|| vec!["*".to_string()]);
            
        let allow_methods = config.get("allow_methods")
            .and_then(|v| v.as_array())
            .map(|arr| arr.iter().filter_map(|v| v.as_str().map(|s| s.to_string())).collect())
            .unwrap_or_else(|| vec!["GET".to_string(), "POST".to_string(), "PUT".to_string(), "DELETE".to_string(), "OPTIONS".to_string()]);
            
        let allow_headers = config.get("allow_headers")
            .and_then(|v| v.as_array())
            .map(|arr| arr.iter().filter_map(|v| v.as_str().map(|s| s.to_string())).collect())
            .unwrap_or_else(|| vec!["*".to_string()]);
            
        let max_age = config.get("max_age")
            .and_then(|v| v.as_u64())
            .map(|v| v as u32);
        
        Self {
            allow_origins,
            allow_methods,
            allow_headers,
            max_age,
        }
    }
}

#[async_trait]
impl Middleware for CorsMiddleware {
    async fn process(&self, request: &HttpRequest) -> Result<(), Response> {
        // CORS is handled in response headers, not request validation
        Ok(())
    }
}

// Rate Limiting Middleware
pub struct RateLimitingMiddleware {
    pub requests_per_minute: u32,
    pub window_seconds: u64,
}

impl RateLimitingMiddleware {
    pub fn new(config: &Map<String, Value>) -> Self {
        let requests_per_minute = config.get("requests_per_minute")
            .and_then(|v| v.as_u64())
            .unwrap_or(100) as u32;
            
        let window_seconds = config.get("window_seconds")
            .and_then(|v| v.as_u64())
            .unwrap_or(60);
        
        Self {
            requests_per_minute,
            window_seconds,
        }
    }
}

#[async_trait]
impl Middleware for RateLimitingMiddleware {
    async fn process(&self, request: &HttpRequest) -> Result<(), Response> {
        // Rate limiting is handled at the server level
        Ok(())
    }
}

// Authentication Middleware
pub struct AuthMiddleware {
    pub secret_key: String,
    pub exclude_paths: Vec<String>,
    pub header_name: String,
}

impl AuthMiddleware {
    pub fn new(config: &Map<String, Value>) -> Self {
        let secret_key = config.get("secret_key")
            .and_then(|v| v.as_str())
            .unwrap_or("default-secret")
            .to_string();
            
        let exclude_paths = config.get("exclude_paths")
            .and_then(|v| v.as_array())
            .map(|arr| arr.iter().filter_map(|v| v.as_str().map(|s| s.to_string())).collect())
            .unwrap_or_default();
            
        let header_name = config.get("header_name")
            .and_then(|v| v.as_str())
            .unwrap_or("authorization")
            .to_string();
        
        Self {
            secret_key,
            exclude_paths,
            header_name,
        }
    }
}

#[async_trait]
impl Middleware for AuthMiddleware {
    async fn process(&self, request: &HttpRequest) -> Result<(), Response> {
        // Skip authentication for excluded paths
        if self.exclude_paths.contains(&request.path) {
            return Ok(());
        }
        
        // Check for authorization header
        if let Some(auth_header) = request.get_header(&self.header_name) {
            if auth_header.starts_with("Bearer ") {
                let token = &auth_header[7..];
                
                // Validate JWT token (simplified validation)
                if self.validate_token(token) {
                    return Ok(());
                }
            }
        }
        
        // Return unauthorized response
        let response = HttpResponse::unauthorized("Authentication required");
        Err(self.convert_to_axum_response(response))
    }
}

impl AuthMiddleware {
    fn validate_token(&self, token: &str) -> bool {
        // Simplified token validation - in production, use proper JWT validation
        !token.is_empty() && token.len() > 10
    }
    
    fn convert_to_axum_response(&self, http_response: HttpResponse) -> Response {
        let mut response = Response::builder()
            .status(http_response.status);
            
        for (key, value) in &http_response.headers {
            response = response.header(key, value);
        }
        
        response.body(axum::body::Body::from(http_response.body)).unwrap()
    }
}

// Security Headers Middleware
pub struct SecurityHeadersMiddleware {
    pub hsts_max_age: u32,
    pub content_type_options: bool,
    pub frame_options: String,
    pub xss_protection: bool,
}

impl SecurityHeadersMiddleware {
    pub fn new(config: &Map<String, Value>) -> Self {
        let hsts_max_age = config.get("hsts_max_age")
            .and_then(|v| v.as_u64())
            .unwrap_or(31536000) as u32;
            
        let content_type_options = config.get("content_type_options")
            .and_then(|v| v.as_bool())
            .unwrap_or(true);
            
        let frame_options = config.get("frame_options")
            .and_then(|v| v.as_str())
            .unwrap_or("DENY")
            .to_string();
            
        let xss_protection = config.get("xss_protection")
            .and_then(|v| v.as_bool())
            .unwrap_or(true);
        
        Self {
            hsts_max_age,
            content_type_options,
            frame_options,
            xss_protection,
        }
    }
}

#[async_trait]
impl Middleware for SecurityHeadersMiddleware {
    async fn process(&self, request: &HttpRequest) -> Result<(), Response> {
        // Security headers are added to responses, not request validation
        Ok(())
    }
}

// Logging Middleware
pub struct LoggingMiddleware {
    pub log_level: String,
    pub include_body: bool,
    pub include_headers: bool,
}

impl LoggingMiddleware {
    pub fn new(config: &Map<String, Value>) -> Self {
        let log_level = config.get("log_level")
            .and_then(|v| v.as_str())
            .unwrap_or("info")
            .to_string();
            
        let include_body = config.get("include_body")
            .and_then(|v| v.as_bool())
            .unwrap_or(false);
            
        let include_headers = config.get("include_headers")
            .and_then(|v| v.as_bool())
            .unwrap_or(true);
        
        Self {
            log_level,
            include_body,
            include_headers,
        }
    }
}

#[async_trait]
impl Middleware for LoggingMiddleware {
    async fn process(&self, request: &HttpRequest) -> Result<(), Response> {
        // Log the request
        let mut log_msg = format!("{} {} from {}", 
            request.method, 
            request.path, 
            request.remote_addr
        );
        
        if self.include_headers && !request.headers.is_empty() {
            log_msg.push_str(&format!(" Headers: {:?}", request.headers));
        }
        
        if self.include_body && !request.body.is_empty() {
            log_msg.push_str(&format!(" Body: {}", request.body));
        }
        
        match self.log_level.as_str() {
            "debug" => tracing::debug!("{}", log_msg),
            "info" => tracing::info!("{}", log_msg),
            "warn" => tracing::warn!("{}", log_msg),
            "error" => tracing::error!("{}", log_msg),
            _ => tracing::info!("{}", log_msg),
        }
        
        Ok(())
    }
}

// Validation Middleware
pub struct ValidationMiddleware {
    pub max_content_length: usize,
    pub allowed_content_types: Vec<String>,
    pub required_headers: Vec<String>,
}

impl ValidationMiddleware {
    pub fn new(config: &Map<String, Value>) -> Self {
        let max_content_length = config.get("max_content_length")
            .and_then(|v| v.as_u64())
            .unwrap_or(10 * 1024 * 1024) as usize; // 10MB default
            
        let allowed_content_types = config.get("allowed_content_types")
            .and_then(|v| v.as_array())
            .map(|arr| arr.iter().filter_map(|v| v.as_str().map(|s| s.to_string())).collect())
            .unwrap_or_default();
            
        let required_headers = config.get("required_headers")
            .and_then(|v| v.as_array())
            .map(|arr| arr.iter().filter_map(|v| v.as_str().map(|s| s.to_string())).collect())
            .unwrap_or_default();
        
        Self {
            max_content_length,
            allowed_content_types,
            required_headers,
        }
    }
}

#[async_trait]
impl Middleware for ValidationMiddleware {
    async fn process(&self, request: &HttpRequest) -> Result<(), Response> {
        // Check content length
        if request.content_length > self.max_content_length {
            let response = HttpResponse::bad_request(&format!("Content too large. Max allowed: {} bytes", self.max_content_length));
            return Err(self.convert_to_axum_response(response));
        }
        
        // Check content type if specified
        if !self.allowed_content_types.is_empty() && !request.content_type.is_empty() {
            let is_allowed = self.allowed_content_types.iter()
                .any(|ct| request.content_type.starts_with(ct));
                
            if !is_allowed {
                let response = HttpResponse::bad_request("Invalid content type");
                return Err(self.convert_to_axum_response(response));
            }
        }
        
        // Check required headers
        for required_header in &self.required_headers {
            if !request.has_header(required_header) {
                let response = HttpResponse::bad_request(&format!("Missing required header: {}", required_header));
                return Err(self.convert_to_axum_response(response));
            }
        }
        
        Ok(())
    }
}

impl ValidationMiddleware {
    fn convert_to_axum_response(&self, http_response: HttpResponse) -> Response {
        let mut response = Response::builder()
            .status(http_response.status);
            
        for (key, value) in &http_response.headers {
            response = response.header(key, value);
        }
        
        response.body(axum::body::Body::from(http_response.body)).unwrap()
    }
}

// Execute middleware chain
pub async fn execute_middleware(chain: &MiddlewareChain, request: &HttpRequest) -> Result<(), Response> {
    for middleware_def in &chain.middleware {
        if !middleware_def.enabled {
            continue;
        }
        
        match middleware_def.name.as_str() {
            "cors" => {
                let middleware = CorsMiddleware::new(&middleware_def.config);
                middleware.process(request).await?;
            }
            "rate_limiting" => {
                let middleware = RateLimitingMiddleware::new(&middleware_def.config);
                middleware.process(request).await?;
            }
            "auth" => {
                let middleware = AuthMiddleware::new(&middleware_def.config);
                middleware.process(request).await?;
            }
            "security_headers" => {
                let middleware = SecurityHeadersMiddleware::new(&middleware_def.config);
                middleware.process(request).await?;
            }
            "logging" => {
                let middleware = LoggingMiddleware::new(&middleware_def.config);
                middleware.process(request).await?;
            }
            "validation" => {
                let middleware = ValidationMiddleware::new(&middleware_def.config);
                middleware.process(request).await?;
            }
            _ => {
                tracing::warn!("Unknown middleware: {}", middleware_def.name);
            }
        }
    }
    
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_middleware_chain() {
        let mut chain = MiddlewareChain::new();
        
        let cors_middleware = MiddlewareDefinition {
            name: "cors".to_string(),
            config: Map::new(),
            enabled: true,
            order: 1,
        };
        
        let auth_middleware = MiddlewareDefinition {
            name: "auth".to_string(),
            config: Map::new(),
            enabled: true,
            order: 2,
        };
        
        chain.add(auth_middleware);
        chain.add(cors_middleware);
        
        // Should be sorted by order
        assert_eq!(chain.middleware[0].name, "cors");
        assert_eq!(chain.middleware[1].name, "auth");
    }

    #[test]
    fn test_cors_middleware_config() {
        let config = json!({
            "allow_origins": ["https://example.com"],
            "allow_methods": ["GET", "POST"],
            "max_age": 3600
        });
        
        let cors = CorsMiddleware::new(config.as_object().unwrap());
        assert_eq!(cors.allow_origins, vec!["https://example.com"]);
        assert_eq!(cors.allow_methods, vec!["GET", "POST"]);
        assert_eq!(cors.max_age, Some(3600));
    }

    #[test]
    fn test_validation_middleware_config() {
        let config = json!({
            "max_content_length": 1024,
            "allowed_content_types": ["application/json"],
            "required_headers": ["authorization"]
        });
        
        let validation = ValidationMiddleware::new(config.as_object().unwrap());
        assert_eq!(validation.max_content_length, 1024);
        assert_eq!(validation.allowed_content_types, vec!["application/json"]);
        assert_eq!(validation.required_headers, vec!["authorization"]);
    }
}
