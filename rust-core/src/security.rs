// Security headers and utilities
use axum::response::Response;
use axum::http::{HeaderMap, HeaderValue};

#[derive(Debug, Clone)]
pub struct SecurityHeaders {
    pub enable_hsts: bool,
    pub enable_xframe: bool,
    pub enable_xcontent: bool,
    pub enable_xss: bool,
    pub enable_csp: bool,
    pub csp_policy: String,
    pub hsts_max_age: u32,
}

impl SecurityHeaders {
    pub fn new() -> Self {
        Self {
            enable_hsts: true,
            enable_xframe: true,
            enable_xcontent: true,
            enable_xss: true,
            enable_csp: true,
            csp_policy: "default-src 'self'".to_string(),
            hsts_max_age: 31536000, // 1 year
        }
    }

    pub fn apply_headers(&self, mut response: Response) -> Response {
        let headers = response.headers_mut();
        
        if self.enable_hsts {
            headers.insert(
                "Strict-Transport-Security",
                HeaderValue::from_str(&format!("max-age={}", self.hsts_max_age)).unwrap()
            );
        }
        
        if self.enable_xframe {
            headers.insert("X-Frame-Options", HeaderValue::from_static("DENY"));
        }
        
        if self.enable_xcontent {
            headers.insert("X-Content-Type-Options", HeaderValue::from_static("nosniff"));
        }
        
        if self.enable_xss {
            headers.insert("X-XSS-Protection", HeaderValue::from_static("1; mode=block"));
        }
        
        if self.enable_csp {
            headers.insert(
                "Content-Security-Policy",
                HeaderValue::from_str(&self.csp_policy).unwrap()
            );
        }
        
        response
    }
}
