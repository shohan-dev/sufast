"""Shared pytest fixtures for local and CI test consistency."""

import pytest

from sufast import App
from sufast.testclient import TestClient


@pytest.fixture
def app_factory():
    """Create isolated app instances for tests."""

    def _build(**kwargs):
        return App(debug=True, **kwargs)

    return _build


@pytest.fixture
def client_factory():
    """Create TestClient instances tied to a given app."""

    def _build(app):
        return TestClient(app)

    return _build


@pytest.fixture
def sample_user_payload():
    """Reusable JSON payload for user-oriented endpoint tests."""
    return {"name": "Test User", "email": "test@example.com", "role": "user"}
