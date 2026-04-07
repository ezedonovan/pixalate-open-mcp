# Anthropic Directory Compliance - Design Spec

## Goal

Make the pixalate-open-mcp server compliant with Anthropic's Software Directory Policy and MCP Directory Policy for submission as a local MCP server to Claude Connectors.

## Blocking Issues

Four policy requirements are not met, plus one recommended upgrade:

1. **Tool annotations missing (5E)** — all 11 tools lack `readOnlyHint`, `destructiveHint`, `title`
2. **Inconsistent error handling (5A)** — 9 of 11 tools have no graceful error handling
3. **Privacy policy missing (3A)** — no link despite forwarding user data to Pixalate APIs
4. **Debug logging of user params (1D)** — request params (IPs, device IDs, domains) logged at DEBUG
5. **No Streamable HTTP transport (5F)** — SSE supported but planned for deprecation

Additionally, all tool handlers and key functions lack docstrings.

---

## Section 1: Tool Annotations

**Files:** `src/pixalate_open_mcp/models/tools.py`, `src/pixalate_open_mcp/server/app.py`

Extend `PixalateTool` model with annotation fields:

```python
class PixalateTool(BaseModel):
    title: str
    description: str
    handler: Callable
    read_only_hint: bool = True
    destructive_hint: bool = False
    open_world_hint: bool = True
```

Update `register_tools()` to pass annotations to `mcp_server.add_tool()`.

All 11 tools are read-only and non-destructive. All call external Pixalate APIs (`open_world_hint=True`) except the Version tool (`open_world_hint=False`).

---

## Section 2: Error Handling

**Files:** All tool handler files in `src/pixalate_open_mcp/tools/`

Add consistent try/except to all 11 tool handler functions returning structured error dicts:

```python
try:
    # existing logic
except requests.HTTPError as e:
    return {"error": f"API request failed with status {e.response.status_code}", "details": str(e)}
except requests.ConnectionError:
    return {"error": "Unable to connect to Pixalate API. Check your network connection."}
except requests.Timeout:
    return {"error": "Request to Pixalate API timed out. Please try again."}
except Exception as e:
    return {"error": f"Unexpected error: {str(e)}"}
```

Update existing `get_analytics_report()` to use the same pattern for consistency.

---

## Section 3: Privacy & Logging

**Files:** `README.md`, `src/pixalate_open_mcp/utils/request.py`

### Privacy Policy
Add a "Privacy" section to the README linking to `https://www.pixalate.com/privacy-policy`.

### Request Logging
Remove `{params}` from the debug log in `request.py` line 35. User-supplied data (IPs, device IDs, domains) must not be logged.

- **Before:** `logger.debug(f"{method} {url} {params} start")`
- **After:** `logger.debug(f"{method} {url} start")`

Keep method, URL, status code, and elapsed time logs (operational, no user data).

---

## Section 4: Streamable HTTP Transport

**Files:** `src/pixalate_open_mcp/server/app.py`

Add `streamable-http` as a third transport option in the CLI:

```python
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse", "streamable-http"]),
    default="stdio",
)
```

Wire up `server.run_streamable_http_async()` in `main()`. FastMCP already provides this method. Keep SSE for backward compatibility.

---

## Section 5: Function Documentation

**Files:** All modified files plus `src/pixalate_open_mcp/models/config.py`, `src/pixalate_open_mcp/utils/logging_config.py`

Add Google-style docstrings to:
- All 11 tool handler functions (analytics, fraud, enrichment)
- Utility functions in `request.py` and `logging_config.py`
- Server functions (`create_mcp_server`, `register_tools`, `get_mcp_server_version`)
- Model function (`load_config`)

---

## Out of Scope

- Hardcoded API key in `mcp.json` (file is gitignored)
- Input validation on user agent strings or IP addresses
- Cross-service automation concerns (not applicable — single service)
