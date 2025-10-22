#!/usr/bin/env python3
"""
Deployment verification script for Playwright MCP Server on Databricks Apps.

This script helps verify that your deployment is correctly configured before
deploying to Databricks Apps.
"""
import sys
import subprocess
from pathlib import Path
import json


def print_status(message: str, status: str = "info"):
    """Print a status message with color."""
    colors = {
        "info": "\033[94m",
        "success": "\033[92m",
        "warning": "\033[93m",
        "error": "\033[91m",
    }
    reset = "\033[0m"
    prefix = {
        "info": "ℹ",
        "success": "✓",
        "warning": "⚠",
        "error": "✗",
    }
    print(f"{colors[status]}{prefix[status]} {message}{reset}")


def check_file_exists(filepath: Path, description: str) -> bool:
    """Check if a required file exists."""
    if filepath.exists():
        print_status(f"{description}: {filepath}", "success")
        return True
    else:
        print_status(f"{description} not found: {filepath}", "error")
        return False


def check_command_available(command: str) -> bool:
    """Check if a command is available in PATH."""
    try:
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip().split("\n")[0]
            print_status(f"{command} is available: {version}", "success")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print_status(f"{command} is not available", "error")
    return False


def main():
    """Run deployment verification checks."""
    print_status("Starting deployment verification...", "info")
    print()
    
    all_checks_passed = True
    
    # Check required files
    print_status("Checking required files...", "info")
    root = Path(__file__).parent
    required_files = [
        (root / "pyproject.toml", "Python project configuration"),
        (root / "databricks.yml", "Databricks bundle configuration"),
        (root / "app.yaml", "App configuration"),
        (root / "hooks" / "apps_build.py", "Build hook"),
        (root / "package.json", "Node.js package configuration"),
        (root / "cli.js", "MCP CLI entry point"),
        (root / "index.js", "MCP server module"),
    ]
    
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            all_checks_passed = False
    print()
    
    # Check Python source files
    print_status("Checking Python source files...", "info")
    src_files = [
        (root / "src" / "playwright_mcp_databricks" / "__init__.py", "Package init"),
        (root / "src" / "playwright_mcp_databricks" / "app.py", "FastAPI application"),
        (root / "src" / "playwright_mcp_databricks" / "main.py", "Main entry point"),
        (root / "src" / "playwright_mcp_databricks" / "static" / "index.html", "Landing page"),
    ]
    
    for filepath, description in src_files:
        if not check_file_exists(filepath, description):
            all_checks_passed = False
    print()
    
    # Check required commands
    print_status("Checking required commands...", "info")
    required_commands = ["node", "npm", "uv", "databricks"]
    
    for command in required_commands:
        if not check_command_available(command):
            all_checks_passed = False
            if command == "databricks":
                print_status("Install with: pip install databricks-cli", "warning")
            elif command == "uv":
                print_status("Install with: pip install uv", "warning")
    print()
    
    # Test build process
    print_status("Testing build process...", "info")
    try:
        result = subprocess.run(
            ["uv", "build", "--wheel"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=root
        )
        if result.returncode == 0:
            print_status("Build successful", "success")
            
            # Check .build directory
            build_dir = root / ".build"
            if build_dir.exists():
                print_status(f"Build directory created: {build_dir}", "success")
                
                # List contents
                contents = list(build_dir.iterdir())
                print_status(f"Build contains {len(contents)} files:", "info")
                for item in sorted(contents):
                    print(f"  - {item.name}")
            else:
                print_status(".build directory not found", "error")
                all_checks_passed = False
        else:
            print_status(f"Build failed: {result.stderr}", "error")
            all_checks_passed = False
    except subprocess.TimeoutExpired:
        print_status("Build timed out", "error")
        all_checks_passed = False
    except FileNotFoundError:
        print_status("uv command not found - skipping build test", "warning")
    print()
    
    # Check databricks.yml structure
    print_status("Validating databricks.yml...", "info")
    try:
        import yaml
        with open(root / "databricks.yml", "r") as f:
            config = yaml.safe_load(f)
        
        if "bundle" in config and "name" in config["bundle"]:
            print_status(f"Bundle name: {config['bundle']['name']}", "success")
        else:
            print_status("Bundle configuration incomplete", "error")
            all_checks_passed = False
            
        if "resources" in config and "apps" in config["resources"]:
            print_status("App resources defined", "success")
        else:
            print_status("App resources not defined", "error")
            all_checks_passed = False
    except ImportError:
        print_status("PyYAML not installed - skipping YAML validation", "warning")
        print_status("Install with: pip install pyyaml", "info")
    except Exception as e:
        print_status(f"Error validating databricks.yml: {e}", "error")
        all_checks_passed = False
    print()
    
    # Summary
    print("=" * 60)
    if all_checks_passed:
        print_status("All checks passed! Ready to deploy.", "success")
        print()
        print_status("Next steps:", "info")
        print("  1. Authenticate: databricks auth login --profile your-profile")
        print("  2. Deploy: databricks bundle deploy -p your-profile")
        print("  3. Run: databricks bundle run playwright-mcp-on-apps -p your-profile")
        return 0
    else:
        print_status("Some checks failed. Please fix the issues above.", "error")
        return 1


if __name__ == "__main__":
    sys.exit(main())
