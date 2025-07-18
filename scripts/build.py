#!/usr/bin/env python3
"""
Build script for Sufast project.
Builds Rust libraries for all platforms and prepares Python package.
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result

def build_rust():
    """Build the Rust core library."""
    print("🦀 Building Rust core...")
    
    rust_dir = Path("rust-core")
    if not rust_dir.exists():
        print("❌ rust-core directory not found!")
        return False
    
    # Build in release mode
    try:
        run_command(["cargo", "build", "--release"], cwd=rust_dir)
        print("✅ Rust build successful!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Rust build failed: {e}")
        return False

def copy_rust_artifacts():
    """Copy built Rust libraries to Python package."""
    print("📦 Copying Rust artifacts...")
    
    rust_target = Path("rust-core/target/release")
    python_pkg = Path("python/sufast")
    
    if not python_pkg.exists():
        python_pkg.mkdir(parents=True)
    
    # Determine library extension based on platform
    system = platform.system()
    if system == "Windows":
        lib_name = "sufast_server.dll"
    elif system == "Darwin":
        lib_name = "libsufast_server.dylib"
    else:  # Linux and others
        lib_name = "libsufast_server.so"
        # On Linux, copy as .so instead of lib*.so
        target_name = "sufast_server.so"
    
    source_lib = rust_target / lib_name
    if system == "Linux":
        target_lib = python_pkg / target_name
    else:
        target_lib = python_pkg / lib_name
    
    if source_lib.exists():
        shutil.copy2(source_lib, target_lib)
        print(f"✅ Copied {source_lib} to {target_lib}")
        return True
    else:
        print(f"❌ Library not found: {source_lib}")
        return False

def build_python():
    """Build the Python package."""
    print("🐍 Building Python package...")
    
    python_dir = Path("python")
    if not python_dir.exists():
        print("❌ python directory not found!")
        return False
    
    try:
        # Clean previous builds
        for dir_name in ["build", "dist", "*.egg-info"]:
            for path in python_dir.glob(dir_name):
                if path.is_dir():
                    shutil.rmtree(path)
                    print(f"🧹 Cleaned {path}")
        
        # Build package
        run_command([sys.executable, "-m", "build"], cwd=python_dir)
        print("✅ Python package built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Python build failed: {e}")
        return False

def run_tests():
    """Run the test suite."""
    print("🧪 Running tests...")
    
    # Run Rust tests
    print("🦀 Running Rust tests...")
    try:
        run_command(["cargo", "test"], cwd="rust-core")
        print("✅ Rust tests passed!")
    except subprocess.CalledProcessError:
        print("❌ Rust tests failed!")
        return False
    
    # Run Python tests
    print("🐍 Running Python tests...")
    try:
        run_command([sys.executable, "-m", "pytest", "tests/", "-v"], cwd="python")
        print("✅ Python tests passed!")
    except subprocess.CalledProcessError:
        print("❌ Python tests failed!")
        return False
    
    return True

def main():
    """Main build function."""
    print("🚀 Starting Sufast build process...")
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "rust":
            success = build_rust()
        elif command == "python":
            success = build_python()
        elif command == "copy":
            success = copy_rust_artifacts()
        elif command == "test":
            success = run_tests()
        elif command == "all":
            success = (
                build_rust() and
                copy_rust_artifacts() and
                build_python() and
                run_tests()
            )
        else:
            print(f"Unknown command: {command}")
            print("Available commands: rust, python, copy, test, all")
            return 1
    else:
        # Default: build everything
        success = (
            build_rust() and
            copy_rust_artifacts() and
            build_python()
        )
    
    if success:
        print("🎉 Build completed successfully!")
        return 0
    else:
        print("💥 Build failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
