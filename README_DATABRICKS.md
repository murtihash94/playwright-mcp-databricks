# Deploying Playwright MCP Server on Databricks Apps

This guide explains how to deploy the Playwright Model Context Protocol (MCP) server as a Databricks App. This deployment allows you to use browser automation capabilities through the MCP protocol directly within your Databricks environment.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Architecture](#architecture)
- [Local Development](#local-development)
- [Deployment Methods](#deployment-methods)
  - [Using databricks bundle CLI](#using-databricks-bundle-cli)
  - [Using databricks apps CLI](#using-databricks-apps-cli)
- [Connecting to the Server](#connecting-to-the-server)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## Overview

The Playwright MCP Server on Databricks Apps provides:

- **Browser automation via MCP**: Access all Playwright browser automation tools through the Model Context Protocol
- **Headless operation**: Runs in headless mode suitable for server environments
- **Secure access**: Authentication via Databricks tokens
- **Scalable deployment**: Runs as a Databricks App with managed infrastructure

## Prerequisites

Before deploying, ensure you have:

1. **Databricks CLI** installed and configured:
   ```bash
   pip install databricks-cli
   databricks auth login --profile your-profile-name
   ```

2. **uv** (Python package manager):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Node.js 18+** (for the Playwright engine):
   ```bash
   # On Databricks Apps, Node.js is typically available
   # For local development, install from nodejs.org
   ```

4. **Databricks workspace access** with permissions to:
   - Create and deploy apps
   - Access the workspace file system

## Architecture

The deployment consists of:

```
┌─────────────────────────────────────┐
│   Databricks App Container          │
│                                     │
│  ┌────────────────────────────┐   │
│  │   FastAPI Application       │   │
│  │   (Python wrapper)          │   │
│  └──────────┬─────────────────┘   │
│             │                       │
│  ┌──────────▼─────────────────┐   │
│  │   Playwright MCP Server     │   │
│  │   (Node.js process)         │   │
│  └──────────┬─────────────────┘   │
│             │                       │
│  ┌──────────▼─────────────────┐   │
│  │   Chromium Browser          │   │
│  │   (headless)                │   │
│  └────────────────────────────┘   │
└─────────────────────────────────────┘
          │
          │ SSE/HTTP
          ▼
    MCP Clients
```

**Components:**
- **FastAPI wrapper**: Provides HTTP endpoints and manages the Node.js subprocess
- **Node.js MCP server**: The core Playwright automation engine
- **Chromium browser**: Headless browser for automation tasks

## Local Development

Test the server locally before deploying:

1. **Install dependencies**:
   ```bash
   # Install Python dependencies
   uv sync
   
   # Install Node.js dependencies
   npm install
   ```

2. **Start the server**:
   ```bash
   # Using uv
   uv run playwright-mcp-server
   
   # Or using uvicorn directly
   uvicorn playwright_mcp_databricks.app:app --reload --port 8000
   ```

3. **Test the server**:
   ```bash
   # Check health endpoint
   curl http://localhost:8000/health
   
   # View the landing page
   open http://localhost:8000
   ```

## Deployment Methods

There are two ways to deploy the server on Databricks Apps:

### Using databricks bundle CLI

The `databricks bundle` CLI provides a declarative way to deploy apps using configuration files.

#### Step 1: Build the wheel

```bash
cd /path/to/playwright-mcp-databricks
uv build --wheel
```

This creates a `.build` directory with:
- Python wheel package
- Node.js dependencies (package.json, cli.js, etc.)
- App configuration (app.yaml)

#### Step 2: Deploy the bundle

```bash
databricks bundle deploy -p your-profile-name
```

This command:
- Syncs the `.build` directory to Databricks workspace
- Creates/updates the app configuration
- Prepares the app for execution

#### Step 3: Start the app

```bash
databricks bundle run playwright-mcp-on-apps -p your-profile-name
```

The app will be available at:
```
https://your-workspace-url.databricksapps.com/api/mcp/
```

### Using databricks apps CLI

The `databricks apps` CLI provides direct control over app lifecycle.

#### Step 1: Build the wheel

```bash
cd /path/to/playwright-mcp-databricks
uv build --wheel
```

#### Step 2: Create the app

```bash
databricks apps create playwright-mcp-server -p your-profile-name
```

#### Step 3: Upload source code

```bash
DATABRICKS_USERNAME=$(databricks current-user me | jq -r .userName)
databricks sync .build "/Users/$DATABRICKS_USERNAME/playwright-mcp-server" -p your-profile-name
```

#### Step 4: Deploy and start

```bash
databricks apps deploy playwright-mcp-server \
  --source-code-path "/Workspace/Users/$DATABRICKS_USERNAME/playwright-mcp-server" \
  -p your-profile-name

databricks apps start playwright-mcp-server -p your-profile-name
```

#### Step 5: Get the app URL

```bash
databricks apps get playwright-mcp-server -p your-profile-name
```

## Connecting to the Server

### Using Python (with Databricks SDK)

```python
from databricks.sdk import WorkspaceClient
from databricks_mcp import DatabricksOAuthClientProvider
from mcp.client.streamable_http import streamablehttp_client as connect
from mcp import ClientSession

client = WorkspaceClient()

async def main():
    # Connect to the Playwright MCP server
    app_url = "https://your-app-url.databricksapps.com/api/mcp/"
    
    async with connect(app_url, auth=DatabricksOAuthClientProvider(client)) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()
            
            # Use Playwright tools
            result = await session.call_tool("browser_navigate", {
                "url": "https://example.com"
            })
            
            # Get page snapshot
            snapshot = await session.call_tool("browser_snapshot", {})
            print(snapshot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Using Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "playwright-databricks": {
      "url": "https://your-app-url.databricksapps.com/api/mcp/",
      "headers": {
        "Authorization": "Bearer YOUR_DATABRICKS_TOKEN"
      }
    }
  }
}
```

Get your token:
```bash
databricks auth token -p your-profile-name
```

### Using MCP Inspector

```bash
npx @modelcontextprotocol/inspector \
  --url https://your-app-url.databricksapps.com/api/mcp/ \
  --header "Authorization: Bearer YOUR_DATABRICKS_TOKEN"
```

## Configuration

### Browser Options

The server runs with these default Playwright options:
- **Browser**: Chromium (headless)
- **Sandbox**: Disabled (required for container environments)
- **Viewport**: Default size (can be configured)

### Environment Variables

You can configure the app by modifying `app.yaml`:

```yaml
command: ["uv", "run", "playwright-mcp-server"]
env:
  - name: PLAYWRIGHT_BROWSERS_PATH
    value: /tmp/playwright
  - name: NODE_OPTIONS
    value: "--max-old-space-size=2048"
```

### Resource Limits

Databricks Apps automatically manage resources. For heavy browser automation:
- Consider increasing memory limits
- Use app instance types with more resources
- Implement connection pooling for multiple clients

## Troubleshooting

### App won't start

**Check logs**:
```bash
databricks apps logs playwright-mcp-server -p your-profile-name
```

**Common issues**:
- Node.js not found: Ensure Node.js is available in the app environment
- Chromium installation failed: Check browser installation in logs
- Permission errors: Verify app service principal has necessary permissions

### Connection refused

**Verify app is running**:
```bash
databricks apps get playwright-mcp-server -p your-profile-name
```

**Check the URL**:
- Must end with `/api/mcp/` (note the trailing slash)
- Use HTTPS, not HTTP
- Verify token is valid: `databricks auth token -p your-profile-name`

### Browser automation fails

**Common issues**:
- Timeout errors: Increase navigation timeout in MCP calls
- Element not found: Page may not be fully loaded; add wait commands
- Sandbox errors: Verify `--no-sandbox` flag is set

**Debug mode**:
Temporarily enable headed mode for debugging (local development only):
```python
# In app.py, modify the command to remove --headless
cmd = ["node", str(cli_path), "--browser", "chromium", "--no-sandbox"]
```

### Performance issues

**Optimize browser usage**:
- Close tabs when done: `await session.call_tool("browser_close", {})`
- Use shared browser context if appropriate
- Limit concurrent browser operations

**Monitor resources**:
```bash
databricks apps get playwright-mcp-server -p your-profile-name | jq .resources
```

## Available Tools

The server exposes all Playwright MCP tools:

**Core automation**:
- `browser_navigate` - Navigate to URLs
- `browser_click` - Click elements
- `browser_type` - Type text
- `browser_snapshot` - Get accessibility tree
- `browser_take_screenshot` - Capture screenshots
- `browser_evaluate` - Run JavaScript

**Advanced features**:
- `browser_tabs` - Manage multiple tabs
- `browser_handle_dialog` - Handle alerts/prompts
- `browser_network_requests` - Inspect network traffic
- `browser_console_messages` - View console logs

For the complete list, see the [Playwright MCP documentation](https://github.com/microsoft/playwright-mcp#tools).

## Security Considerations

- **Authentication**: Always use Databricks token authentication
- **Authorization**: Service principal needs appropriate workspace permissions
- **Network isolation**: Consider deploying in a private network if handling sensitive data
- **Secrets management**: Never hardcode tokens; use Databricks secrets

## Next Steps

- Explore [Playwright documentation](https://playwright.dev) for browser automation patterns
- Review [MCP protocol specification](https://modelcontextprotocol.io)
- Check [Databricks Apps documentation](https://docs.databricks.com/apps/) for platform features
- Join the [Playwright community](https://github.com/microsoft/playwright/discussions)

## Support

For issues related to:
- **Playwright MCP**: [GitHub Issues](https://github.com/microsoft/playwright-mcp/issues)
- **Databricks Apps**: [Databricks Support](https://docs.databricks.com/support)
- **MCP Protocol**: [MCP GitHub](https://github.com/modelcontextprotocol)
