// Template engine with basic and Jinja2-like support

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use serde_json::Value;

#[derive(Debug, Clone)]
pub struct TemplateEngine {
    pub template_dir: PathBuf,
    pub cache_enabled: bool,
    pub auto_escape: bool,
}

impl TemplateEngine {
    pub fn new(template_dir: &str) -> Self {
        Self {
            template_dir: PathBuf::from(template_dir),
            cache_enabled: true,
            auto_escape: true,
        }
    }
    
    pub fn render(&self, template_name: &str, context: &HashMap<String, Value>) -> Result<String, TemplateError> {
        let template_path = self.template_dir.join(template_name);
        
        if !template_path.exists() {
            return Err(TemplateError::TemplateNotFound(template_name.to_string()));
        }
        
        let template_content = std::fs::read_to_string(&template_path)
            .map_err(|e| TemplateError::IoError(e))?;
        
        self.render_string(&template_content, context)
    }
    
    pub fn render_string(&self, template: &str, context: &HashMap<String, Value>) -> Result<String, TemplateError> {
        let mut result = template.to_string();
        
        // Simple variable substitution: {{ variable }}
        let var_regex = regex::Regex::new(r"\{\{\s*(\w+)\s*\}\}").unwrap();
        result = var_regex.replace_all(&result, |caps: &regex::Captures| {
            let var_name = &caps[1];
            if let Some(value) = context.get(var_name) {
                self.value_to_string(value)
            } else {
                format!("{{{{ {} }}}}", var_name) // Keep original if not found
            }
        }).to_string();
        
        // Simple conditional: {% if condition %} ... {% endif %}
        let if_regex = regex::Regex::new(r"\{%\s*if\s+(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}").unwrap();
        result = if_regex.replace_all(&result, |caps: &regex::Captures| {
            let condition = &caps[1];
            let content = &caps[2];
            
            if let Some(value) = context.get(condition) {
                if self.is_truthy(value) {
                    content.to_string()
                } else {
                    String::new()
                }
            } else {
                String::new()
            }
        }).to_string();
        
        // Simple loop: {% for item in items %} ... {% endfor %}
        let for_regex = regex::Regex::new(r"\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}").unwrap();
        result = for_regex.replace_all(&result, |caps: &regex::Captures| {
            let item_name = &caps[1];
            let array_name = &caps[2];
            let template_content = &caps[3];
            
            if let Some(Value::Array(items)) = context.get(array_name) {
                let mut loop_result = String::new();
                for item in items {
                    let mut loop_context = context.clone();
                    loop_context.insert(item_name.to_string(), item.clone());
                    
                    // Recursively render the loop content
                    if let Ok(rendered) = self.render_string(template_content, &loop_context) {
                        loop_result.push_str(&rendered);
                    }
                }
                loop_result
            } else {
                String::new()
            }
        }).to_string();
        
        // Auto-escape HTML if enabled
        if self.auto_escape {
            result = self.escape_html(&result);
        }
        
        Ok(result)
    }
    
    fn value_to_string(&self, value: &Value) -> String {
        match value {
            Value::String(s) => s.clone(),
            Value::Number(n) => n.to_string(),
            Value::Bool(b) => b.to_string(),
            Value::Array(arr) => format!("[{}]", arr.len()),
            Value::Object(obj) => format!("{{{}}}", obj.len()),
            Value::Null => "".to_string(),
        }
    }
    
    fn is_truthy(&self, value: &Value) -> bool {
        match value {
            Value::Bool(b) => *b,
            Value::String(s) => !s.is_empty(),
            Value::Number(n) => n.as_f64().unwrap_or(0.0) != 0.0,
            Value::Array(arr) => !arr.is_empty(),
            Value::Object(obj) => !obj.is_empty(),
            Value::Null => false,
        }
    }
    
    fn escape_html(&self, input: &str) -> String {
        input
            .replace('&', "&amp;")
            .replace('<', "&lt;")
            .replace('>', "&gt;")
            .replace('"', "&quot;")
            .replace('\'', "&#x27;")
    }
    
    pub fn with_cache(mut self, enabled: bool) -> Self {
        self.cache_enabled = enabled;
        self
    }
    
    pub fn with_auto_escape(mut self, enabled: bool) -> Self {
        self.auto_escape = enabled;
        self
    }
}

#[derive(Debug, thiserror::Error)]
pub enum TemplateError {
    #[error("Template not found: {0}")]
    TemplateNotFound(String),
    #[error("IO error: {0}")]
    IoError(std::io::Error),
    #[error("Render error: {0}")]
    RenderError(String),
}

// Static file handler
pub struct StaticFileHandler {
    pub static_dirs: HashMap<String, PathBuf>,
    pub cache_max_age: u32,
    pub enable_etag: bool,
}

impl StaticFileHandler {
    pub fn new() -> Self {
        Self {
            static_dirs: HashMap::new(),
            cache_max_age: 3600, // 1 hour
            enable_etag: true,
        }
    }
    
    pub fn add_directory(&mut self, route_prefix: &str, directory: &str) {
        self.static_dirs.insert(route_prefix.to_string(), PathBuf::from(directory));
    }
    
    pub fn get_file_path(&self, request_path: &str) -> Option<PathBuf> {
        for (prefix, dir) in &self.static_dirs {
            if request_path.starts_with(prefix) {
                let relative_path = request_path.strip_prefix(prefix).unwrap_or("");
                let relative_path = relative_path.trim_start_matches('/');
                
                // Security check
                if relative_path.contains("..") {
                    return None;
                }
                
                return Some(dir.join(relative_path));
            }
        }
        None
    }
    
    pub fn get_content_type(&self, file_path: &Path) -> String {
        match file_path.extension().and_then(|ext| ext.to_str()) {
            Some("html") => "text/html; charset=utf-8",
            Some("css") => "text/css",
            Some("js") => "application/javascript",
            Some("json") => "application/json",
            Some("png") => "image/png",
            Some("jpg") | Some("jpeg") => "image/jpeg",
            Some("gif") => "image/gif",
            Some("svg") => "image/svg+xml",
            Some("ico") => "image/x-icon",
            Some("woff") => "font/woff",
            Some("woff2") => "font/woff2",
            Some("ttf") => "font/ttf",
            Some("eot") => "application/vnd.ms-fontobject",
            Some("pdf") => "application/pdf",
            Some("txt") => "text/plain; charset=utf-8",
            _ => "application/octet-stream",
        }.to_string()
    }
    
    pub fn generate_etag(&self, content: &[u8]) -> String {
        use sha2::{Sha256, Digest};
        let mut hasher = Sha256::new();
        hasher.update(content);
        let result = hasher.finalize();
        format!("\"{}\"", hex::encode(&result[..8]))
    }
}

impl Default for StaticFileHandler {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_simple_variable_substitution() {
        let engine = TemplateEngine::new("templates");
        let template = "Hello, {{ name }}!";
        let mut context = HashMap::new();
        context.insert("name".to_string(), json!("World"));
        
        let result = engine.render_string(template, &context).unwrap();
        assert_eq!(result, "Hello, World!");
    }

    #[test]
    fn test_conditional_rendering() {
        let engine = TemplateEngine::new("templates");
        let template = "{% if show_greeting %}Hello, {{ name }}!{% endif %}";
        let mut context = HashMap::new();
        context.insert("show_greeting".to_string(), json!(true));
        context.insert("name".to_string(), json!("World"));
        
        let result = engine.render_string(template, &context).unwrap();
        assert_eq!(result, "Hello, World!");
        
        // Test false condition
        context.insert("show_greeting".to_string(), json!(false));
        let result = engine.render_string(template, &context).unwrap();
        assert_eq!(result, "");
    }

    #[test]
    fn test_loop_rendering() {
        let engine = TemplateEngine::new("templates");
        let template = "{% for user in users %}Hello {{ user }}! {% endfor %}";
        let mut context = HashMap::new();
        context.insert("users".to_string(), json!(["Alice", "Bob", "Charlie"]));
        
        let result = engine.render_string(template, &context).unwrap();
        assert_eq!(result, "Hello Alice! Hello Bob! Hello Charlie! ");
    }

    #[test]
    fn test_html_escaping() {
        let engine = TemplateEngine::new("templates").with_auto_escape(true);
        let template = "{{ content }}";
        let mut context = HashMap::new();
        context.insert("content".to_string(), json!("<script>alert('xss')</script>"));
        
        let result = engine.render_string(template, &context).unwrap();
        assert!(result.contains("&lt;script&gt;"));
    }

    #[test]
    fn test_static_file_handler() {
        let mut handler = StaticFileHandler::new();
        handler.add_directory("/static", "public");
        
        let file_path = handler.get_file_path("/static/css/style.css");
        assert!(file_path.is_some());
        assert_eq!(file_path.unwrap(), PathBuf::from("public/css/style.css"));
        
        // Test security - should reject path traversal
        let bad_path = handler.get_file_path("/static/../secret.txt");
        assert!(bad_path.is_none());
    }

    #[test]
    fn test_content_type_detection() {
        let handler = StaticFileHandler::new();
        
        assert_eq!(handler.get_content_type(Path::new("style.css")), "text/css");
        assert_eq!(handler.get_content_type(Path::new("script.js")), "application/javascript");
        assert_eq!(handler.get_content_type(Path::new("image.png")), "image/png");
        assert_eq!(handler.get_content_type(Path::new("unknown.xyz")), "application/octet-stream");
    }
}
