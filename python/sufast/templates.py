"""
Template engine and static file handling for Sufast framework.
"""
import os
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional, Union
from .request import Response, html_response


class TemplateEngine:
    """Simple template engine with basic functionality."""
    
    def __init__(self, template_dir: str = 'templates'):
        self.template_dir = Path(template_dir)
        self.template_cache = {}
        self.auto_reload = True
    
    def render(self, template_name: str, context: Dict[str, Any] = None) -> str:
        """Render template with context."""
        context = context or {}
        template_path = self.template_dir / template_name
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template {template_name} not found")
        
        # Check cache
        cache_key = str(template_path)
        if not self.auto_reload and cache_key in self.template_cache:
            template_content = self.template_cache[cache_key]
        else:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            self.template_cache[cache_key] = template_content
        
        # Simple template rendering (basic variable substitution)
        return self._render_template(template_content, context)
    
    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """Basic template rendering with variable substitution."""
        result = template
        
        # Handle simple variables {{ variable }}
        import re
        var_pattern = r'\{\{\s*(\w+)\s*\}\}'
        
        def replace_var(match):
            var_name = match.group(1)
            return str(context.get(var_name, f'{{{{ {var_name} }}}}'))
        
        result = re.sub(var_pattern, replace_var, result)
        
        # Handle loops {% for item in items %}...{% endfor %}
        loop_pattern = r'\{\%\s*for\s+(\w+)\s+in\s+(\w+)\s*\%\}(.*?)\{\%\s*endfor\s*\%\}'
        
        def replace_loop(match):
            item_var = match.group(1)
            list_var = match.group(2)
            loop_content = match.group(3)
            
            if list_var not in context:
                return ''
            
            result_parts = []
            for item in context[list_var]:
                item_context = context.copy()
                item_context[item_var] = item
                rendered_item = self._render_template(loop_content, item_context)
                result_parts.append(rendered_item)
            
            return ''.join(result_parts)
        
        result = re.sub(loop_pattern, replace_loop, result, flags=re.DOTALL)
        
        # Handle conditionals {% if condition %}...{% endif %}
        if_pattern = r'\{\%\s*if\s+(\w+)\s*\%\}(.*?)\{\%\s*endif\s*\%\}'
        
        def replace_if(match):
            condition_var = match.group(1)
            if_content = match.group(2)
            
            if context.get(condition_var):
                return self._render_template(if_content, context)
            return ''
        
        result = re.sub(if_pattern, replace_if, result, flags=re.DOTALL)
        
        return result
    
    def render_response(self, template_name: str, context: Dict[str, Any] = None, 
                       status: int = 200) -> Response:
        """Render template and return HTML response."""
        html = self.render(template_name, context)
        return html_response(html, status)


class StaticFileHandler:
    """Handler for static files."""
    
    def __init__(self, static_dir: str = 'static', url_prefix: str = '/static'):
        self.static_dir = Path(static_dir)
        self.url_prefix = url_prefix.rstrip('/')
        self.cache_max_age = 3600  # 1 hour
    
    def serve_file(self, file_path: str) -> Response:
        """Serve a static file."""
        # Remove URL prefix and get file path
        if file_path.startswith(self.url_prefix):
            file_path = file_path[len(self.url_prefix):].lstrip('/')
        
        full_path = self.static_dir / file_path
        
        # Security check - ensure file is within static directory
        try:
            full_path = full_path.resolve()
            self.static_dir.resolve()
            if not str(full_path).startswith(str(self.static_dir.resolve())):
                return Response({'error': 'Access denied'}, 403)
        except (OSError, ValueError):
            return Response({'error': 'Invalid path'}, 400)
        
        if not full_path.exists():
            return Response({'error': 'File not found'}, 404)
        
        if not full_path.is_file():
            return Response({'error': 'Not a file'}, 404)
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(str(full_path))
        if content_type is None:
            content_type = 'application/octet-stream'
        
        try:
            with open(full_path, 'rb') as f:
                content = f.read()
            
            headers = {
                'cache-control': f'public, max-age={self.cache_max_age}',
                'content-length': str(len(content))
            }
            
            return Response(content, 200, headers, content_type)
        
        except Exception as e:
            return Response({'error': f'Error reading file: {str(e)}'}, 500)
    
    def is_static_file(self, path: str) -> bool:
        """Check if path is for a static file."""
        return path.startswith(self.url_prefix)


class AssetManager:
    """Manages CSS, JS, and other assets."""
    
    def __init__(self, static_handler: StaticFileHandler):
        self.static_handler = static_handler
        self.css_files = []
        self.js_files = []
    
    def add_css(self, file_path: str):
        """Add CSS file to be included."""
        if file_path not in self.css_files:
            self.css_files.append(file_path)
    
    def add_js(self, file_path: str):
        """Add JavaScript file to be included."""
        if file_path not in self.js_files:
            self.js_files.append(file_path)
    
    def render_css_tags(self) -> str:
        """Render CSS link tags."""
        tags = []
        for css_file in self.css_files:
            url = f"{self.static_handler.url_prefix}/{css_file}"
            tags.append(f'<link rel="stylesheet" href="{url}">')
        return '\n'.join(tags)
    
    def render_js_tags(self) -> str:
        """Render JavaScript script tags."""
        tags = []
        for js_file in self.js_files:
            url = f"{self.static_handler.url_prefix}/{js_file}"
            tags.append(f'<script src="{url}"></script>')
        return '\n'.join(tags)


# Template helper functions
def url_for(route_name: str, **kwargs) -> str:
    """Generate URL for route (to be implemented by App)."""
    # This will be overridden by the App instance
    return f"/{route_name}"

def static_url(filename: str) -> str:
    """Generate URL for static file."""
    return f"/static/{filename}"


# Global template functions that can be used in templates
TEMPLATE_GLOBALS = {
    'url_for': url_for,
    'static_url': static_url,
}


class JinjaTemplateEngine(TemplateEngine):
    """Jinja2-based template engine for more advanced features."""
    
    def __init__(self, template_dir: str = 'templates'):
        super().__init__(template_dir)
        self.jinja_env = None
        self._setup_jinja()
    
    def _setup_jinja(self):
        """Setup Jinja2 environment."""
        try:
            from jinja2 import Environment, FileSystemLoader
            loader = FileSystemLoader(str(self.template_dir))
            self.jinja_env = Environment(
                loader=loader,
                autoescape=True,
                auto_reload=self.auto_reload
            )
            # Add global functions
            self.jinja_env.globals.update(TEMPLATE_GLOBALS)
        except ImportError:
            print("Jinja2 not installed. Using basic template engine.")
            self.jinja_env = None
    
    def render(self, template_name: str, context: Dict[str, Any] = None) -> str:
        """Render template with Jinja2 if available, otherwise use basic engine."""
        context = context or {}
        
        if self.jinja_env:
            try:
                template = self.jinja_env.get_template(template_name)
                return template.render(**context)
            except Exception as e:
                print(f"Jinja2 template error: {e}")
                # Fall back to basic engine
                pass
        
        # Use basic template engine
        return super().render(template_name, context)
