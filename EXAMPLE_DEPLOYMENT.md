# Example: Deploying Playwright MCP to Databricks Apps

This example demonstrates how to deploy the Playwright MCP server to Databricks Apps.

## Prerequisites

```bash
# Install required tools
pip install databricks-cli uv

# Authenticate with Databricks
databricks auth login --profile my-profile
```

## Option 1: Deploy using databricks bundle

```bash
# Build the package
uv build --wheel

# Deploy the bundle
databricks bundle deploy -p my-profile

# Start the app
databricks bundle run playwright-mcp-on-apps -p my-profile

# Get the app URL
databricks apps get playwright-mcp-on-apps -p my-profile
```

## Option 2: Deploy using databricks apps

```bash
# Build the package
uv build --wheel

# Create the app
databricks apps create playwright-mcp-server -p my-profile

# Upload the build directory
DATABRICKS_USERNAME=$(databricks current-user me | jq -r .userName)
databricks sync .build "/Users/$DATABRICKS_USERNAME/playwright-mcp" -p my-profile

# Deploy and start
databricks apps deploy playwright-mcp-server \
  --source-code-path "/Workspace/Users/$DATABRICKS_USERNAME/playwright-mcp" \
  -p my-profile

databricks apps start playwright-mcp-server -p my-profile
```

## Using the deployed server

### Python example

```python
from databricks.sdk import WorkspaceClient
from databricks_mcp import DatabricksOAuthClientProvider
from mcp.client.streamable_http import streamablehttp_client as connect
from mcp import ClientSession

client = WorkspaceClient()

async def main():
    app_url = "https://your-app-url.databricksapps.com/api/mcp/"
    
    async with connect(app_url, auth=DatabricksOAuthClientProvider(client)) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # Navigate to a page
            await session.call_tool("browser_navigate", {"url": "https://example.com"})
            
            # Get snapshot
            snapshot = await session.call_tool("browser_snapshot", {})
            print(snapshot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Claude Desktop configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "playwright-databricks": {
      "url": "https://your-app-url.databricksapps.com/api/mcp/",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      }
    }
  }
}
```

Get your token:
```bash
databricks auth token -p my-profile
```

## Verifying the deployment

Run the verification script before deploying:

```bash
python verify_deployment.py
```

This checks:
- All required files are present
- Build process works correctly
- Configuration is valid
- Required commands are available

## Troubleshooting

### Check app status
```bash
databricks apps get playwright-mcp-server -p my-profile
```

### View logs
```bash
databricks apps logs playwright-mcp-server -p my-profile
```

### Test locally first
```bash
uvicorn playwright_mcp_databricks.app:app --reload --port 8000
```

Then visit http://localhost:8000 to see the landing page.
