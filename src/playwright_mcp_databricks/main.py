"""
Main entry point for the Playwright MCP server on Databricks Apps.
"""
import uvicorn


def main():
    """Start the Playwright MCP server."""
    uvicorn.run(
        "playwright_mcp_databricks.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
