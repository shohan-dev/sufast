#!/usr/bin/env python3
"""
Linting and code quality script for Sufast project.
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

def lint_python():
    """Run Python linting tools."""
    print("🐍 Linting Python code...")
    
    python_dir = Path("python")
    if not python_dir.exists():
        print("❌ python directory not found!")
        return False
    
    success = True
    
    # Black formatting check
    print("🔧 Checking Python formatting (black)...")
    if not run_command([sys.executable, "-m", "black", "--check", "."], cwd=python_dir, check=False):
        print("❌ Black formatting issues found. Run 'black .' to fix.")
        success = False
    
    # isort import sorting check
    print("📦 Checking import sorting (isort)...")
    if not run_command([sys.executable, "-m", "isort", "--check-only", "."], cwd=python_dir, check=False):
        print("❌ Import sorting issues found. Run 'isort .' to fix.")
        success = False
    
    # flake8 linting
    print("🔍 Running flake8 linting...")
    if not run_command([sys.executable, "-m", "flake8", "sufast/", "tests/"], cwd=python_dir, check=False):
        print("❌ Flake8 found issues.")
        success = False
    
    # mypy type checking
    print("🔬 Running mypy type checking...")
    if not run_command([sys.executable, "-m", "mypy", "sufast/"], cwd=python_dir, check=False):
        print("❌ MyPy found type issues.")
        success = False
    
    return success

def lint_rust():
    """Run Rust linting tools."""
    print("🦀 Linting Rust code...")
    
    rust_dir = Path("rust-core")
    if not rust_dir.exists():
        print("❌ rust-core directory not found!")
        return False
    
    success = True
    
    # Rust formatting check
    print("🔧 Checking Rust formatting...")
    if not run_command(["cargo", "fmt", "--check"], cwd=rust_dir, check=False):
        print("❌ Rust formatting issues found. Run 'cargo fmt' to fix.")
        success = False
    
    # Clippy linting
    print("🔍 Running Clippy linting...")
    if not run_command(["cargo", "clippy", "--", "-D", "warnings"], cwd=rust_dir, check=False):
        print("❌ Clippy found issues.")
        success = False
    
    return success

def security_audit():
    """Run security audits."""
    print("🔒 Running security audits...")
    
    success = True
    
    # Rust security audit
    print("🦀 Running Rust security audit...")
    if not run_command(["cargo", "audit"], cwd="rust-core", check=False):
        print("❌ Rust security audit found issues.")
        success = False
    
    # Python security audit
    print("🐍 Running Python security audit...")
    python_dir = Path("python")
    if python_dir.exists():
        if not run_command([sys.executable, "-m", "safety", "check"], cwd=python_dir, check=False):
            print("❌ Python safety audit found issues.")
            success = False
        
        if not run_command([sys.executable, "-m", "bandit", "-r", "sufast/"], cwd=python_dir, check=False):
            print("❌ Bandit security scan found issues.")
            success = False
    
    return success

def format_code():
    """Auto-format code."""
    print("🎨 Auto-formatting code...")
    
    # Format Python code
    python_dir = Path("python")
    if python_dir.exists():
        print("🐍 Formatting Python code...")
        run_command([sys.executable, "-m", "black", "."], cwd=python_dir, check=False)
        run_command([sys.executable, "-m", "isort", "."], cwd=python_dir, check=False)
    
    # Format Rust code
    rust_dir = Path("rust-core")
    if rust_dir.exists():
        print("🦀 Formatting Rust code...")
        run_command(["cargo", "fmt"], cwd=rust_dir, check=False)
    
    print("✅ Code formatting completed!")

def main():
    """Main linting function."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "python":
            success = lint_python()
        elif command == "rust":
            success = lint_rust()
        elif command == "security":
            success = security_audit()
        elif command == "format":
            format_code()
            return 0
        elif command == "all":
            success = (
                lint_python() and
                lint_rust() and
                security_audit()
            )
        else:
            print(f"Unknown command: {command}")
            print("Available commands: python, rust, security, format, all")
            return 1
    else:
        # Default: run all linting
        success = (
            lint_python() and
            lint_rust() and
            security_audit()
        )
    
    if success:
        print("🎉 All linting checks passed!")
        return 0
    else:
        print("💥 Some linting checks failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
