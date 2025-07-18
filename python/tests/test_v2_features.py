"""
Test the new v2.0 features
"""
import pytest
from sufast import (
    App, Request, Response, json_response, 
    CORSMiddleware, LoggingMiddleware,
    Database, Model, SQLiteConnection
)
from sufast.routing import Router
from dataclasses import dataclass
from typing import Optional


def test_new_app_features():
    """Test that the new App features work."""
    app = App(debug=True)
    
    # Test middleware
    cors = CORSMiddleware()
    app.add_middleware(cors)
    
    assert len(app.middleware_stack.middlewares) == 1
    
    # Test router
    assert isinstance(app.router, Router)
    
    # Test template engine
    assert app.template_engine is not None


def test_dynamic_routing():
    """Test dynamic routing with parameters."""
    app = App()
    
    @app.get('/users/{user_id:int}')
    def get_user(request):
        user_id = request.path_params['user_id']
        return json_response({'user_id': user_id})
    
    # Check route was registered
    route, params = app.router.find_route('GET', '/users/123')
    assert route is not None
    assert params['user_id'] == 123


def test_request_response_objects():
    """Test Request and Response objects."""
    # Test Request
    headers = {'content-type': 'application/json'}
    body = b'{"name": "test"}'
    request = Request('POST', '/test', headers, body, 'param=value')
    
    assert request.method == 'POST'
    assert request.path == '/test'
    assert request.json == {'name': 'test'}
    assert request.query_params == {'param': 'value'}
    assert request.is_json == True
    
    # Test Response
    response = json_response({'message': 'hello'}, 201)
    assert response.status == 201
    assert response.content == {'message': 'hello'}
    
    response_dict = response.to_dict()
    assert response_dict['status'] == 201
    assert 'application/json' in response_dict['headers']['content-type']


def test_middleware_system():
    """Test middleware processing."""
    cors = CORSMiddleware(allow_origins=['https://example.com'])
    
    # Test request processing
    request = Request('OPTIONS', '/test', {'origin': 'https://example.com'}, b'')
    response = cors.process_request(request)
    
    assert response is not None  # Should return preflight response
    assert response.status == 200


def test_database_model():
    """Test database model functionality."""
    @dataclass
    class TestUser(Model):
        id: Optional[int] = None
        name: str = ""
        email: str = ""
    
    # Test model creation
    user_data = {'name': 'John', 'email': 'john@example.com'}
    user = TestUser(**user_data)
    
    assert user.name == 'John'
    assert user.email == 'john@example.com'
    
    # Test to_dict
    user_dict = user.to_dict()
    assert 'name' in user_dict
    assert 'email' in user_dict


def test_route_groups():
    """Test route groups functionality."""
    app = App()
    
    api_v1 = app.group('/api/v1')
    
    @api_v1.get('/users')
    def get_users(request):
        return json_response([])
    
    # Check route was registered with prefix
    route, params = app.router.find_route('GET', '/api/v1/users')
    assert route is not None
    assert route.path == '/api/v1/users'


def test_static_file_handler():
    """Test static file handler."""
    from sufast.templates import StaticFileHandler
    
    handler = StaticFileHandler('static', '/static')
    
    assert handler.is_static_file('/static/css/style.css') == True
    assert handler.is_static_file('/api/users') == False


def test_template_engine():
    """Test template engine."""
    from sufast.templates import TemplateEngine
    
    engine = TemplateEngine('templates')
    
    # Test basic variable substitution
    template = "Hello {{ name }}!"
    result = engine._render_template(template, {'name': 'World'})
    
    assert result == "Hello World!"
    
    # Test loops
    template = "{% for item in items %}{{ item }}{% endfor %}"
    result = engine._render_template(template, {'items': ['a', 'b', 'c']})
    
    assert result == "abc"


def test_complete_request_flow():
    """Test a complete request flow with all features."""
    app = App(debug=True)
    
    # Add middleware
    app.add_middleware(LoggingMiddleware())
    
    @app.get('/api/test/{id:int}')
    def test_endpoint(request):
        return json_response({
            'id': request.path_params['id'],
            'query': request.query_params,
            'method': request.method
        })
    
    # Simulate request handling
    headers = {'content-type': 'application/json'}
    result = app.handle_request('GET', '/api/test/42', headers, b'', 'filter=active')
    
    assert result['status'] == 200
    body = result['body']
    import json
    data = json.loads(body)
    
    assert data['id'] == 42
    assert data['query'] == {'filter': 'active'}
    assert data['method'] == 'GET'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
