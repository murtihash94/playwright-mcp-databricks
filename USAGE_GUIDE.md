# Playwright MCP Server - Databricks Apps Deployment Guide

## Overview

This repository has been updated to support deployment as a Databricks App. The Playwright Model Context Protocol (MCP) server now includes:

1. **Python FastAPI wrapper** - Wraps the Node.js MCP server for Databricks Apps compatibility
2. **Databricks bundle configuration** - Deploy using `databricks bundle` or `databricks apps` CLI
3. **Web landing page** - Beautiful UI showing connection details and examples
4. **Deployment verification** - Scripts to validate your configuration before deploying
5. **Comprehensive documentation** - Step-by-step guides for all deployment scenarios

## Quick Start

### 1. Prerequisites

```bash
# Install tools
pip install uv databricks-cli

# Authenticate with Databricks
databricks auth login --profile my-profile
```

### 2. Build the Package

```bash
# Build wheel and create .build directory
uv build --wheel
```

This creates a `.build` directory with:
- Python wheel package
- Node.js MCP server files
- App configuration

### 3. Deploy to Databricks

**Option A: Using databricks bundle (recommended)**

```bash
# Deploy the bundle
databricks bundle deploy -p my-profile

# Start the app
databricks bundle run playwright-mcp-on-apps -p my-profile
```

**Option B: Using databricks apps**

```bash
# Create and deploy app
databricks apps create playwright-mcp-server -p my-profile
DATABRICKS_USERNAME=$(databricks current-user me | jq -r .userName)
databricks sync .build "/Users/$DATABRICKS_USERNAME/playwright-mcp" -p my-profile
databricks apps deploy playwright-mcp-server \
  --source-code-path "/Workspace/Users/$DATABRICKS_USERNAME/playwright-mcp" \
  -p my-profile
databricks apps start playwright-mcp-server -p my-profile
```

### 4. Get Your App URL

```bash
databricks apps get playwright-mcp-on-apps -p my-profile
```

Your server will be available at:
```
https://your-workspace.databricksapps.com/api/mcp/
```

## File Structure

```
playwright-mcp-databricks/
├── src/
│   └── playwright_mcp_databricks/
│       ├── __init__.py           # Package initialization
│       ├── app.py                # FastAPI application
│       ├── main.py               # Entry point
│       └── static/
│           └── index.html        # Landing page
├── hooks/
│   └── apps_build.py            # Build hook for Databricks Apps
├── databricks.yml               # Databricks bundle configuration
├── app.yaml                     # App runtime configuration
├── pyproject.toml               # Python package configuration
├── requirements.txt             # Python dependencies
├── verify_deployment.py         # Deployment verification script
├── test_package.py              # Package tests
├── README_DATABRICKS.md         # Comprehensive deployment docs
├── EXAMPLE_DEPLOYMENT.md        # Quick deployment examples
└── (existing Node.js files)     # Original Playwright MCP files
```

## Architecture

The deployment uses a layered architecture:

```
┌─────────────────────────────────────────────┐
│        Databricks App Container             │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │     FastAPI Application (Python)       │ │
│  │  - HTTP endpoints (/api/mcp/)         │ │
│  │  - Landing page (/)                   │ │
│  │  - Health checks                      │ │
│  └─────────────┬─────────────────────────┘ │
│                │ subprocess                 │
│  ┌─────────────▼─────────────────────────┐ │
│  │   Playwright MCP Server (Node.js)     │ │
│  │  - MCP protocol implementation        │ │
│  │  - Browser automation tools           │ │
│  └─────────────┬─────────────────────────┘ │
│                │                            │
│  ┌─────────────▼─────────────────────────┐ │
│  │      Chromium Browser (headless)      │ │
│  │  - Web page rendering                 │ │
│  │  - JavaScript execution               │ │
│  └───────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
                 │
                 │ HTTPS/SSE
                 ▼
          ┌──────────────┐
          │ MCP Clients  │
          │ - Python SDK │
          │ - Claude     │
          │ - Others     │
          └──────────────┘
```

## Using the Deployed Server

### Python Client

```python
from databricks.sdk import WorkspaceClient
from databricks_mcp import DatabricksOAuthClientProvider
from mcp.client.streamable_http import streamablehttp_client as connect
from mcp import ClientSession

client = WorkspaceClient()

async def automate_browser():
    app_url = "https://your-app-url.databricksapps.com/api/mcp/"
    
    async with connect(app_url, auth=DatabricksOAuthClientProvider(client)) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize connection
            await session.initialize()
            
            # Navigate to a URL
            result = await session.call_tool("browser_navigate", {
                "url": "https://example.com"
            })
            
            # Take a snapshot of the page (accessibility tree)
            snapshot = await session.call_tool("browser_snapshot", {})
            print(snapshot)
            
            # Click an element
            await session.call_tool("browser_click", {
                "element": "button Login",
                "ref": "element_reference_from_snapshot"
            })
            
            # Type text
            await session.call_tool("browser_type", {
                "element": "textbox Username",
                "ref": "element_reference",
                "text": "myusername"
            })
            
            # Take a screenshot
            await session.call_tool("browser_take_screenshot", {
                "filename": "page.png"
            })

# Run the automation
import asyncio
asyncio.run(automate_browser())
```

### Claude Desktop

Add to `claude_desktop_config.json`:

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
databricks auth token -p my-profile
```

### MCP Inspector

```bash
npx @modelcontextprotocol/inspector \
  --url https://your-app-url.databricksapps.com/api/mcp/ \
  --header "Authorization: Bearer YOUR_TOKEN"
```

## Available Tools

The server exposes all Playwright MCP tools. Key tools include:

### Navigation & Page Management
- `browser_navigate` - Navigate to URLs
- `browser_navigate_back` - Go back in history
- `browser_close` - Close the browser
- `browser_tabs` - Manage multiple tabs

### Element Interaction
- `browser_click` - Click elements
- `browser_type` - Type text into fields
- `browser_fill_form` - Fill multiple form fields at once
- `browser_select_option` - Select dropdown options
- `browser_hover` - Hover over elements
- `browser_drag` - Drag and drop

### Page Inspection
- `browser_snapshot` - Get accessibility tree (LLM-friendly)
- `browser_take_screenshot` - Capture visual screenshots
- `browser_console_messages` - View console logs
- `browser_network_requests` - Inspect network activity

### Advanced
- `browser_evaluate` - Execute JavaScript
- `browser_handle_dialog` - Handle alerts/prompts
- `browser_wait_for` - Wait for conditions
- `browser_press_key` - Keyboard input

For complete tool documentation, see [Playwright MCP Tools](https://github.com/microsoft/playwright-mcp#tools).

## Verification & Testing

### Before Deployment

Run the verification script to check your setup:

```bash
python verify_deployment.py
```

This validates:
- Required files exist
- Build process works
- Configuration is correct
- Dependencies are available

### Test Package Structure

Run package tests:

```bash
python test_package.py
```

This verifies:
- Python modules import correctly
- FastAPI app structure is valid
- Static files are present

### Local Testing

Test the server locally before deploying:

```bash
# Install dependencies
pip install -r requirements.txt
npm install

# Start the server
uvicorn playwright_mcp_databricks.app:app --reload --port 8000
```

Visit http://localhost:8000 to see the landing page.

## Configuration

### Browser Options

Modify `src/playwright_mcp_databricks/app.py` to configure browser options:

```python
cmd = [
    "node",
    str(cli_path),
    "--headless",           # Run headless (required for Databricks)
    "--browser", "chromium", # Browser type
    "--no-sandbox",         # Disable sandbox (required for containers)
    "--timeout-navigation", "60000",  # Navigation timeout
    "--viewport-size", "1280x720",    # Viewport size
]
```

### Environment Variables

Configure via `app.yaml`:

```yaml
command: ["uv", "run", "playwright-mcp-server"]
env:
  - name: PLAYWRIGHT_BROWSERS_PATH
    value: /tmp/playwright
  - name: NODE_OPTIONS
    value: "--max-old-space-size=2048"
```

## Troubleshooting

### App Won't Start

Check logs:
```bash
databricks apps logs playwright-mcp-on-apps -p my-profile
```

Common issues:
- **Node.js not found**: Ensure Node.js is available in the container
- **Permission errors**: Check service principal permissions
- **Port conflicts**: Verify port 8000 is available

### Connection Issues

Verify the app URL:
```bash
databricks apps get playwright-mcp-on-apps -p my-profile | jq .url
```

Check:
- URL must end with `/api/mcp/` (with trailing slash)
- Token is valid: `databricks auth token -p my-profile`
- Network connectivity to Databricks workspace

### Browser Automation Fails

Common issues:
- **Timeout errors**: Increase timeouts in tool calls
- **Element not found**: Wait for page to load fully
- **Sandbox errors**: Verify `--no-sandbox` is set

## Documentation

- **[README_DATABRICKS.md](./README_DATABRICKS.md)** - Complete deployment guide
- **[EXAMPLE_DEPLOYMENT.md](./EXAMPLE_DEPLOYMENT.md)** - Quick deployment examples
- **[README.md](./README.md)** - Main Playwright MCP documentation

## Security Considerations

1. **Authentication**: Always use Databricks token authentication
2. **Authorization**: Grant minimal necessary permissions to service principal
3. **Network**: Deploy in private networks for sensitive workloads
4. **Secrets**: Use Databricks secrets for sensitive configuration
5. **Monitoring**: Enable logging and monitoring for production deployments

## Performance Tips

1. **Resource allocation**: Configure appropriate instance types for your workload
2. **Connection pooling**: Reuse browser contexts when possible
3. **Cleanup**: Always close tabs/browser when done
4. **Timeout tuning**: Adjust timeouts based on your network and page complexity

## Support & Contributing

- **Issues**: Report bugs at [GitHub Issues](https://github.com/murtihash94/playwright-mcp-databricks/issues)
- **Playwright MCP**: [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp)
- **Databricks MCP Template**: [murtihash94/custom_mcp_server_databricks](https://github.com/murtihash94/custom_mcp_server_databricks)
- **MCP Protocol**: [modelcontextprotocol.io](https://modelcontextprotocol.io)

## License

Apache-2.0 (same as Playwright MCP)

## Acknowledgments

- Based on [Playwright MCP](https://github.com/microsoft/playwright-mcp) by Microsoft
- Databricks Apps deployment pattern from [Databricks Labs MCP](https://github.com/databrickslabs/mcp)
- Template from [custom_mcp_server_databricks](https://github.com/murtihash94/custom_mcp_server_databricks)
