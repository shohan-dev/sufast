// Enhanced request handling with full HTTP support

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HttpRequest {
    pub method: String,
    pub path: String,
    pub headers: HashMap<String, String>,
    pub body: String,
    pub query_string: String,
    pub query_params: HashMap<String, String>,
    pub path_params: HashMap<String, String>,
    pub content_type: String,
    pub content_length: usize,
    pub user_agent: String,
    pub remote_addr: String,
    pub request_id: u64,
    pub timestamp: DateTime<Utc>,
}

impl HttpRequest {
    pub fn new() -> Self {
        Self {
            method: String::new(),
            path: String::new(),
            headers: HashMap::new(),
            body: String::new(),
            query_string: String::new(),
            query_params: HashMap::new(),
            path_params: HashMap::new(),
            content_type: String::new(),
            content_length: 0,
            user_agent: String::new(),
            remote_addr: String::new(),
            request_id: 0,
            timestamp: Utc::now(),
        }
    }
    
    pub fn get_header(&self, name: &str) -> Option<&String> {
        self.headers.get(&name.to_lowercase())
    }
    
    pub fn has_header(&self, name: &str) -> bool {
        self.headers.contains_key(&name.to_lowercase())
    }
    
    pub fn get_query_param(&self, name: &str) -> Option<&String> {
        self.query_params.get(name)
    }
    
    pub fn get_path_param(&self, name: &str) -> Option<&String> {
        self.path_params.get(name)
    }
    
    pub fn is_json(&self) -> bool {
        self.content_type.contains("application/json")
    }
    
    pub fn is_form(&self) -> bool {
        self.content_type.contains("application/x-www-form-urlencoded")
    }
    
    pub fn is_multipart(&self) -> bool {
        self.content_type.contains("multipart/form-data")
    }
    
    pub fn is_secure(&self) -> bool {
        self.get_header("x-forwarded-proto") == Some(&"https".to_string()) ||
        self.get_header("x-forwarded-ssl") == Some(&"on".to_string())
    }
    
    pub fn parse_json<T>(&self) -> Result<T, serde_json::Error>
    where
        T: for<'de> Deserialize<'de>,
    {
        serde_json::from_str(&self.body)
    }
    
    pub fn parse_form(&self) -> Result<HashMap<String, String>, serde_urlencoded::de::Error> {
        serde_urlencoded::from_str(&self.body)
    }
    
    pub fn get_cookies(&self) -> HashMap<String, String> {
        let mut cookies = HashMap::new();
        
        if let Some(cookie_header) = self.get_header("cookie") {
            for cookie_pair in cookie_header.split(';') {
                let parts: Vec<&str> = cookie_pair.trim().splitn(2, '=').collect();
                if parts.len() == 2 {
                    cookies.insert(parts[0].to_string(), parts[1].to_string());
                }
            }
        }
        
        cookies
    }
    
    pub fn get_authorization(&self) -> Option<String> {
        self.get_header("authorization").cloned()
    }
    
    pub fn get_bearer_token(&self) -> Option<String> {
        if let Some(auth) = self.get_authorization() {
            if auth.starts_with("Bearer ") {
                return Some(auth[7..].to_string());
            }
        }
        None
    }
    
    pub fn get_basic_auth(&self) -> Option<(String, String)> {
        if let Some(auth) = self.get_authorization() {
            if auth.starts_with("Basic ") {
                if let Ok(decoded) = base64::decode(&auth[6..]) {
                    if let Ok(credentials) = String::from_utf8(decoded) {
                        let parts: Vec<&str> = credentials.splitn(2, ':').collect();
                        if parts.len() == 2 {
                            return Some((parts[0].to_string(), parts[1].to_string()));
                        }
                    }
                }
            }
        }
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_request_creation() {
        let request = HttpRequest::new();
        assert_eq!(request.method, "");
        assert_eq!(request.path, "");
        assert_eq!(request.request_id, 0);
    }

    #[test]
    fn test_header_access() {
        let mut request = HttpRequest::new();
        request.headers.insert("content-type".to_string(), "application/json".to_string());
        
        assert!(request.has_header("content-type"));
        assert_eq!(request.get_header("content-type"), Some(&"application/json".to_string()));
        assert!(request.is_json());
    }

    #[test]
    fn test_cookie_parsing() {
        let mut request = HttpRequest::new();
        request.headers.insert("cookie".to_string(), "session=abc123; user=john".to_string());
        
        let cookies = request.get_cookies();
        assert_eq!(cookies.get("session"), Some(&"abc123".to_string()));
        assert_eq!(cookies.get("user"), Some(&"john".to_string()));
    }

    #[test]
    fn test_bearer_token() {
        let mut request = HttpRequest::new();
        request.headers.insert("authorization".to_string(), "Bearer abc123xyz".to_string());
        
        assert_eq!(request.get_bearer_token(), Some("abc123xyz".to_string()));
    }

    #[test]
    fn test_json_parsing() {
        let mut request = HttpRequest::new();
        request.body = r#"{"name": "John", "age": 30}"#.to_string();
        
        #[derive(Deserialize)]
        struct TestData {
            name: String,
            age: u32,
        }
        
        let parsed: Result<TestData, _> = request.parse_json();
        assert!(parsed.is_ok());
        
        let data = parsed.unwrap();
        assert_eq!(data.name, "John");
        assert_eq!(data.age, 30);
    }
}
