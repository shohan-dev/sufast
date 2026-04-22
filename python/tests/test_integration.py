"""Integration tests for Sufast public behavior."""

from sufast import APIRouter, App, Sufast
from sufast.testclient import TestClient


def test_legacy_app_alias_is_constructible():
    app = App(title="Alias Integration")
    assert isinstance(app, Sufast)


def test_multiple_apps_are_isolated():
    app1 = App()
    app2 = App()

    @app1.get("/app1")
    def app1_handler():
        return {"app": "first"}

    @app2.get("/app2")
    def app2_handler():
        return {"app": "second"}

    with TestClient(app1) as c1, TestClient(app2) as c2:
        assert c1.get("/app1").status_code == 200
        assert c1.get("/app2").status_code == 404
        assert c2.get("/app2").status_code == 200
        assert c2.get("/app1").status_code == 404


def test_router_inclusion_and_path_params_work():
    app = App()
    router = APIRouter(prefix="/api")

    @router.get("/users/{user_id}")
    def get_user(user_id: int):
        return {"user_id": user_id}

    app.include_router(router)

    with TestClient(app) as client:
        response = client.get("/api/users/42")
        assert response.status_code == 200
        assert response.json()["user_id"] == 42


def test_method_not_allowed_returns_405():
    app = App()

    @app.get("/only-get")
    def only_get():
        return {"ok": True}

    with TestClient(app) as client:
        response = client.post("/only-get")
        assert response.status_code == 405


def test_unicode_and_special_routes():
    app = App()

    @app.get("/api/v1/users-and-groups")
    def users_groups():
        return {"endpoint": "users-and-groups"}

    @app.get("/café")
    def cafe():
        return {"name": "cafe"}

    with TestClient(app) as client:
        assert client.get("/api/v1/users-and-groups").status_code == 200
        assert client.get("/café").status_code == 200


def test_registering_many_routes_is_supported():
    app = App()

    for i in range(200):

        def make_handler(idx):
            return lambda: {"route": idx}

        app.get(f"/route-{i}")(make_handler(i))

    stats = app.get_performance_stats()
    assert stats["routes"]["total"] >= 200
