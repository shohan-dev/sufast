# Changelog

All notable changes to Sufast will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive CI/CD pipeline with GitHub Actions
- Multi-platform testing (Windows, macOS, Linux)
- Python type hints throughout the codebase
- Rust benchmarking suite with Criterion
- Security audit integration
- Performance regression testing
- Comprehensive documentation in docs/
- Development scripts for building, testing, and linting
- Pre-commit hooks support

### Changed
- Restructured project into professional multi-language layout
- Upgraded to Axum 0.7 for improved performance
- Enhanced error handling with better user feedback
- Improved FFI safety with comprehensive null checks
- Updated Rust dependencies to latest stable versions

### Developer Experience
- Clear separation between Python and Rust development
- Automated code formatting for both languages
- Comprehensive test suites with 90%+ coverage
- Detailed contributing guidelines
- Professional project structure

## [1.0.0] - 2024-01-01

### Added
- Initial release of Sufast web framework
- Core HTTP server powered by Rust (Axum/Tokio)
- Python decorator-based routing (`@app.get`, `@app.post`, etc.)
- Dynamic route parameters (`/users/{id}`)
- Cross-platform support (Windows, Linux, macOS)
- FFI integration between Python and Rust
- High-performance request handling (52,000+ RPS)
- Zero-configuration deployment
- Comprehensive error handling
- JSON response serialization
- Development and production modes

### Performance
- 52,000+ requests per second throughput
- ~2.1ms average response latency
- ~25MB memory usage for typical workloads
- Sub-100ms startup time

### Platform Support
- Python 3.8, 3.9, 3.10, 3.11, 3.12
- Windows (x64)
- Linux (x64)
- macOS (x64, ARM64)

## [0.2.4] - 2023-12-15

### Added
- Improved library loading with better error messages
- Enhanced route pattern matching
- Better Unicode support in routes and responses

### Fixed
- Library loading issues on some Linux distributions
- Route parameter extraction edge cases
- Memory leaks in long-running servers

## [0.2.3] - 2023-12-01

### Added
- Support for PATCH and DELETE methods
- Improved error reporting for handler exceptions
- Better cross-platform library detection

### Changed
- Optimized JSON serialization performance
- Enhanced startup logging and diagnostics

## [0.2.2] - 2023-11-15

### Added
- Production mode with optimized settings
- Configurable port binding
- Enhanced route storage efficiency

### Fixed
- Thread safety issues in route management
- Port binding edge cases

## [0.2.1] - 2023-11-01

### Added
- Support for Python 3.12
- Improved error handling and reporting
- Better documentation and examples

### Changed
- Updated Rust dependencies for security patches
- Optimized request routing performance

## [0.2.0] - 2023-10-15

### Added
- Dynamic route parameters with `{param}` syntax
- Support for complex nested routes
- Enhanced JSON response handling
- Comprehensive test suite

### Changed
- Major refactoring of core routing logic
- Improved FFI interface design
- Better error propagation from Rust to Python

### Performance
- 40% improvement in routing performance
- Reduced memory allocation overhead
- Faster startup times

## [0.1.0] - 2023-09-01

### Added
- Initial alpha release
- Basic HTTP server functionality
- Simple route registration
- GET and POST method support
- Basic Python-Rust FFI integration

### Known Issues
- Limited error handling
- Basic route matching only
- Memory usage not optimized
- Limited platform testing

---

## Version Support Policy

- **Major versions**: Supported for 2 years after release
- **Minor versions**: Supported until next major version
- **Patch versions**: Supported until next minor version
- **Security patches**: Backported to supported versions

## Migration Guides

### Upgrading from 0.x to 1.0

1. **Project Structure**: If you have a custom build setup, update paths:
   - Python code: `sufast/` → `python/sufast/`
   - Rust code: `server_rust/` → `rust-core/`

2. **Dependencies**: Update your development dependencies:
   ```bash
   pip install sufast[dev]  # For development dependencies
   ```

3. **Testing**: Update test imports if you were importing internal modules

4. **Build Process**: Use new build scripts:
   ```bash
   python scripts/build.py all
   python scripts/test.py all
   ```

### Breaking Changes from 0.x

- **Internal API**: Some internal functions renamed for clarity
- **Error Format**: Error response format slightly changed for consistency
- **Build System**: New build system requires Python 3.8+ and Rust 1.70+

## Contributing to Changelog

When contributing to Sufast:

1. Add your changes to the `[Unreleased]` section
2. Use the categories: Added, Changed, Deprecated, Removed, Fixed, Security
3. Include performance impacts if relevant
4. Reference issue numbers where applicable

Example:
```markdown
### Added
- New feature X that improves Y ([#123](https://github.com/shohan-dev/sufast/issues/123))

### Performance  
- 15% improvement in request throughput
- Reduced memory usage by 10MB on average workloads
```
