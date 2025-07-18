# Contributing to Sufast

We love your input! We want to make contributing to Sufast as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Environment Setup

### Prerequisites

- **Python 3.8+** with pip
- **Rust 1.70+** with Cargo
- **Git** for version control

### Setup Instructions

1. **Fork and Clone**
   ```bash
   git clone https://github.com/shohan-dev/sufast.git
   cd sufast
   ```

2. **Python Development Setup**
   ```bash
   cd python
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   
   pip install -e .[dev]
   ```

3. **Rust Development Setup**
   ```bash
   cd rust-core
   cargo build
   cargo test
   ```

4. **Pre-commit Hooks** (Optional but recommended)
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Development Workflow

### For Python Developers

1. **Make changes** in `python/sufast/`
2. **Add tests** in `python/tests/`
3. **Run tests**: `python scripts/test.py python`
4. **Check formatting**: `python scripts/lint.py python`
5. **Auto-format**: `python scripts/lint.py format`

### For Rust Developers

1. **Make changes** in `rust-core/src/`
2. **Add tests** in the same files or `rust-core/tests/`
3. **Run tests**: `python scripts/test.py rust`
4. **Check formatting**: `python scripts/lint.py rust`
5. **Auto-format**: `cargo fmt`

### Building and Testing

```bash
# Build everything
python scripts/build.py all

# Run all tests
python scripts/test.py all

# Run linting
python scripts/lint.py all

# Run only Python tests
python scripts/test.py python

# Run only Rust tests
python scripts/test.py rust

# Run benchmarks
python scripts/test.py bench
```

## Project Structure

```
📁 sufast/
├── 🐍 python/              # Python package
│   ├── sufast/             # Main Python module
│   │   ├── __init__.py     # Package exports
│   │   └── core.py         # Core App class
│   ├── tests/              # Python test suite
│   │   ├── test_core.py    # Core functionality tests
│   │   └── test_integration.py # Integration tests
│   ├── pyproject.toml      # Python package configuration
│   └── MANIFEST.in         # Package data inclusion
├── 🦀 rust-core/           # Rust engine
│   ├── src/                # Rust source code
│   │   ├── lib.rs          # FFI interface
│   │   ├── server.rs       # HTTP server
│   │   ├── routes.rs       # Route management
│   │   └── handlers.rs     # Request handlers
│   ├── benches/            # Rust benchmarks
│   ├── Cargo.toml          # Rust package configuration
│   └── README.md           # Rust-specific documentation
├── 📚 docs/                # Documentation
├── 🔧 scripts/             # Build and development scripts
│   ├── build.py            # Build automation
│   ├── lint.py             # Code quality checks
│   └── test.py             # Test automation
├── 🔄 .github/workflows/   # CI/CD configuration
└── 📋 Root configuration files
```

## Coding Standards

### Python Code Style

- **Formatter**: Black (line length: 88)
- **Import sorting**: isort
- **Linting**: flake8
- **Type checking**: mypy
- **Docstrings**: Google style

Example:
```python
def create_user(name: str, email: str) -> Dict[str, Any]:
    """Create a new user with the given name and email.
    
    Args:
        name: The user's full name.
        email: The user's email address.
        
    Returns:
        A dictionary containing the created user's information.
        
    Raises:
        ValueError: If name or email is empty.
    """
    if not name or not email:
        raise ValueError("Name and email are required")
    
    return {"name": name, "email": email, "id": generate_id()}
```

### Rust Code Style

- **Formatter**: rustfmt (default settings)
- **Linting**: clippy with deny warnings
- **Documentation**: rustdoc with examples

Example:
```rust
/// Match a request path against a route pattern.
/// 
/// # Examples
/// 
/// ```
/// let params = match_path("/users/{id}", "/users/123");
/// assert_eq!(params.unwrap().get("id"), Some(&"123".to_string()));
/// ```
/// 
/// # Arguments
/// 
/// * `pattern` - The route pattern with parameters in {braces}
/// * `path` - The actual request path to match
/// 
/// # Returns
/// 
/// `Some(HashMap)` with extracted parameters, or `None` if no match
pub fn match_path(pattern: &str, path: &str) -> Option<HashMap<String, String>> {
    // Implementation...
}
```

## Testing Guidelines

### Python Tests

- Use **pytest** for all tests
- Aim for **90%+ coverage**
- Use **mocking** for external dependencies
- Separate **unit**, **integration**, and **performance** tests

Test file structure:
```python
class TestFeatureName:
    """Test the FeatureName functionality."""
    
    def test_basic_functionality(self):
        """Test basic feature works as expected."""
        # Arrange
        app = App()
        
        # Act
        result = app.some_method()
        
        # Assert
        assert result == expected
    
    @pytest.mark.performance
    def test_performance(self, benchmark):
        """Test performance requirements."""
        result = benchmark(expensive_operation)
        assert result.is_fast_enough()
```

### Rust Tests

- Use **built-in test framework**
- Include **unit**, **integration**, and **doc tests**
- Use **criterion** for benchmarks

Test structure:
```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_basic_functionality() {
        // Arrange
        let input = "test input";
        
        // Act
        let result = function_under_test(input);
        
        // Assert
        assert_eq!(result, expected);
    }
    
    #[tokio::test]
    async fn test_async_functionality() {
        // Test async functions
    }
}
```

## Performance Requirements

- **HTTP Requests**: Must handle 50,000+ RPS
- **Memory Usage**: Keep under 100MB for typical workloads
- **Startup Time**: Under 100ms for development mode
- **Response Time**: 95th percentile under 10ms

## Pull Request Process

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make Your Changes**
   - Write code following our style guidelines
   - Add comprehensive tests
   - Update documentation if needed

3. **Test Your Changes**
   ```bash
   python scripts/test.py all
   python scripts/lint.py all
   ```

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Add amazing feature
   
   - Implement feature X
   - Add tests for feature X
   - Update documentation"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/amazing-feature
   ```

6. **PR Checklist**
   - [ ] Tests pass locally
   - [ ] Code follows style guidelines
   - [ ] Documentation is updated
   - [ ] Performance impact is considered
   - [ ] Breaking changes are documented

## Issue Reporting

### Bug Reports

Use the bug report template and include:

- **Environment**: OS, Python version, Rust version
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Reproduction steps**: Minimal code to reproduce
- **Logs/Errors**: Any error messages or stack traces

### Feature Requests

Use the feature request template and include:

- **Use case**: Why is this feature needed
- **Proposed solution**: How should it work
- **Alternatives**: Other ways to solve the problem
- **Implementation**: Technical considerations

## Code Review Process

### For Reviewers

- **Be constructive**: Suggest improvements, don't just point out problems
- **Test the changes**: Pull the branch and test it locally
- **Consider performance**: How will this affect the 50k+ RPS goal?
- **Check documentation**: Are changes properly documented?

### For Contributors

- **Respond to feedback**: Address all review comments
- **Test suggestions**: Try reviewer suggestions and report back
- **Be patient**: Reviews take time, especially for large changes
- **Ask questions**: If feedback is unclear, ask for clarification

## Release Process

1. **Version Bump**: Update version in `python/pyproject.toml` and `rust-core/Cargo.toml`
2. **Changelog**: Update `CHANGELOG.md` with new features and fixes
3. **Documentation**: Update any version-specific documentation
4. **Testing**: Full test suite must pass on all platforms
5. **Tagging**: Create and push git tag
6. **CI/CD**: Automated release to PyPI via GitHub Actions

## Getting Help

- **GitHub Discussions**: For questions and general discussion
- **GitHub Issues**: For bug reports and feature requests
- **Documentation**: Check the docs/ directory first
- **Code Examples**: Look at tests/ for usage examples

## Recognition

Contributors will be:

- **Listed in CONTRIBUTORS.md**
- **Mentioned in release notes** for significant contributions
- **Given commit access** after consistent quality contributions
- **Invited to join the core team** for exceptional contributors

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

---

**Thank you for contributing to Sufast! 🚀**
