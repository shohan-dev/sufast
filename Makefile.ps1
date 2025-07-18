# Sufast Development Commands
# 
# PowerShell script equivalent to Makefile for cross-platform development
#
# Usage: 
#   .\Makefile.ps1 <command>
#   
# Available commands:
#   help        - Show this help message
#   setup       - Set up development environment
#   build       - Build all components
#   test        - Run all tests
#   lint        - Run all linting tools
#   format      - Auto-format code
#   clean       - Clean build artifacts
#   install     - Install package locally
#   release     - Prepare release build

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "Sufast Development Commands" -ForegroundColor Green
    Write-Host "===========================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Available commands:" -ForegroundColor Yellow
    Write-Host "  help        - Show this help message"
    Write-Host "  setup       - Set up development environment"
    Write-Host "  build       - Build all components"
    Write-Host "  test        - Run all tests"
    Write-Host "  lint        - Run all linting tools"
    Write-Host "  format      - Auto-format code"
    Write-Host "  clean       - Clean build artifacts"
    Write-Host "  install     - Install package locally"
    Write-Host "  release     - Prepare release build"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\Makefile.ps1 setup"
    Write-Host "  .\Makefile.ps1 build"
    Write-Host "  .\Makefile.ps1 test"
}

function Setup-Environment {
    Write-Host "🔧 Setting up development environment..." -ForegroundColor Green
    
    # Check prerequisites
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Error "Python is not installed or not in PATH"
        exit 1
    }
    
    if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
        Write-Error "Rust/Cargo is not installed or not in PATH"
        exit 1
    }
    
    # Set up Python environment
    Write-Host "🐍 Setting up Python environment..."
    Set-Location python
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -e .[dev]
    Set-Location ..
    
    # Check Rust setup
    Write-Host "🦀 Checking Rust setup..."
    Set-Location rust-core
    cargo check
    Set-Location ..
    
    Write-Host "✅ Development environment ready!" -ForegroundColor Green
}

function Build-All {
    Write-Host "🏗️ Building all components..." -ForegroundColor Green
    python scripts/build.py all
}

function Test-All {
    Write-Host "🧪 Running all tests..." -ForegroundColor Green
    python scripts/test.py all
}

function Lint-All {
    Write-Host "🔍 Running all linting tools..." -ForegroundColor Green
    python scripts/lint.py all
}

function Format-Code {
    Write-Host "🎨 Auto-formatting code..." -ForegroundColor Green
    python scripts/lint.py format
}

function Clean-Build {
    Write-Host "🧹 Cleaning build artifacts..." -ForegroundColor Green
    
    # Clean Python artifacts
    if (Test-Path "python/build") { Remove-Item -Recurse -Force "python/build" }
    if (Test-Path "python/dist") { Remove-Item -Recurse -Force "python/dist" }
    Get-ChildItem -Path "python" -Filter "*.egg-info" -Recurse | Remove-Item -Recurse -Force
    Get-ChildItem -Path "python" -Filter "__pycache__" -Recurse | Remove-Item -Recurse -Force
    
    # Clean Rust artifacts
    Set-Location rust-core
    cargo clean
    Set-Location ..
    
    # Clean root artifacts
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "sufast.egg-info") { Remove-Item -Recurse -Force "sufast.egg-info" }
    
    Write-Host "✅ Cleanup completed!" -ForegroundColor Green
}

function Install-Local {
    Write-Host "📦 Installing package locally..." -ForegroundColor Green
    Build-All
    Set-Location python
    pip install -e .
    Set-Location ..
    Write-Host "✅ Package installed!" -ForegroundColor Green
}

function Prepare-Release {
    Write-Host "🚀 Preparing release build..." -ForegroundColor Green
    
    # Clean first
    Clean-Build
    
    # Run full test suite
    if (-not (Test-All)) {
        Write-Error "Tests failed! Cannot prepare release."
        exit 1
    }
    
    # Run linting
    if (-not (Lint-All)) {
        Write-Error "Linting failed! Cannot prepare release."
        exit 1
    }
    
    # Build release
    Build-All
    
    Write-Host "✅ Release build ready!" -ForegroundColor Green
    Write-Host "📦 Distribution files are in python/dist/" -ForegroundColor Yellow
}

# Command routing
switch ($Command.ToLower()) {
    "help" { Show-Help }
    "setup" { Setup-Environment }
    "build" { Build-All }
    "test" { Test-All }
    "lint" { Lint-All }
    "format" { Format-Code }
    "clean" { Clean-Build }
    "install" { Install-Local }
    "release" { Prepare-Release }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host ""
        Show-Help
        exit 1
    }
}
