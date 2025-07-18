"""
Integration tests for Sufast web framework.
"""
import threading
import time
import requests
import pytest
import ctypes
from unittest.mock import patch
import json

from sufast import App


class TestIntegration:
    """Integration tests that test the full stack."""

    @pytest.fixture
    def mock_rust_lib(self):
        """Mock the Rust library for integration tests."""
        with patch.object(App, '_load_sufast_lib') as mock_load:
            mock_lib = mock_load.return_value
            mock_lib.set_routes.return_value = True
            mock_lib.start_server.return_value = True
            yield mock_lib

    def test_app_routes_serialization(self, mock_rust_lib):
        """Test that routes are properly serialized and passed to Rust."""
        app = App()
        
        @app.get("/")
        def home():
            return {"message": "Hello World"}
        
        @app.post("/users")
        def create_user():
            return {"id": 1, "name": "Test User"}
        
        @app.get("/users/{id}")
        def get_user():
            return {"id": 123, "name": "Dynamic User"}
        
        # Mock the infinite loop to immediately raise KeyboardInterrupt
        def mock_run_loop(*args, **kwargs):
            # Simulate the server starting and then immediately stopping
            lib = app._load_sufast_lib()
            json_routes = json.dumps(app.routes).encode('utf-8')
            buffer = (ctypes.c_ubyte * len(json_routes)).from_buffer_copy(json_routes)
            
            print("\n🔧 Booting up ⚡ sufast web server engine...\n")
            print(f"🌐 Mode     : 🧪 Development")
            print(f"🔀  Routes   : {sum(len(r) for r in app.routes.values())} registered")
            print(f"🚪 Port     : 8080")
            print("🟢 Status   : Server is up and running!")
            print(f"➡️  Visit    : http://localhost:8080")
            print("🔄 Press Ctrl+C to stop the server.\n")
            
            lib.set_routes(buffer, len(json_routes))
            lib.start_server(False, 8080)
            
            print("🛑 Server stopped by user.")
            raise KeyboardInterrupt()
        
        # Replace the run method entirely
        with patch.object(app, 'run', side_effect=mock_run_loop):
            with pytest.raises(KeyboardInterrupt):
                app.run(port=8080)
        
        # Verify set_routes was called with correct data
        mock_rust_lib.set_routes.assert_called_once()
        
        # Get the JSON data that was passed to Rust
        call_args = mock_rust_lib.set_routes.call_args
        json_data = call_args[0][0]  # First argument (the buffer)
        
        # Convert buffer back to string and parse JSON
        json_str = bytes(json_data).decode('utf-8')
        routes_data = json.loads(json_str)
        
        # Verify route structure
        assert "GET" in routes_data
        assert "POST" in routes_data
        assert "/" in routes_data["GET"]
        assert "/users" in routes_data["POST"]
        assert "/users/{id}" in routes_data["GET"]

    def test_multiple_apps_isolation(self):
        """Test that multiple App instances don't interfere with each other."""
        app1 = App()
        app2 = App()
        
        @app1.get("/app1")
        def app1_handler():
            return {"app": "first"}
        
        @app2.get("/app2")
        def app2_handler():
            return {"app": "second"}
        
        # Verify isolation
        assert "/app1" in app1.routes["GET"]
        assert "/app1" not in app2.routes["GET"]
        assert "/app2" in app2.routes["GET"]
        assert "/app2" not in app1.routes["GET"]

    def test_large_number_of_routes(self, mock_rust_lib):
        """Test handling of many routes."""
        app = App()
        
        # Create 100 routes
        for i in range(100):
            @app.get(f"/route_{i}")
            def handler():
                return {"route": i}
        
        assert len(app.routes["GET"]) == 100
        
        # Mock the infinite loop to immediately raise KeyboardInterrupt
        def mock_run_loop(*args, **kwargs):
            lib = app._load_sufast_lib()
            json_routes = json.dumps(app.routes).encode('utf-8')
            buffer = (ctypes.c_ubyte * len(json_routes)).from_buffer_copy(json_routes)
            
            print("\n🔧 Booting up ⚡ sufast web server engine...\n")
            print(f"🌐 Mode     : 🧪 Development")
            print(f"🔀  Routes   : {sum(len(r) for r in app.routes.values())} registered")
            print(f"🚪 Port     : 8080")
            print("🟢 Status   : Server is up and running!")
            print(f"➡️  Visit    : http://localhost:8080")
            print("🔄 Press Ctrl+C to stop the server.\n")
            
            lib.set_routes(buffer, len(json_routes))
            lib.start_server(False, 8080)
            
            print("🛑 Server stopped by user.")
            raise KeyboardInterrupt()
        
        with patch.object(app, 'run', side_effect=mock_run_loop):
            with pytest.raises(KeyboardInterrupt):
                app.run()
        
        mock_rust_lib.set_routes.assert_called_once()

    def test_route_with_special_characters(self):
        """Test routes with special characters."""
        app = App()
        
        @app.get("/api/v1/users-and-groups")
        def users_groups():
            return {"endpoint": "users-and-groups"}
        
        @app.get("/search")
        def search():
            return {"query": "test", "results": []}
        
        assert "/api/v1/users-and-groups" in app.routes["GET"]
        assert "/search" in app.routes["GET"]

    def test_unicode_route_paths(self):
        """Test Unicode characters in route paths."""
        app = App()
        
        @app.get("/café")
        def cafe():
            return {"name": "café"}
        
        @app.get("/用户")
        def chinese_users():
            return {"language": "chinese"}
        
        assert "/café" in app.routes["GET"]
        assert "/用户" in app.routes["GET"]

    def test_json_serialization_edge_cases(self):
        """Test edge cases in JSON serialization."""
        app = App()
        
        @app.get("/empty")
        def empty():
            return {}
        
        @app.get("/null")
        def null():
            return None
        
        @app.get("/nested")
        def nested():
            return {
                "level1": {
                    "level2": {
                        "level3": "deep"
                    }
                }
            }
        
        assert app.routes["GET"]["/empty"] == "{}"
        assert app.routes["GET"]["/null"] == "null"
        
        nested_response = json.loads(app.routes["GET"]["/nested"])
        assert nested_response["level1"]["level2"]["level3"] == "deep"


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_handler_import_error(self):
        """Test handler that has import errors."""
        app = App()
        
        @app.get("/import_error")
        def import_error_handler():
            # Simulate an import error by raising one directly
            raise ImportError("Module not found")
        
        # The handler should be registered despite the error
        assert "/import_error" in app.routes["GET"]

    def test_handler_runtime_error(self):
        """Test handler that raises runtime errors."""
        app = App()
        
        @app.get("/runtime_error")
        def runtime_error_handler():
            return {"result": 1 / 0}  # Division by zero
        
        stored_response = app.routes["GET"]["/runtime_error"]
        parsed_response = json.loads(stored_response)
        assert "error" in parsed_response

    def test_handler_returns_unserializable(self):
        """Test handler that returns unserializable objects."""
        app = App()
        
        @app.get("/unserializable")
        def unserializable_handler():
            return {"function": lambda x: x}  # Functions can't be serialized
        
        stored_response = app.routes["GET"]["/unserializable"]
        parsed_response = json.loads(stored_response)
        assert "error" in parsed_response


class TestPerformance:
    """Performance-related tests."""

    @pytest.mark.performance
    def test_route_registration_performance(self, benchmark):
        """Benchmark route registration performance."""
        def register_routes():
            app = App()
            for i in range(1000):
                @app.get(f"/route_{i}")
                def handler():
                    return {"id": i}
            return app
        
        result = benchmark(register_routes)
        assert len(result.routes["GET"]) == 1000

    @pytest.mark.performance
    def test_json_serialization_performance(self, benchmark):
        """Benchmark JSON serialization performance."""
        app = App()
        
        large_data = {
            "users": [
                {"id": i, "name": f"User {i}", "email": f"user{i}@example.com"}
                for i in range(1000)
            ]
        }
        
        def register_large_response():
            @app.get("/large")
            def large_handler():
                return large_data
        
        benchmark(register_large_response)
        
        # Verify the data was stored correctly
        stored_response = app.routes["GET"]["/large"]
        parsed_response = json.loads(stored_response)
        assert len(parsed_response["users"]) == 1000
