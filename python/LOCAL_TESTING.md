# Local Python Testing

Use these commands from the `python/` directory for deterministic local runs.

## 1) Environment setup

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## 2) Run all tests

```bash
python -m pytest
```

## 3) Run targeted suites

```bash
python -m pytest tests/test_core.py -q
python -m pytest tests/test_integration.py -q
python -m pytest -m "not slow"
```

## 4) Coverage sanity

```bash
python -m pytest --cov=sufast --cov-report=term-missing
```

## 5) Static checks

```bash
python -m flake8 sufast tests
python -m mypy sufast
```

## Notes

- Use `python -m pytest` (not plain `pytest`) to avoid environment/path drift.
- Tests are written to run without the Rust shared library and should pass in Python-only mode.
- If optional dev tools are missing, install them with `python -m pip install -e ".[dev]"`.
