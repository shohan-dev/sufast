"""Unit tests for core app behavior via public API."""

from sufast import App
from sufast.testclient import TestClient


def test_app_initialization_defaults():
    app = App(title="Core Test App")
    stats = app.get_performance_stats()

    # Built-in docs + health routes should be available.
    assert stats["routes"]["total"] >= 4
    assert stats["framework"] == "Sufast"


def test_http_method_decorators_register_and_respond():
    app = App()

    @app.get("/get")
    def get_handler():
        return {"ok": "get"}

    @app.post("/post")
    def post_handler():
        return {"ok": "post"}

    @app.put("/put")
    def put_handler():
        return {"ok": "put"}

    @app.patch("/patch")
    def patch_handler():
        return {"ok": "patch"}

    @app.delete("/delete")
    def delete_handler():
        return {"ok": "delete"}

    with TestClient(app) as client:
        assert client.get("/get").json()["ok"] == "get"
        assert client.post("/post").json()["ok"] == "post"
        assert client.put("/put").json()["ok"] == "put"
        assert client.patch("/patch").json()["ok"] == "patch"
        assert client.delete("/delete").json()["ok"] == "delete"


def test_string_response_is_plain_text():
    app = App()

    @app.get("/string")
    def string_handler():
        return "Hello World"

    with TestClient(app) as client:
        response = client.get("/string")
        assert response.status_code == 200
        assert response.text == "Hello World"


def test_handler_exception_returns_500():
    app = App(debug=False)

    @app.get("/error")
    def error_handler():
        raise ValueError("Test error")

    with TestClient(app) as client:
        response = client.get("/error")
        assert response.status_code == 500
        assert "Internal Server Error" in response.text
