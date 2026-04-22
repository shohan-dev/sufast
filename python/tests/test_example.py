"""Pytest smoke tests for the complete example app."""

from example.complete_example import app
from sufast.testclient import TestClient


def test_complete_example_smoke_paths():
    with TestClient(app) as client:
        assert client.get("/").status_code == 200
        assert client.get("/api/users").status_code == 200
        assert (
            client.post(
                "/api/users", json_data={"name": "Dave", "email": "dave@test.com"}
            ).status_code
            == 201
        )
        assert client.get("/api/products").status_code == 200
        assert client.get("/docs").status_code == 200
        assert client.get("/health").status_code == 200
        assert client.get("/html").status_code == 200
        assert client.get("/text").status_code == 200
        assert client.get("/sync").status_code == 200
        assert client.delete("/api/users/1").status_code == 200


def test_complete_example_openapi_available():
    with TestClient(app) as client:
        spec = client.get("/openapi.json")
        assert spec.status_code == 200
        payload = spec.json()
        assert "paths" in payload
        assert "/api/users" in payload["paths"]
