"""Compatibility regression tests for public package exports."""

from sufast import App, Database, Model, SQLiteConnection, Sufast


def test_app_alias_points_to_sufast():
    """Legacy App import stays compatible with Sufast."""
    assert App is Sufast


def test_database_symbols_exported():
    """Legacy top-level database symbols remain importable."""
    assert Database is not None
    assert Model is not None
    assert SQLiteConnection is not None
