#!/usr/bin/env python3
"""
Test runner script for Sufast project.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Command failed with return code {result.returncode}")
        if result.stdout:
            print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return False
    else:
        print("✅ Command succeeded")
        if result.stdout:
            print(result.stdout)
        return True

def test_rust():
    """Run Rust tests."""
    print("🦀 Running Rust tests...")
    
    rust_dir = Path("rust-core")
    if not rust_dir.exists():
        print("❌ rust-core directory not found!")
        return False
    
    success = True
    
    # Unit tests
    print("🧪 Running Rust unit tests...")
    if not run_command(["cargo", "test", "--lib"], cwd=rust_dir, check=False):
        success = False
    
    # Integration tests
    print("🔗 Running Rust integration tests...")
    if not run_command(["cargo", "test", "--tests"], cwd=rust_dir, check=False):
        success = False
    
    # Doc tests
    print("📚 Running Rust doc tests...")
    if not run_command(["cargo", "test", "--doc"], cwd=rust_dir, check=False):
        success = False
    
    return success

def test_python():
    """Run Python tests."""
    print("🐍 Running Python tests...")
    
    python_dir = Path("python")
    if not python_dir.exists():
        print("❌ python directory not found!")
        return False
    
    success = True
    
    # Unit tests
    print("🧪 Running Python unit tests...")
    if not run_command([
        sys.executable, "-m", "pytest", 
        "tests/", "-v", 
        "--cov=sufast", 
        "--cov-report=xml",
        "--cov-report=html",
        "--cov-report=term-missing"
    ], cwd=python_dir, check=False):
        success = False
    
    return success

def benchmark_rust():
    """Run Rust benchmarks."""
    print("⚡ Running Rust benchmarks...")
    
    rust_dir = Path("rust-core")
    if not rust_dir.exists():
        print("❌ rust-core directory not found!")
        return False
    
    return run_command(["cargo", "bench"], cwd=rust_dir, check=False)

def benchmark_python():
    """Run Python benchmarks."""
    print("⚡ Running Python benchmarks...")
    
    python_dir = Path("python")
    if not python_dir.exists():
        print("❌ python directory not found!")
        return False
    
    return run_command([
        sys.executable, "-m", "pytest", 
        "tests/", "-v", 
        "--benchmark-only"
    ], cwd=python_dir, check=False)

def integration_tests():
    """Run integration tests."""
    print("🔗 Running integration tests...")
    
    python_dir = Path("python")
    if not python_dir.exists():
        print("❌ python directory not found!")
        return False
    
    return run_command([
        sys.executable, "-m", "pytest", 
        "tests/test_integration.py", "-v"
    ], cwd=python_dir, check=False)

def performance_tests():
    """Run performance tests."""
    print("🚀 Running performance tests...")
    
    success = True
    
    # Python performance tests
    python_dir = Path("python")
    if python_dir.exists():
        if not run_command([
            sys.executable, "-m", "pytest", 
            "tests/", "-v", 
            "-m", "performance"
        ], cwd=python_dir, check=False):
            success = False
    
    # Rust benchmarks
    if not benchmark_rust():
        success = False
    
    return success

def main():
    """Main test function."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "rust":
            success = test_rust()
        elif command == "python":
            success = test_python()
        elif command == "bench":
            success = benchmark_rust() and benchmark_python()
        elif command == "integration":
            success = integration_tests()
        elif command == "performance":
            success = performance_tests()
        elif command == "all":
            success = (
                test_rust() and
                test_python() and
                integration_tests()
            )
        elif command == "ci":
            # Comprehensive CI test suite
            success = (
                test_rust() and
                test_python() and
                integration_tests() and
                performance_tests()
            )
        else:
            print(f"Unknown command: {command}")
            print("Available commands: rust, python, bench, integration, performance, all, ci")
            return 1
    else:
        # Default: run all tests except benchmarks
        success = (
            test_rust() and
            test_python() and
            integration_tests()
        )
    
    if success:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
