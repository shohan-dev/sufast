"""
Sufast docs UI generators.

This module renders `/docs` and `/redoc` pages from OpenAPI specs using
UI assets stored in `sufast/docui/`.
"""

from __future__ import annotations

import json
from html import escape as html_escape
from pathlib import Path
from typing import Any, Dict

_DOCUI_DIR = Path(__file__).with_name("docui")


def _read_docui_asset(filename: str) -> str:
    """Read a doc UI asset as UTF-8 text."""
    path = _DOCUI_DIR / filename
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        # Keep docs route functional even if packaging omitted an asset.
        return ""


def _render_template(template: str, context: Dict[str, str]) -> str:
    """Render a template by replacing `__TOKEN__` placeholders."""
    rendered = template
    for key, value in context.items():
        rendered = rendered.replace(f"__{key}__", value)
    return rendered


def _build_method_stats(openapi_spec: Dict[str, Any]) -> str:
    """Build method pills HTML for docs header."""
    method_counts = {
        "get": 0,
        "post": 0,
        "put": 0,
        "delete": 0,
        "patch": 0,
        "websocket": 0,
    }
    total = 0
    for _, methods in openapi_spec.get("paths", {}).items():
        for method, op in methods.items():
            m = method.lower()
            if op.get("x-websocket"):
                method_counts["websocket"] += 1
            elif m in method_counts:
                method_counts[m] += 1
            total += 1

    pills = [f'<span class="stat-pill total">Total: {total}</span>']
    for method, count in method_counts.items():
        if count > 0:
            pills.append(
                f'<span class="stat-pill {method}">{method.upper()}: {count}</span>'
            )
    return "".join(pills)


def generate_swagger_html(openapi_spec: dict, theme: str = "default") -> str:
    """Generate `/docs` HTML from OpenAPI spec."""
    info = openapi_spec.get("info", {})
    title = info.get("title", "Sufast API")
    version = info.get("version", "1.0.0")
    description = info.get("description", "Interactive API documentation.")

    css = _read_docui_asset("swagger.css")
    js = _read_docui_asset("swagger.js")
    html_template = _read_docui_asset("swagger.html")

    default_theme = "dark" if theme not in {"light", "dark"} else theme
    context = {
        "TITLE": html_escape(str(title)),
        "VERSION": html_escape(str(version)),
        "DESCRIPTION": html_escape(str(description)),
        "SPEC_JSON": json.dumps(openapi_spec, default=str),
        "DEFAULT_THEME": default_theme,
        "METHOD_STATS": _build_method_stats(openapi_spec),
        "INLINE_CSS": css,
        "INLINE_JS": js,
    }
    return _render_template(html_template, context)


def generate_redoc_html(openapi_spec: dict) -> str:
    """Generate `/redoc` HTML from OpenAPI spec."""
    title = openapi_spec.get("info", {}).get("title", "Sufast API")

    css = _read_docui_asset("redoc.css")
    js = _read_docui_asset("redoc.js")
    html_template = _read_docui_asset("redoc.html")

    context = {
        "TITLE": html_escape(str(title)),
        "SPEC_JSON": json.dumps(openapi_spec, default=str),
        "INLINE_CSS": css,
        "INLINE_JS": js,
    }
    return _render_template(html_template, context)
