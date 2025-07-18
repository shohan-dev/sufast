// Advanced routing with typed parameters and pattern matching

use regex::Regex;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RouteDefinition {
    pub method: String,
    pub path: String,
    pub handler_name: String,
    pub middleware: Vec<String>,
    pub params: HashMap<String, String>, // parameter types
}

#[derive(Debug, Clone)]
pub struct RoutePattern {
    pub regex: Regex,
    pub param_names: Vec<String>,
    pub param_types: HashMap<String, ParamType>,
}

#[derive(Debug, Clone)]
pub enum ParamType {
    String,
    Integer,
    Float,
    Uuid,
    Slug,
}

impl RoutePattern {
    pub fn compile(path: &str) -> Self {
        let mut regex_pattern = String::new();
        let mut param_names = Vec::new();
        let mut param_types = HashMap::new();
        let mut current_pos = 0;

        // Find all parameter patterns {name:type} or {name}
        while let Some(start) = path[current_pos..].find('{') {
            let abs_start = current_pos + start;

            // Add literal part before parameter
            regex_pattern.push_str(&regex::escape(&path[current_pos..abs_start]));

            // Find end of parameter
            if let Some(end) = path[abs_start..].find('}') {
                let abs_end = abs_start + end;
                let param_spec = &path[abs_start + 1..abs_end];

                let (param_name, param_type) = if param_spec.contains(':') {
                    let parts: Vec<&str> = param_spec.split(':').collect();
                    (parts[0], parse_param_type(parts[1]))
                } else {
                    (param_spec, ParamType::String)
                };

                param_names.push(param_name.to_string());
                param_types.insert(param_name.to_string(), param_type.clone());

                // Add regex pattern for parameter type
                let type_pattern = match param_type {
                    ParamType::Integer => r"(-?\d+)",
                    ParamType::Float => r"(-?\d+\.?\d*)",
                    ParamType::Uuid => {
                        r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
                    }
                    ParamType::Slug => r"([\w\-]+)",
                    ParamType::String => r"([^/]+)",
                };
                regex_pattern.push_str(type_pattern);

                current_pos = abs_end + 1;
            } else {
                // Malformed parameter, treat as literal
                regex_pattern.push('{');
                current_pos = abs_start + 1;
            }
        }

        // Add remaining literal part
        regex_pattern.push_str(&regex::escape(&path[current_pos..]));

        // Anchor the pattern
        regex_pattern = format!("^{}$", regex_pattern);

        let regex = Regex::new(&regex_pattern).unwrap_or_else(|_| {
            // Fallback to exact match if regex compilation fails
            Regex::new(&format!("^{}$", regex::escape(path))).unwrap()
        });

        Self {
            regex,
            param_names,
            param_types,
        }
    }
}

fn parse_param_type(type_str: &str) -> ParamType {
    match type_str {
        "int" => ParamType::Integer,
        "float" => ParamType::Float,
        "uuid" => ParamType::Uuid,
        "slug" => ParamType::Slug,
        _ => ParamType::String,
    }
}

pub fn extract_path_params(pattern: &RoutePattern, path: &str) -> Option<HashMap<String, String>> {
    if let Some(captures) = pattern.regex.captures(path) {
        let mut params = HashMap::new();

        for (i, param_name) in pattern.param_names.iter().enumerate() {
            if let Some(captured) = captures.get(i + 1) {
                let value = captured.as_str();

                // Validate parameter type
                if let Some(param_type) = pattern.param_types.get(param_name) {
                    if !validate_param_type(value, param_type) {
                        return None;
                    }
                }

                params.insert(param_name.clone(), value.to_string());
            }
        }

        Some(params)
    } else {
        None
    }
}

fn validate_param_type(value: &str, param_type: &ParamType) -> bool {
    match param_type {
        ParamType::Integer => value.parse::<i64>().is_ok(),
        ParamType::Float => value.parse::<f64>().is_ok(),
        ParamType::Uuid => {
            // Basic UUID format validation
            value.len() == 36 && value.chars().filter(|&c| c == '-').count() == 4
        }
        ParamType::Slug => {
            // Alphanumeric characters and hyphens only
            value.chars().all(|c| c.is_alphanumeric() || c == '-')
        }
        ParamType::String => true, // Any string is valid
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_simple_route_pattern() {
        let pattern = RoutePattern::compile("/users/{id:int}");
        let params = extract_path_params(&pattern, "/users/123");

        assert!(params.is_some());
        let params = params.unwrap();
        assert_eq!(params.get("id"), Some(&"123".to_string()));
    }

    #[test]
    fn test_multiple_params() {
        let pattern = RoutePattern::compile("/users/{user_id:int}/posts/{post_id:int}");
        let params = extract_path_params(&pattern, "/users/123/posts/456");

        assert!(params.is_some());
        let params = params.unwrap();
        assert_eq!(params.get("user_id"), Some(&"123".to_string()));
        assert_eq!(params.get("post_id"), Some(&"456".to_string()));
    }

    #[test]
    fn test_uuid_validation() {
        let pattern = RoutePattern::compile("/users/{id:uuid}");
        let valid_uuid = "123e4567-e89b-12d3-a456-426614174000";
        let params = extract_path_params(&pattern, &format!("/users/{}", valid_uuid));

        assert!(params.is_some());
        assert_eq!(params.unwrap().get("id"), Some(&valid_uuid.to_string()));

        // Test invalid UUID
        let invalid_params = extract_path_params(&pattern, "/users/not-a-uuid");
        assert!(invalid_params.is_none());
    }

    #[test]
    fn test_float_validation() {
        let pattern = RoutePattern::compile("/price/{amount:float}");
        let params = extract_path_params(&pattern, "/price/19.99");

        assert!(params.is_some());
        assert_eq!(params.unwrap().get("amount"), Some(&"19.99".to_string()));
    }

    #[test]
    fn test_slug_validation() {
        let pattern = RoutePattern::compile("/posts/{slug:slug}");
        let params = extract_path_params(&pattern, "/posts/my-awesome-post");

        assert!(params.is_some());
        assert_eq!(
            params.unwrap().get("slug"),
            Some(&"my-awesome-post".to_string())
        );

        // Test invalid slug (contains special characters)
        let invalid_params = extract_path_params(&pattern, "/posts/my post!");
        assert!(invalid_params.is_none());
    }
}
