#!/usr/bin/env python3
"""
Simple test to verify the FastAPI app can be imported and structured correctly.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        import playwright_mcp_databricks
        print(f"✓ playwright_mcp_databricks version: {playwright_mcp_databricks.__version__}")
    except Exception as e:
        print(f"✗ Failed to import playwright_mcp_databricks: {e}")
        return False
    
    try:
        from playwright_mcp_databricks.app import app
        print(f"✓ FastAPI app imported successfully")
    except Exception as e:
        print(f"✗ Failed to import FastAPI app: {e}")
        return False
    
    try:
        from playwright_mcp_databricks.main import main
        print(f"✓ Main entry point imported successfully")
    except Exception as e:
        print(f"✗ Failed to import main: {e}")
        return False
    
    return True


def test_app_structure():
    """Test that the FastAPI app has expected endpoints."""
    print("\nTesting FastAPI app structure...")
    
    try:
        from playwright_mcp_databricks.app import app
        
        # Check routes
        routes = [route.path for route in app.routes]
        expected_routes = ["/", "/health", "/mcp/sse", "/api/mcp/"]
        
        for route in expected_routes:
            if any(route in r for r in routes):
                print(f"✓ Route {route} is defined")
            else:
                print(f"✗ Route {route} is missing")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Error testing app structure: {e}")
        return False


def test_static_files():
    """Test that static files exist."""
    print("\nTesting static files...")
    
    static_dir = Path(__file__).parent / "src" / "playwright_mcp_databricks" / "static"
    index_html = static_dir / "index.html"
    
    if index_html.exists():
        print(f"✓ index.html exists: {index_html}")
        
        # Check it has content
        content = index_html.read_text()
        if "Playwright" in content and "MCP" in content:
            print(f"✓ index.html contains expected content")
            return True
        else:
            print(f"✗ index.html missing expected content")
            return False
    else:
        print(f"✗ index.html not found: {index_html}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Playwright MCP Databricks Package")
    print("=" * 60)
    
    all_passed = True
    
    if not test_imports():
        all_passed = False
    
    if not test_app_structure():
        all_passed = False
    
    if not test_static_files():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
