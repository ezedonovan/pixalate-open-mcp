# Pixalate Open MCP Server

An MCP (Model Context Protocol) server that provides access to Pixalate's analytics, fraud detection, and enrichment
APIs through AI assistants like Claude Desktop.

## What it provides

This MCP server enables AI assistants to:

- Query **Analytics API** for reporting data and metadata
- Access **Fraud API** for risk scoring of IPs, devices, and user agents
- Use **Enrichment APIs** for mobile apps, CTV apps, and domain reputation data

## Quick Start

### 1. Install the MCP server

Install using `uv` (recommended for reliability):

```bash
# Install the MCP server as an isolated tool
uv tool install pixalate_open_mcp

# Find the installed binary path
which pixalate_open_mcp  # macOS/Linux
where pixalate_open_mcp  # Windows
```

### 2. Get your Pixalate API key

You'll need a Pixalate API key to access the services:

- Contact Pixalate support to obtain your `X_API_KEY`
- This key provides access to Analytics, Fraud, and Enrichment APIs

### 3. Configure Claude Desktop

Add this configuration to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pixalate_open_mcp": {
      "command": "/absolute/path/to/pixalate_open_mcp",
      "env": {
        "X_API_KEY": "your-pixalate-api-key-here"
      }
    }
  }
}
```

### 4. Start using the tools

Once configured, restart Claude Desktop and you can ask it to:

- "Get analytics metadata to see my quota status"
- "Check fraud risk for IP address 101.179.108.187"
- "Check fraud risk for device ID 6757809f5e6d66f4e40fb9fd88c05139"
- "Check fraud risk for user agent Bot Googlebot/2.1 (iPod; N; RISC OS 2.4.35; IBM360; rv1.3.1) Alligator/20080524
  Jungledog/3.0"
- "Get mobile app enrichment data for app ID 1407852246"
- "Get mobile app enrichment data for app ID 1407852246 for tablet devices"
- "Get mobile app enrichment data for app ID 1407852246 in EMEA region"
- "Get CTV app enrichment data for app ID 71845 in North America region"
- "Get CTV app enrichment data for these Roku app IDs: 151908, 74519"
- "Retrieve domain reputation for cnn.com"
- "Retrieve analytics report data, specifically IVT, for the domain yahoo.com through the first week of August 2025"

## Available Tools

### Analytics API

**Metadata**: Get analytics database status and quota

**Report Tool**: Retrieve analytics report data

- Requires report configuration with dimensions, metrics, and filters
- Returns paginated analytics data

### Fraud API

**Metadata**: Get fraud database status and quota

**Fraud Tool**: Get fraud risk probability for IPs, devices, or user agents

- Parameters: `ip`, `device`, `agent` (one or more required)
- Returns risk score from 0.01-1.0 where higher values indicate greater fraud risk

### Enrichment API

**Mobile Apps**:

- **Metadata**: Get mobile app database status and quota
- **Get Apps**: Retrieve risk ratings and reputation data for mobile applications

**Connected TV (CTV)**:

- **Metadata**: Get CTV app database status and quota
- **Get Apps**: Retrieve risk ratings and reputation data for CTV applications

**Domains**:

- **Metadata**: Get domain database status and quota
- **Get Apps**: Retrieve risk ratings and reputation data for websites/domains

## Troubleshooting

### Common Issues

1. **"Tool not found" or connection errors**
    - Verify your API key is correct and active
    - Check that Claude Desktop configuration uses the correct absolute path
    - Restart Claude Desktop after configuration changes

2. **API quota exceeded**
    - Use the metadata tools to check your current quota status
    - Contact Pixalate support to increase limits if needed

3. **Dependency conflicts with uvx**
    - Use the isolated installation method with `uv tool install` instead
    - This creates a clean environment without global conflicts

### Logging

The server logs activity to rotating log files:

- **macOS**: `~/Library/Logs/mcp-servers/pixalate_open_mcp.log`
- **Linux**: `~/.local/state/mcp-servers/logs/pixalate_open_mcp.log`
- **Windows**: `%LOCALAPPDATA%\mcp-servers\logs\pixalate_open_mcp.log`

Control log verbosity with the `LOG_LEVEL` environment variable:

```json
{
  "mcpServers": {
    "pixalate_open_mcp": {
      "command": "/path/to/pixalate_open_mcp",
      "env": {
        "X_API_KEY": "your-api-key",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Requirements

- Python ≥3.12,<4.0
- Active Pixalate API subscription
- Operating Systems: macOS, Linux, Windows

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Author

Ezequiel - edonovan@pixalate.com
