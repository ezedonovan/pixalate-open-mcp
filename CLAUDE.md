# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Installation
```bash
make install          # Install virtual environment and pre-commit hooks
uv sync              # Sync dependencies
uv run pre-commit install  # Install pre-commit hooks manually
```

### Code Quality and Testing
```bash
make check           # Run all quality checks (linting, type checking, deptry)
make test           # Run pytest with coverage
uv run pre-commit run -a  # Run pre-commit hooks on all files
uv run mypy         # Type checking
uv run deptry src   # Check for obsolete dependencies
```

### Single Test Execution
```bash
uv run python -m pytest tests/specific_test.py  # Run specific test file
uv run python -m pytest tests/specific_test.py::test_function  # Run specific test
uv run python -m pytest -k "test_pattern"  # Run tests matching pattern
```

### Build and Documentation
```bash
make build          # Build wheel file
make docs           # Build and serve documentation locally
make docs-test      # Test documentation build
tox                 # Run tests across multiple Python versions
```

## Architecture Overview

This is a Pixalate Open MCP (Model Context Protocol) Server that provides analytics, fraud detection, and enrichment tools through both stdio and SSE transports.

### Core Architecture

**MCP Server Structure**: Built using FastMCP, the server registers multiple toolsets that interact with Pixalate's APIs:

- **Server Entry Point**: `src/pixalate_open_mcp/server/app.py:15` - `create_mcp_server()` function initializes the MCP server and registers all toolsets
- **Tool Registration**: `src/pixalate_open_mcp/server/app.py:24` - `register_tools()` iterates through toolsets (enrichment, fraud, analytics) and registers each tool with the MCP server
- **Transport Support**: Supports both stdio (default) and SSE transports via CLI options

### Tool Organization

**Toolset Pattern**: Each domain (analytics, fraud, enrichment) follows a consistent pattern:
- **Models**: Domain-specific Pydantic models in `src/pixalate_open_mcp/models/`
- **Tools**: Implementation in `src/pixalate_open_mcp/tools/{domain}/tools.py`
- **Tool Registration**: Each tools.py exports a `toolset` object of type `PixalateToolset`

**Key Toolsets**:
- **Analytics**: Provides metadata and reporting capabilities for analytics data
- **Fraud**: Fraud detection and analysis tools
- **Enrichment**: Data enrichment services

### Configuration and Utilities

**Configuration**: `src/pixalate_open_mcp/models/config.py:12` - `load_config()` loads server configuration from environment variables including API keys and log levels

**Request Handling**: `src/pixalate_open_mcp/utils/request.py` - Centralized HTTP request handling for Pixalate API interactions

**Logging**: `src/pixalate_open_mcp/utils/logging_config.py` - Structured logging configuration with file rotation

### Client Implementation

**Echo Client**: `src/pixalate_open_mcp/client/app.py` provides a reference implementation for connecting to the MCP server using stdio transport.

## Environment Variables

Required for API access:
- `X_API_KEY`: Pixalate API key
- `LOG_LEVEL`: Logging level (default: DEBUG)
- `MCP_SERVER_NAME`: Server name (default: pixalate-open-mcp)

## Project Structure Notes

- **Python Version**: Requires Python >=3.12,<4.0
- **Package Management**: Uses `uv` for dependency management and virtual environments
- **Code Quality**: Enforced via ruff, mypy, pre-commit hooks
- **Testing**: pytest with coverage reporting
- **Documentation**: MkDocs with Material theme
