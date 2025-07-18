"""
Unit tests for Sufast core functionality.
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import platform
import sys
from pathlib import Path

from sufast import App


class TestApp:
    """Test the main App class functionality."""

    def test_app_initialization(self):
        """Test App initializes correctly."""
        app = App()
        
        assert app.routes == {
            "GET": {},
            "POST": {},
            "PUT": {},
            "PATCH": {},
            "DELETE": {}
        }
        
        expected_lib = "sufast_server.dll" if platform.system() == "Windows" else "sufast_server.so"
        assert app.library_name == expected_lib

    def test_get_decorator(self):
        """Test @app.get decorator registration."""
        app = App()
        
        @app.get("/test")
        def test_handler():
            return {"message": "test"}
        
        assert "/test" in app.routes["GET"]
        assert app.routes["GET"]["/test"] == '{"message": "test"}'

    def test_post_decorator(self):
        """Test @app.post decorator registration."""
        app = App()
        
        @app.post("/create")
        def create_handler():
            return {"created": True}
        
        assert "/create" in app.routes["POST"]
        assert app.routes["POST"]["/create"] == '{"created": true}'

    def test_put_decorator(self):
        """Test @app.put decorator registration."""
        app = App()
        
        @app.put("/update")
        def update_handler():
            return {"updated": True}
        
        assert "/update" in app.routes["PUT"]
        assert app.routes["PUT"]["/update"] == '{"updated": true}'

    def test_patch_decorator(self):
        """Test @app.patch decorator registration."""
        app = App()
        
        @app.patch("/modify")
        def modify_handler():
            return {"modified": True}
        
        assert "/modify" in app.routes["PATCH"]
        assert app.routes["PATCH"]["/modify"] == '{"modified": true}'

    def test_delete_decorator(self):
        """Test @app.delete decorator registration."""
        app = App()
        
        @app.delete("/remove")
        def remove_handler():
            return {"deleted": True}
        
        assert "/remove" in app.routes["DELETE"]
        assert app.routes["DELETE"]["/remove"] == '{"deleted": true}'

    def test_string_response_handling(self):
        """Test that string responses are not double-encoded."""
        app = App()
        
        @app.get("/string")
        def string_handler():
            return "Hello World"
        
        assert app.routes["GET"]["/string"] == "Hello World"

    def test_handler_exception_handling(self):
        """Test that handler exceptions are caught and stored."""
        app = App()
        
        @app.get("/error")
        def error_handler():
            raise ValueError("Test error")
        
        stored_response = app.routes["GET"]["/error"]
        parsed_response = json.loads(stored_response)
        assert "error" in parsed_response
        assert "Test error" in parsed_response["error"]
