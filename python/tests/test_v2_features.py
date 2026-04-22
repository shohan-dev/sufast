"""Regression tests for exported framework features."""

from dataclasses import dataclass
from typing import Optional

from sufast import (
    APIRouter,
    App,
    CORSMiddleware,
    Database,
    Model,
    Request,
    SQLiteConnection,
    json_response,
)
from sufast.templates import StaticFileHandler, TemplateEngine
from sufast.testclient import TestClient


def test_dynamic_routing_with_typed_parameter():
    app = App()

    @app.get("/users/{user_id}")
    def get_user(user_id: int):
        return {"user_id": user_id}

    with TestClient(app) as client:
        response = client.get("/users/123")
        assert response.status_code == 200
        assert response.json()["user_id"] == 123


def test_request_and_response_helpers():
    request = Request(
        "POST",
        "/test",
        {"content-type": "application/json"},
        b'{"name":"test"}',
        "page=1",
    )
    assert request.json == {"name": "test"}
    assert request.query_params == {"page": "1"}

    response = json_response({"message": "ok"}, 201)
    payload = response.to_dict()
    assert payload["status"] == 201
    assert payload["headers"]["content-type"] == "application/json"


def test_cors_middleware_integration():
    app = App()
    app.add_middleware(CORSMiddleware, allow_origins=["https://example.com"])

    @app.get("/hello")
    def hello():
        return {"ok": True}

    with TestClient(app) as client:
        response = client.get("/hello", headers={"origin": "https://example.com"})
        assert response.status_code == 200
        assert (
            response.headers.get("access-control-allow-origin") == "https://example.com"
        )


def test_database_model_basics():
    @dataclass
    class TestUser(Model):
        id: Optional[int] = None
        name: str = ""
        email: str = ""

    conn = SQLiteConnection(":memory:")
    db = Database(conn)
    db.create_tables([TestUser])

    TestUser.create(name="John", email="john@example.com")
    records = TestUser.where(name="John")

    assert len(records) == 1
    assert records[0].name == "John"
    assert records[0].email == "john@example.com"
    db.close()


def test_api_router_prefix_registration():
    app = App()
    router = APIRouter(prefix="/api/v1")

    @router.get("/users")
    def get_users():
        return []

    app.include_router(router)
    with TestClient(app) as client:
        assert client.get("/api/v1/users").status_code == 200


def test_template_engine_and_static_handler():
    engine = TemplateEngine("templates")
    assert (
        engine._render_template("Hello {{ name }}!", {"name": "World"})
        == "Hello World!"
    )
    assert (
        engine._render_template(
            "{% for item in items %}{{ item }}{% endfor %}", {"items": ["a", "b"]}
        )
        == "ab"
    )

    handler = StaticFileHandler("static", "/static")
    assert handler.is_static_file("/static/css/style.css")
    assert not handler.is_static_file("/api/users")
