"""
FastAPI application for Playwright MCP Server on Databricks Apps.

This module wraps the Node.js based Playwright MCP server and exposes it
via FastAPI with streamable HTTP transport for use on Databricks Apps.
"""
import subprocess
import asyncio
import os
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.session import ServerSession
from mcp.server.sse import SseServerTransport

# Get the static directory path
STATIC_DIR = Path(__file__).parent / "static"

# Create FastAPI app
app = FastAPI(
    title="Playwright MCP Server",
    description="Browser automation capabilities using Playwright via Model Context Protocol",
    version="0.0.43"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve the landing page."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "playwright-mcp-server"}


async def handle_sse_connection(request: Request):
    """
    Handle SSE connection by proxying to the Node.js Playwright MCP server.
    
    This creates a subprocess running the Node.js MCP server and establishes
    bidirectional communication via stdin/stdout.
    """
    # Find the Node.js MCP server CLI
    # In production, this will be in the installed package location
    cli_path = Path(__file__).parent.parent.parent / "cli.js"
    if not cli_path.exists():
        # Try alternative location (installed package)
        import sys
        for path in sys.path:
            test_path = Path(path) / "cli.js"
            if test_path.exists():
                cli_path = test_path
                break
    
    # Start the Node.js MCP server as a subprocess
    # Use headless mode and appropriate options for Databricks Apps
    cmd = [
        "node",
        str(cli_path),
        "--headless",
        "--browser", "chromium",
        "--no-sandbox",
        "--port", "0"  # stdin/stdout mode
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    
    async def stream_response():
        """Stream responses from the MCP server."""
        try:
            # Read from the process stdout and stream to client
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                yield line
        finally:
            # Cleanup
            if process.returncode is None:
                process.terminate()
                await process.wait()
    
    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/mcp/sse")
@app.post("/mcp/sse")
async def mcp_sse_endpoint(request: Request):
    """
    MCP Server Sent Events endpoint.
    
    This endpoint provides SSE transport for the MCP protocol.
    """
    return await handle_sse_connection(request)


@app.get("/api/mcp/")
@app.post("/api/mcp/")
async def mcp_api_endpoint(request: Request):
    """
    Alternative MCP endpoint path (for compatibility with different clients).
    """
    return await handle_sse_connection(request)


# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
