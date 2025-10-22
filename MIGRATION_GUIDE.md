# Migration Guide: Deploying Existing Playwright MCP to Databricks Apps

This guide helps you understand what changed and how to deploy your Playwright MCP server to Databricks Apps.

## What Changed?

### Added Components

The following files were added to enable Databricks Apps deployment:

#### Python Wrapper Package
```
src/playwright_mcp_databricks/
├── __init__.py           # Package metadata
├── app.py                # FastAPI wrapper for Node.js MCP server
├── main.py               # Entry point
└── static/
    └── index.html        # Web landing page
```

#### Databricks Configuration
```
databricks.yml            # Bundle deployment configuration
app.yaml                  # App runtime configuration
pyproject.toml            # Python package definition
hooks/apps_build.py       # Custom build hook for Databricks Apps
```

#### Development Tools
```
requirements.txt          # Python dependencies for development
verify_deployment.py      # Pre-deployment validation script
test_package.py          # Package structure tests
```

#### Documentation
```
README_DATABRICKS.md      # Comprehensive deployment guide
EXAMPLE_DEPLOYMENT.md     # Quick start examples
USAGE_GUIDE.md           # Complete usage documentation
MIGRATION_GUIDE.md       # This file
```

### Unchanged Components

**All original Playwright MCP functionality remains unchanged:**
- `package.json` - Node.js dependencies
- `cli.js` - MCP CLI entry point
- `index.js` - MCP server implementation
- All tools and capabilities work exactly as before

## Architecture Changes

### Before (Standard Deployment)

```
MCP Client → Node.js MCP Server → Chromium Browser
            (stdio/HTTP)
```

### After (Databricks Apps)

```
MCP Client → FastAPI Wrapper → Node.js MCP Server → Chromium Browser
  (HTTP)      (subprocess)         (stdio)
```

The FastAPI wrapper:
- Provides HTTP/SSE transport for MCP protocol
- Manages Node.js subprocess lifecycle
- Adds authentication layer
- Serves web landing page

## What Stays the Same

1. **All MCP tools** - No changes to available tools or their APIs
2. **Node.js MCP server** - Same implementation, same capabilities
3. **Playwright version** - No version changes
4. **Configuration options** - All Playwright options still available

## What's New

1. **HTTP/SSE transport** - Access MCP over HTTP (in addition to stdio)
2. **Web UI** - Landing page with connection info and examples
3. **Managed deployment** - Databricks handles infrastructure
4. **Enterprise auth** - Databricks token-based authentication
5. **Health checks** - Built-in monitoring endpoints

## Migration Scenarios

### Scenario 1: Using stdio locally → Keep using stdio locally

**No changes needed!** The existing setup still works:

```bash
npx @playwright/mcp@latest
```

### Scenario 2: Running HTTP server → Can deploy to Databricks

If you were running:
```bash
npx @playwright/mcp@latest --port 8931
```

You can now deploy to Databricks Apps:
```bash
uv build --wheel
databricks bundle deploy -p my-profile
databricks bundle run playwright-mcp-on-apps -p my-profile
```

### Scenario 3: Docker deployment → Can switch to Databricks Apps

If you were using:
```bash
docker run -p 8931:8931 mcr.microsoft.com/playwright/mcp
```

You can deploy to Databricks Apps for better integration:
```bash
uv build --wheel
databricks bundle deploy -p my-profile
databricks bundle run playwright-mcp-on-apps -p my-profile
```

Benefits:
- No Docker management needed
- Databricks handles scaling and availability
- Integrated authentication
- Better monitoring and logging

## Client Migration

### Python Client

**Before (local stdio):**
```python
import subprocess
from mcp import ClientSession
from mcp.client.stdio import stdio_client

async def main():
    server_params = {
        "command": "npx",
        "args": ["@playwright/mcp@latest"]
    }
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # Use tools...
```

**After (Databricks Apps):**
```python
from databricks.sdk import WorkspaceClient
from databricks_mcp import DatabricksOAuthClientProvider
from mcp.client.streamable_http import streamablehttp_client as connect
from mcp import ClientSession

async def main():
    client = WorkspaceClient()
    app_url = "https://your-app.databricksapps.com/api/mcp/"
    
    async with connect(app_url, auth=DatabricksOAuthClientProvider(client)) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # Use tools - same API!
```

### Claude Desktop

**Before (local):**
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

**After (Databricks Apps):**
```json
{
  "mcpServers": {
    "playwright": {
      "url": "https://your-app.databricksapps.com/api/mcp/",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      }
    }
  }
}
```

## Deployment Workflow

### Step 1: Verify Your Environment

```bash
# Check prerequisites
python verify_deployment.py
```

This validates:
- All required files present
- Build process works
- Configuration valid

### Step 2: Build Package

```bash
# Build the wheel and prepare .build directory
uv build --wheel
```

Output:
- `dist/playwright_mcp_databricks-*.whl` - Python package
- `.build/` - Databricks Apps deployment directory

### Step 3: Deploy

**Using databricks bundle (recommended):**
```bash
databricks bundle deploy -p my-profile
databricks bundle run playwright-mcp-on-apps -p my-profile
```

**Using databricks apps:**
```bash
databricks apps create playwright-mcp-server -p my-profile
DATABRICKS_USERNAME=$(databricks current-user me | jq -r .userName)
databricks sync .build "/Users/$DATABRICKS_USERNAME/playwright-mcp" -p my-profile
databricks apps deploy playwright-mcp-server \
  --source-code-path "/Workspace/Users/$DATABRICKS_USERNAME/playwright-mcp" \
  -p my-profile
databricks apps start playwright-mcp-server -p my-profile
```

### Step 4: Get App URL

```bash
databricks apps get playwright-mcp-on-apps -p my-profile
```

### Step 5: Update Clients

Update your client configurations to use the app URL with `/api/mcp/` suffix.

## Common Questions

### Q: Do I need to change my MCP tool calls?

**A: No!** All tools work exactly the same. Only the connection method changes.

### Q: Can I still use stdio locally?

**A: Yes!** The original CLI still works:
```bash
npx @playwright/mcp@latest
```

### Q: What about my custom configurations?

**A: They're preserved!** You can pass the same arguments to the Node.js server by modifying `src/playwright_mcp_databricks/app.py`:

```python
cmd = [
    "node",
    str(cli_path),
    "--headless",
    "--browser", "chromium",
    "--no-sandbox",
    "--viewport-size", "1920x1080",  # Your custom config
    "--user-agent", "MyAgent",        # Your custom config
]
```

### Q: Does this change Playwright version?

**A: No!** Same Playwright version (1.57.0-alpha-2025-10-16).

### Q: Can I run both local and Databricks deployments?

**A: Yes!** They're completely independent. Use local for development, Databricks for production.

### Q: What about the browser extension?

**A: Local only.** The browser extension (`--extension` flag) is designed for local development and won't work in Databricks Apps. For Databricks, use headless mode.

## Rollback

If you need to rollback:

1. **Keep using local deployment** - Nothing changed in the original code
2. **Delete Databricks app**:
   ```bash
   databricks apps delete playwright-mcp-on-apps -p my-profile
   ```
3. **Remove new files** (optional):
   ```bash
   rm -rf src/playwright_mcp_databricks
   rm databricks.yml app.yaml pyproject.toml
   rm -rf hooks
   ```

## Performance Comparison

### Local Deployment
- **Pros**: Lower latency, direct access, easier debugging
- **Cons**: Manual management, single machine, no HA

### Databricks Apps Deployment
- **Pros**: Managed infrastructure, HA, enterprise auth, monitoring
- **Cons**: Slightly higher latency (network hop), container overhead

**Recommendation**: Use local for development, Databricks Apps for production/shared access.

## Troubleshooting Migration Issues

### Build Fails

```bash
# Check Python environment
python --version  # Should be 3.11+

# Install dependencies
pip install uv hatchling

# Try building again
uv build --wheel
```

### App Won't Start

```bash
# Check logs
databricks apps logs playwright-mcp-on-apps -p my-profile

# Common issues:
# 1. Node.js missing - check container has Node.js 18+
# 2. npm install failed - check package.json is in .build/
# 3. Permission errors - check service principal permissions
```

### Client Can't Connect

```bash
# Verify app URL
databricks apps get playwright-mcp-on-apps -p my-profile

# Test health endpoint
curl https://your-app.databricksapps.com/health \
  -H "Authorization: Bearer $(databricks auth token -p my-profile)"

# Check token
databricks auth token -p my-profile
```

## Next Steps

1. **Read the guides**:
   - [README_DATABRICKS.md](./README_DATABRICKS.md) - Complete documentation
   - [EXAMPLE_DEPLOYMENT.md](./EXAMPLE_DEPLOYMENT.md) - Quick examples
   - [USAGE_GUIDE.md](./USAGE_GUIDE.md) - Full usage guide

2. **Try local testing first**:
   ```bash
   uvicorn playwright_mcp_databricks.app:app --reload --port 8000
   ```

3. **Deploy to Databricks**:
   ```bash
   uv build --wheel
   databricks bundle deploy -p my-profile
   databricks bundle run playwright-mcp-on-apps -p my-profile
   ```

4. **Update your clients** to use the new URL

## Support

- **Issues**: [GitHub Issues](https://github.com/murtihash94/playwright-mcp-databricks/issues)
- **Playwright MCP**: [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp)
- **Databricks Docs**: [Databricks Apps](https://docs.databricks.com/apps/)

## Feedback

This migration should be seamless. If you encounter any issues, please open an issue on GitHub!
