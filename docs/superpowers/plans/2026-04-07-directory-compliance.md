# Anthropic Directory Compliance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the pixalate-open-mcp server fully compliant with Anthropic's Software Directory Policy for submission as a local MCP server.

**Architecture:** Five targeted changes across existing files: extend the tool model with annotation fields, add consistent error handling to all tool handlers, clean up request logging, add Streamable HTTP transport, and add function docstrings. No new modules or structural changes.

**Tech Stack:** Python 3.12+, FastMCP (mcp package), Pydantic, requests, click

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `src/pixalate_open_mcp/models/tools.py` | Modify | Add annotation fields to PixalateTool |
| `src/pixalate_open_mcp/server/app.py` | Modify | Pass annotations to add_tool, add streamable-http transport, docstrings |
| `src/pixalate_open_mcp/tools/analytics/tools.py` | Modify | Error handling, docstrings |
| `src/pixalate_open_mcp/tools/fraud/tools.py` | Modify | Error handling, docstrings |
| `src/pixalate_open_mcp/tools/enrichment/tools.py` | Modify | Error handling, docstrings |
| `src/pixalate_open_mcp/utils/request.py` | Modify | Remove param logging, docstrings |
| `src/pixalate_open_mcp/utils/logging_config.py` | Modify | Docstrings |
| `src/pixalate_open_mcp/models/config.py` | Modify | Docstrings |
| `README.md` | Modify | Add privacy policy section |
| `tests/test_tool_annotations.py` | Create | Tests for annotations and error handling |

---

### Task 1: Extend PixalateTool Model with Annotation Fields

**Files:**
- Modify: `src/pixalate_open_mcp/models/tools.py:1-14`
- Test: `tests/test_tool_annotations.py`

- [ ] **Step 1: Write failing test for annotation fields**

Create `tests/test_tool_annotations.py`:

```python
from pixalate_open_mcp.models.tools import PixalateTool, PixalateToolset


def dummy_handler() -> dict:
    return {}


def test_pixalate_tool_has_annotation_defaults():
    tool = PixalateTool(
        title="Test",
        description="A test tool.",
        handler=dummy_handler,
    )
    assert tool.read_only_hint is True
    assert tool.destructive_hint is False
    assert tool.open_world_hint is True


def test_pixalate_tool_annotation_override():
    tool = PixalateTool(
        title="Version",
        description="Get version.",
        handler=dummy_handler,
        open_world_hint=False,
    )
    assert tool.open_world_hint is False
    assert tool.read_only_hint is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_tool_annotations.py -v`
Expected: FAIL — `read_only_hint` field not found on PixalateTool

- [ ] **Step 3: Add annotation fields to PixalateTool**

Update `src/pixalate_open_mcp/models/tools.py` to:

```python
from typing import Callable

from pydantic import BaseModel, Field


class PixalateTool(BaseModel):
    """A tool definition for the Pixalate MCP server.

    Attributes:
        title: Human-readable name of the tool.
        description: Description of the tool's functionality and usage.
        handler: Async or sync function that implements the tool.
        read_only_hint: Whether the tool only reads data without side effects.
        destructive_hint: Whether the tool may perform destructive operations.
        open_world_hint: Whether the tool interacts with external services.
    """

    title: str = Field(description="Human readable name of the tool.")
    description: str = Field(description="Description of the tool.")
    handler: Callable = Field(description="Handler function for the tool.")
    read_only_hint: bool = Field(default=True, description="Whether the tool only reads data.")
    destructive_hint: bool = Field(default=False, description="Whether the tool may perform destructive operations.")
    open_world_hint: bool = Field(default=True, description="Whether the tool interacts with external services.")


class PixalateToolset(BaseModel):
    """A named group of related Pixalate tools.

    Attributes:
        name: Name of the toolset (e.g., 'Analytics API').
        tools: List of tools in this toolset.
    """

    name: str = Field(description="Name of the toolset.")
    tools: list[PixalateTool] = Field(description="List of tools.")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_tool_annotations.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/pixalate_open_mcp/models/tools.py tests/test_tool_annotations.py
git commit -m "feat: add annotation fields to PixalateTool model"
```

---

### Task 2: Pass Annotations to FastMCP in register_tools

**Files:**
- Modify: `src/pixalate_open_mcp/server/app.py:1-73`
- Test: `tests/test_tool_annotations.py` (append)

- [ ] **Step 1: Write failing test for annotation registration**

Append to `tests/test_tool_annotations.py`:

```python
from unittest.mock import MagicMock

from mcp.types import ToolAnnotations

from pixalate_open_mcp.server.app import register_tools


def test_register_tools_passes_annotations():
    mock_server = MagicMock()
    register_tools(mock_server)

    for call in mock_server.add_tool.call_args_list:
        kwargs = call[1]
        assert "annotations" in kwargs, f"Tool '{kwargs.get('title')}' missing annotations"
        ann = kwargs["annotations"]
        assert isinstance(ann, ToolAnnotations)
        assert ann.readOnlyHint is True
        assert ann.destructiveHint is False


def test_version_tool_not_open_world():
    mock_server = MagicMock()
    register_tools(mock_server)

    version_call = [
        c for c in mock_server.add_tool.call_args_list if "Version" in c[1].get("title", "")
    ]
    assert len(version_call) == 1
    ann = version_call[0][1]["annotations"]
    assert ann.openWorldHint is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_tool_annotations.py::test_register_tools_passes_annotations -v`
Expected: FAIL — `annotations` not in kwargs

- [ ] **Step 3: Update register_tools to pass annotations**

Update `src/pixalate_open_mcp/server/app.py`:

```python
import asyncio
import sys
from typing import Optional

import click
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from pixalate_open_mcp.__version__ import __version__
from pixalate_open_mcp.models.config import ServerConfig, load_config
from pixalate_open_mcp.tools.analytics.tools import toolset as analytics_toolset
from pixalate_open_mcp.tools.enrichment.tools import toolset as enrichment_toolset
from pixalate_open_mcp.tools.fraud.tools import toolset as fraud_toolset
from pixalate_open_mcp.utils.logging_config import logger, setup_logging


def create_mcp_server(config: Optional[ServerConfig] = None) -> FastMCP:
    """Create and configure the Pixalate MCP server.

    Args:
        config: Server configuration. If None, loads from environment variables.

    Returns:
        Configured FastMCP server instance with all tools registered.
    """
    if config is None:
        config = load_config()
    setup_logging(config)
    server = FastMCP(config.name)
    register_tools(server)
    return server


def register_tools(mcp_server: FastMCP) -> None:
    """Register all Pixalate toolsets with the MCP server.

    Iterates through enrichment, fraud, and analytics toolsets and registers
    each tool with its annotations and description.

    Args:
        mcp_server: The FastMCP server instance to register tools on.
    """
    for toolset in [enrichment_toolset, fraud_toolset, analytics_toolset]:
        toolset_name = toolset.name
        for tool in toolset.tools:
            mcp_server.add_tool(
                fn=tool.handler,
                title=f"{toolset_name} - {tool.title}",
                description=tool.description,
                annotations=ToolAnnotations(
                    readOnlyHint=tool.read_only_hint,
                    destructiveHint=tool.destructive_hint,
                    openWorldHint=tool.open_world_hint,
                ),
            )
    mcp_server.add_tool(
        fn=get_mcp_server_version,
        title="Pixalate Open MCP - Version",
        description="Get the version of the Pixalate Open MCP server.",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=False,
        ),
    )


def get_mcp_server_version() -> dict:
    """Get the current version of the Pixalate Open MCP server.

    Returns:
        Dictionary with server name and version string.
    """
    return {
        "name": "Pixalate Open MCP",
        "version": __version__,
    }


server = create_mcp_server()


@click.command()
@click.option("--port", default=3001, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse", "streamable-http"]),
    default="stdio",
    help="Transport type",
)
def main(port: int, transport: str) -> int:
    """Start the Pixalate Open MCP server.

    Args:
        port: Port number for SSE or Streamable HTTP transport.
        transport: Transport protocol to use (stdio, sse, or streamable-http).

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        if transport == "stdio":
            asyncio.run(server.run_stdio_async())
        elif transport == "sse":
            server.settings.port = port
            asyncio.run(server.run_sse_async())
        else:
            server.settings.port = port
            asyncio.run(server.run_streamable_http_async())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run python -m pytest tests/test_tool_annotations.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/pixalate_open_mcp/server/app.py tests/test_tool_annotations.py
git commit -m "feat: pass tool annotations to FastMCP and add streamable-http transport"
```

---

### Task 3: Add Error Handling to Analytics Tools

**Files:**
- Modify: `src/pixalate_open_mcp/tools/analytics/tools.py:1-52`
- Test: `tests/test_tool_annotations.py` (append)

- [ ] **Step 1: Write failing test for error handling**

Append to `tests/test_tool_annotations.py`:

```python
from unittest.mock import patch

import requests


def test_analytics_metadata_handles_http_error():
    with patch("pixalate_open_mcp.tools.analytics.tools.request_handler") as mock:
        response = MagicMock()
        response.raise_for_status.side_effect = requests.HTTPError(
            response=MagicMock(status_code=403)
        )
        mock.return_value = response
        from pixalate_open_mcp.tools.analytics.tools import get_analytics_metadata

        result = get_analytics_metadata()
        assert "error" in result


def test_analytics_metadata_handles_connection_error():
    with patch("pixalate_open_mcp.tools.analytics.tools.request_handler") as mock:
        mock.side_effect = requests.ConnectionError("Connection refused")
        from pixalate_open_mcp.tools.analytics.tools import get_analytics_metadata

        result = get_analytics_metadata()
        assert "error" in result
        assert "connect" in result["error"].lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_tool_annotations.py::test_analytics_metadata_handles_http_error -v`
Expected: FAIL — raises HTTPError instead of returning dict

- [ ] **Step 3: Update analytics tools with error handling and docstrings**

Update `src/pixalate_open_mcp/tools/analytics/tools.py`:

```python
import os
from urllib.parse import urlencode

import requests

from pixalate_open_mcp.models.analytics import AnalyticsRequest, AnalyticsResponse
from pixalate_open_mcp.models.metadata import Metadata
from pixalate_open_mcp.models.tools import PixalateTool, PixalateToolset
from pixalate_open_mcp.utils.logging_config import logger
from pixalate_open_mcp.utils.request import RequestMethod, request_handler

BASE_URL = "https://api.pixalate.com/api/v2/"


def get_analytics_metadata(pretty: bool = False) -> dict | Metadata:
    """Retrieve metadata for analytics reports including quota status and last update date.

    Args:
        pretty: Whether to format the response for readability.

    Returns:
        Analytics metadata or error details.
    """
    try:
        resp = request_handler(
            method=RequestMethod.GET,
            url=os.path.join(BASE_URL, "analytics", "reports") + "?" + urlencode({"pretty": pretty}).lower(),
        )
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        logger.error(f"Analytics metadata request failed: {e}")
        return {"error": f"API request failed with status {e.response.status_code}", "details": str(e)}
    except requests.ConnectionError:
        logger.error("Failed to connect to Pixalate Analytics API")
        return {"error": "Unable to connect to Pixalate API. Check your network connection."}
    except requests.Timeout:
        logger.error("Analytics metadata request timed out")
        return {"error": "Request to Pixalate API timed out. Please try again."}
    except Exception as e:
        logger.error(f"Unexpected error in analytics metadata: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


def get_analytics_report(request: AnalyticsRequest) -> dict | AnalyticsResponse:
    """Retrieve analytics report data based on the provided query configuration.

    Args:
        request: Analytics request with report ID, query filters, dimensions, and metrics.

    Returns:
        Analytics report data or error details.
    """
    try:
        resp = request_handler(
            method=RequestMethod.GET,
            url=os.path.join(BASE_URL, "analytics", "reports", request.reportId),
            params=request.to_params(),
        )
        return resp.json()
    except requests.HTTPError as e:
        logger.error(f"Analytics report request failed: {e}")
        return {"error": f"API request failed with status {e.response.status_code}", "details": str(e)}
    except requests.ConnectionError:
        logger.error("Failed to connect to Pixalate Analytics API")
        return {"error": "Unable to connect to Pixalate API. Check your network connection."}
    except requests.Timeout:
        logger.error("Analytics report request timed out")
        return {"error": "Request to Pixalate API timed out. Please try again."}
    except Exception as e:
        logger.error(f"Unexpected error in analytics report: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


toolset = PixalateToolset(
    name="Analytics API",
    tools=[
        PixalateTool(
            title="Metadata",
            description="""The purpose of this API is to provide metadata information for analytics reports in general. The response is a JSON formatted object containing the current user's quota state and the date the analytics reports database was last updated.""",
            handler=get_analytics_metadata,
        ),
        PixalateTool(
            title="Report",
            description="""The purpose of this API is to provide the ability for Pixalate Analytics subscribers to ingest analytics data into their own internal systems. The response is a JSON formatted object containing a list of report items""",
            handler=get_analytics_report,
        ),
    ],
)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run python -m pytest tests/test_tool_annotations.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/pixalate_open_mcp/tools/analytics/tools.py tests/test_tool_annotations.py
git commit -m "feat: add error handling and docstrings to analytics tools"
```

---

### Task 4: Add Error Handling to Fraud Tools

**Files:**
- Modify: `src/pixalate_open_mcp/tools/fraud/tools.py:1-49`
- Test: `tests/test_tool_annotations.py` (append)

- [ ] **Step 1: Write failing test for fraud error handling**

Append to `tests/test_tool_annotations.py`:

```python
def test_fraud_metadata_handles_http_error():
    with patch("pixalate_open_mcp.tools.fraud.tools.request_handler") as mock:
        response = MagicMock()
        response.raise_for_status.side_effect = requests.HTTPError(
            response=MagicMock(status_code=401)
        )
        mock.return_value = response
        from pixalate_open_mcp.tools.fraud.tools import get_fraud_metadata

        result = get_fraud_metadata()
        assert "error" in result


def test_fraud_handles_connection_error():
    with patch("pixalate_open_mcp.tools.fraud.tools.request_handler") as mock:
        mock.side_effect = requests.ConnectionError("Connection refused")
        from pixalate_open_mcp.tools.fraud.tools import get_fraud

        from pixalate_open_mcp.models.fraud import FraudRequest

        result = get_fraud(FraudRequest(ip="1.2.3.4"))
        assert "error" in result
        assert "connect" in result["error"].lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_tool_annotations.py::test_fraud_metadata_handles_http_error -v`
Expected: FAIL — raises HTTPError

- [ ] **Step 3: Update fraud tools with error handling and docstrings**

Update `src/pixalate_open_mcp/tools/fraud/tools.py`:

```python
import os
from urllib.parse import urlencode

import requests

from pixalate_open_mcp.models.fraud import FraudRequest, FraudResponse
from pixalate_open_mcp.models.metadata import Metadata
from pixalate_open_mcp.models.tools import PixalateTool, PixalateToolset
from pixalate_open_mcp.utils.logging_config import logger
from pixalate_open_mcp.utils.request import RequestMethod, request_handler

BASE_URL = "https://fraud-api.pixalate.com/api/v2/"


def get_fraud_metadata(pretty: bool = False) -> dict | Metadata:
    """Retrieve metadata for the Fraud API including quota status and last update date.

    Args:
        pretty: Whether to format the response for readability.

    Returns:
        Fraud metadata or error details.
    """
    try:
        resp = request_handler(
            method=RequestMethod.GET,
            url=os.path.join(BASE_URL, "fraud") + "?" + urlencode({"pretty": pretty}).lower(),
        )
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        logger.error(f"Fraud metadata request failed: {e}")
        return {"error": f"API request failed with status {e.response.status_code}", "details": str(e)}
    except requests.ConnectionError:
        logger.error("Failed to connect to Pixalate Fraud API")
        return {"error": "Unable to connect to Pixalate API. Check your network connection."}
    except requests.Timeout:
        logger.error("Fraud metadata request timed out")
        return {"error": "Request to Pixalate API timed out. Please try again."}
    except Exception as e:
        logger.error(f"Unexpected error in fraud metadata: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


def get_fraud(request: FraudRequest) -> dict | FraudResponse:
    """Retrieve fraud risk probability for a specific IP, device, or user agent.

    Args:
        request: Fraud request with IP, device ID, and/or user agent parameters.

    Returns:
        Fraud risk scoring data or error details.
    """
    try:
        resp = request_handler(
            method=RequestMethod.GET,
            url=os.path.join(BASE_URL, "fraud"),
            params=request.to_params(),
        )
        return resp.json()
    except requests.HTTPError as e:
        logger.error(f"Fraud request failed: {e}")
        return {"error": f"API request failed with status {e.response.status_code}", "details": str(e)}
    except requests.ConnectionError:
        logger.error("Failed to connect to Pixalate Fraud API")
        return {"error": "Unable to connect to Pixalate API. Check your network connection."}
    except requests.Timeout:
        logger.error("Fraud request timed out")
        return {"error": "Request to Pixalate API timed out. Please try again."}
    except Exception as e:
        logger.error(f"Unexpected error in fraud request: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


toolset = PixalateToolset(
    name="Fraud API",
    tools=[
        PixalateTool(
            title="Metadata",
            description="""The purpose of this API is to provide metadata information for Fraud API in general. The response is a JSON formatted object containing the current user's quota state and the date the fraud database was last updated.""",
            handler=get_fraud_metadata,
        ),
        PixalateTool(
            title="Fraud",
            description="""Retrieve probability of fraud for a specific IP, Device, or Agent. The Fraud Blocking API returns a probability (risk score) 0.01 to 1.0 representing the likelihood a given value is related to malicious or compromised devices. This risk scoring is calculated by Pixalate's proprietary machine-learning algorithm and allows clients to set their own blocking thresholds based on the quality and scale of their supply inventory. The following is a general guideline for setting fraud blocking thresholds:

Probability equal to 1.0, for filtering out only the worst offender for blocking (deterministic).
Probability is greater than or equal to 0.90 for filtering out users that are fraudulent beyond a reasonable doubt.
Probability between 0.75 (inclusive) and 0.90 (exclusive) to filter out users associated with clear and convincing evidence that they are fraudulent.
Probability between 0.5 (inclusive) and 0.75 (exclusive) to filter out users that it is more likely than not that they are fraudulent (also known as preponderance of the evidence standard).
Pixalate does not recommend blocking any probabilities less than 0.5. When making adjustments to the probability threshold, Pixalate highly recommends regular checks and balances against impression delivery as lowering the probabilistic threshold can potentially impact the impression count.

Zero or more of the following parameters may be provided. If more than one parameter is specified, the probability returned is determined by assessing risk based on the combination of each parameter's individual risk probability.

Not specifying an IP, Device, or Agent will return the metadata for fraud, including the user's current quota. See alternate response schema below.""",
            handler=get_fraud,
        ),
    ],
)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run python -m pytest tests/test_tool_annotations.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/pixalate_open_mcp/tools/fraud/tools.py tests/test_tool_annotations.py
git commit -m "feat: add error handling and docstrings to fraud tools"
```

---

### Task 5: Add Error Handling to Enrichment Tools

**Files:**
- Modify: `src/pixalate_open_mcp/tools/enrichment/tools.py:1-117`
- Test: `tests/test_tool_annotations.py` (append)

- [ ] **Step 1: Write failing test for enrichment error handling**

Append to `tests/test_tool_annotations.py`:

```python
def test_enrichment_mobile_metadata_handles_http_error():
    with patch("pixalate_open_mcp.tools.enrichment.tools.request_handler") as mock:
        response = MagicMock()
        response.raise_for_status.side_effect = requests.HTTPError(
            response=MagicMock(status_code=500)
        )
        mock.return_value = response
        from pixalate_open_mcp.tools.enrichment.tools import get_enrichment_mobile_metadata

        result = get_enrichment_mobile_metadata()
        assert "error" in result


def test_enrichment_domains_handles_connection_error():
    with patch("pixalate_open_mcp.tools.enrichment.tools.request_handler") as mock:
        mock.side_effect = requests.ConnectionError("Connection refused")
        from pixalate_open_mcp.tools.enrichment.tools import get_enrichment_domains

        from pixalate_open_mcp.models.enrichment import EnrichmentDomainRequest

        result = get_enrichment_domains(EnrichmentDomainRequest(adDomain=["cnn.com"]))
        assert "error" in result
        assert "connect" in result["error"].lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_tool_annotations.py::test_enrichment_mobile_metadata_handles_http_error -v`
Expected: FAIL — raises HTTPError

- [ ] **Step 3: Update enrichment tools with error handling and docstrings**

Update `src/pixalate_open_mcp/tools/enrichment/tools.py`:

```python
import os
from urllib.parse import urlencode

import requests

from pixalate_open_mcp.models.enrichment import EnrichmentCTVRequest, EnrichmentDomainRequest, EnrichmentMobileRequest
from pixalate_open_mcp.models.metadata import Metadata
from pixalate_open_mcp.models.tools import PixalateTool, PixalateToolset
from pixalate_open_mcp.utils.logging_config import logger
from pixalate_open_mcp.utils.request import (
    RequestMethod,
    _handle_csv_upload,
    _handle_download,
    _handle_download_response,
    request_handler,
)

BASE_URL = "https://api.pixalate.com/api/v2/"


def get_enrichment_mobile_metadata(pretty: bool = False) -> dict | Metadata:
    """Retrieve metadata for mobile application enrichment data.

    Args:
        pretty: Whether to format the response for readability.

    Returns:
        Mobile enrichment metadata or error details.
    """
    try:
        resp = request_handler(
            method=RequestMethod.GET,
            url=os.path.join(BASE_URL, "mrt", "apps") + "?" + urlencode({"pretty": pretty}).lower(),
        )
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        logger.error(f"Mobile metadata request failed: {e}")
        return {"error": f"API request failed with status {e.response.status_code}", "details": str(e)}
    except requests.ConnectionError:
        logger.error("Failed to connect to Pixalate Enrichment API")
        return {"error": "Unable to connect to Pixalate API. Check your network connection."}
    except requests.Timeout:
        logger.error("Mobile metadata request timed out")
        return {"error": "Request to Pixalate API timed out. Please try again."}
    except Exception as e:
        logger.error(f"Unexpected error in mobile metadata: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


def get_enrichment_mobile_app(request: EnrichmentMobileRequest) -> dict:
    """Retrieve risk ratings and reputational data for mobile applications.

    Args:
        request: Mobile enrichment request with app IDs and optional region/device filters.

    Returns:
        Mobile app enrichment data or error details.
    """
    try:
        return _handle_enrichment_request(
            url=os.path.join(BASE_URL, "mrt", "apps"),
            app_or_domain_ids=request.appIds,
            column_name="appId",
            params=request.to_params(),
        )
    except requests.HTTPError as e:
        logger.error(f"Mobile app enrichment request failed: {e}")
        return {"error": f"API request failed with status {e.response.status_code}", "details": str(e)}
    except requests.ConnectionError:
        logger.error("Failed to connect to Pixalate Enrichment API")
        return {"error": "Unable to connect to Pixalate API. Check your network connection."}
    except requests.Timeout:
        logger.error("Mobile app enrichment request timed out")
        return {"error": "Request to Pixalate API timed out. Please try again."}
    except Exception as e:
        logger.error(f"Unexpected error in mobile app enrichment: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


def get_enrichment_ctv_metadata(pretty: bool = False) -> dict | Metadata:
    """Retrieve metadata for connected TV application enrichment data.

    Args:
        pretty: Whether to format the response for readability.

    Returns:
        CTV enrichment metadata or error details.
    """
    try:
        resp = request_handler(
            method=RequestMethod.GET,
            url=os.path.join(BASE_URL, "mrt", "ctv") + "?" + urlencode({"pretty": pretty}).lower(),
        )
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        logger.error(f"CTV metadata request failed: {e}")
        return {"error": f"API request failed with status {e.response.status_code}", "details": str(e)}
    except requests.ConnectionError:
        logger.error("Failed to connect to Pixalate Enrichment API")
        return {"error": "Unable to connect to Pixalate API. Check your network connection."}
    except requests.Timeout:
        logger.error("CTV metadata request timed out")
        return {"error": "Request to Pixalate API timed out. Please try again."}
    except Exception as e:
        logger.error(f"Unexpected error in CTV metadata: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


def get_enrichment_ctv_app(request: EnrichmentCTVRequest) -> dict:
    """Retrieve risk ratings and reputational data for CTV applications.

    Args:
        request: CTV enrichment request with app IDs and optional region filter.

    Returns:
        CTV app enrichment data or error details.
    """
    try:
        return _handle_enrichment_request(
            url=os.path.join(BASE_URL, "mrt", "ctv"),
            app_or_domain_ids=request.appIds,
            column_name="appId",
            params=request.to_params(),
        )
    except requests.HTTPError as e:
        logger.error(f"CTV app enrichment request failed: {e}")
        return {"error": f"API request failed with status {e.response.status_code}", "details": str(e)}
    except requests.ConnectionError:
        logger.error("Failed to connect to Pixalate Enrichment API")
        return {"error": "Unable to connect to Pixalate API. Check your network connection."}
    except requests.Timeout:
        logger.error("CTV app enrichment request timed out")
        return {"error": "Request to Pixalate API timed out. Please try again."}
    except Exception as e:
        logger.error(f"Unexpected error in CTV app enrichment: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


def get_enrichment_domains_metadata(pretty: bool = False) -> dict | Metadata:
    """Retrieve metadata for domain enrichment data.

    Args:
        pretty: Whether to format the response for readability.

    Returns:
        Domain enrichment metadata or error details.
    """
    try:
        resp = request_handler(
            method=RequestMethod.GET,
            url=os.path.join(BASE_URL, "mrt", "domains") + "?" + urlencode({"pretty": pretty}).lower(),
        )
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        logger.error(f"Domain metadata request failed: {e}")
        return {"error": f"API request failed with status {e.response.status_code}", "details": str(e)}
    except requests.ConnectionError:
        logger.error("Failed to connect to Pixalate Enrichment API")
        return {"error": "Unable to connect to Pixalate API. Check your network connection."}
    except requests.Timeout:
        logger.error("Domain metadata request timed out")
        return {"error": "Request to Pixalate API timed out. Please try again."}
    except Exception as e:
        logger.error(f"Unexpected error in domain metadata: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


def get_enrichment_domains(request: EnrichmentDomainRequest) -> dict:
    """Retrieve risk ratings and reputational data for websites and domains.

    Args:
        request: Domain enrichment request with domain names and optional region filter.

    Returns:
        Domain enrichment data or error details.
    """
    try:
        return _handle_enrichment_request(
            url=os.path.join(BASE_URL, "mrt", "domains"),
            app_or_domain_ids=request.adDomain,
            column_name="adDomain",
            params=request.to_params(),
        )
    except requests.HTTPError as e:
        logger.error(f"Domain enrichment request failed: {e}")
        return {"error": f"API request failed with status {e.response.status_code}", "details": str(e)}
    except requests.ConnectionError:
        logger.error("Failed to connect to Pixalate Enrichment API")
        return {"error": "Unable to connect to Pixalate API. Check your network connection."}
    except requests.Timeout:
        logger.error("Domain enrichment request timed out")
        return {"error": "Request to Pixalate API timed out. Please try again."}
    except Exception as e:
        logger.error(f"Unexpected error in domain enrichment: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


def _handle_enrichment_request(url: str, app_or_domain_ids: list[str], column_name: str, params: dict) -> dict:
    """Handle enrichment requests, using CSV upload for batch queries.

    For single IDs, makes a direct GET request. For multiple IDs, uploads a CSV
    and polls for the download result.

    Args:
        url: Base API URL for the enrichment endpoint.
        app_or_domain_ids: List of app IDs or domain names to query.
        column_name: CSV column header name ('appId' or 'adDomain').
        params: Additional query parameters (region, device, etc.).

    Returns:
        Enrichment data from the Pixalate API.
    """
    if len(app_or_domain_ids) > 1:
        download_url = _handle_csv_upload(url=url, column_name=column_name, data=app_or_domain_ids, params=params)
        response = _handle_download(download_url)
        data = _handle_download_response(response)
        return data
    else:
        url = os.path.join(url, app_or_domain_ids[0])
        resp = request_handler(method=RequestMethod.GET, url=url, params=params)
        return resp.json()


toolset = PixalateToolset(
    name="Enrichment API",
    tools=[
        PixalateTool(
            title="Mobile, Metadata",
            description="The purpose of this API is to provide metadata information for mobile applications in general. The response is a JSON formatted object containing the current user's quota state and the date the mobile applications database was last updated.",
            handler=get_enrichment_mobile_metadata,
        ),
        PixalateTool(
            title="Mobile, Get Apps",
            description="The purpose of this API is to provide risk ratings and reputational data for mobile applications. The response is a JSON formatted object containing a list of app information partitioned by region and device.",
            handler=get_enrichment_mobile_app,
        ),
        PixalateTool(
            title="CTV, Metadata",
            description="The purpose of this API is to provide metadata information for the connected TV applications in general. The response is a JSON formatted object containing the current user's quota state and the date the Connected TV applications database was last updated.",
            handler=get_enrichment_ctv_metadata,
        ),
        PixalateTool(
            title="CTV, Get Apps",
            description="The purpose of this API is to provide risk ratings and reputational data for CTV applications. The response is a JSON formatted object containing a list of app information partitioned by region and device.",
            handler=get_enrichment_ctv_app,
        ),
        PixalateTool(
            title="Domains, Metadata",
            description="The purpose of this API is to provide metadata information for domains in general. The response is a JSON formatted object containing the current user's quota state and the date the domains database was last updated.",
            handler=get_enrichment_domains_metadata,
        ),
        PixalateTool(
            title="Domains, Get Apps",
            description="The purpose of this API is to provide risk ratings and reputational data for websites. The response is a JSON formatted object containing a list of app information partitioned by region and device.",
            handler=get_enrichment_domains,
        ),
    ],
)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run python -m pytest tests/test_tool_annotations.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/pixalate_open_mcp/tools/enrichment/tools.py tests/test_tool_annotations.py
git commit -m "feat: add error handling and docstrings to enrichment tools"
```

---

### Task 6: Clean Up Request Logging and Add Utility Docstrings

**Files:**
- Modify: `src/pixalate_open_mcp/utils/request.py:1-78`
- Modify: `src/pixalate_open_mcp/utils/logging_config.py:1-99`
- Modify: `src/pixalate_open_mcp/models/config.py:1-17`
- Test: `tests/test_tool_annotations.py` (append)

- [ ] **Step 1: Write failing test for cleaned logging**

Append to `tests/test_tool_annotations.py`:

```python
import logging


def test_request_handler_does_not_log_params(caplog):
    with patch("pixalate_open_mcp.utils.request.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with caplog.at_level(logging.DEBUG, logger="pixalate_open_mcp"):
            from pixalate_open_mcp.utils.request import RequestMethod, request_handler

            request_handler(method=RequestMethod.GET, url="https://example.com/api", params={"ip": "1.2.3.4"})

        for record in caplog.records:
            assert "1.2.3.4" not in record.message, "User params should not appear in logs"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_tool_annotations.py::test_request_handler_does_not_log_params -v`
Expected: FAIL — params dict logged containing "1.2.3.4"

- [ ] **Step 3: Update request.py — remove param logging, add docstrings**

Update `src/pixalate_open_mcp/utils/request.py`:

```python
import json
import tempfile
import time
import traceback
from typing import Literal

import requests

from pixalate_open_mcp.models.config import load_config
from pixalate_open_mcp.utils.exponential_backoff import exponential_backoff
from pixalate_open_mcp.utils.logging_config import logger

config = load_config()


class RequestMethod:
    POST = "POST"
    GET = "GET"


def raise_invalid_request():
    """Raise an exception for unsupported HTTP request methods."""

    class InvalidRequestMethod(Exception):
        pass

    raise InvalidRequestMethod()


def request_handler(method: Literal[RequestMethod], url: str, **kwargs) -> requests.Response:
    """Send an HTTP request to the Pixalate API.

    Args:
        method: HTTP method (RequestMethod.GET or RequestMethod.POST).
        url: Full URL for the API endpoint.
        **kwargs: Additional arguments passed to requests.get/post (e.g., params, data).

    Returns:
        The HTTP response object.

    Raises:
        requests.HTTPError: If the response status code indicates an error.
        InvalidRequestMethod: If an unsupported HTTP method is provided.
    """
    try:
        params = {
            "url": url,
            "headers": {"x-api-key": config.x_api_key, "Accept": "application/json", "Content-Type": "text/csv"},
            **kwargs,
        }
        logger.debug(f"{method} {url} start")
        t0 = time.time()
        if method == RequestMethod.POST:
            resp = requests.post(**params, timeout=60)
        elif method == RequestMethod.GET:
            resp = requests.get(**params, timeout=60)
        else:
            raise_invalid_request()
        time_spent = t0 - time.time()
        resp.raise_for_status()
        logger.debug(f"{method} {url} complete - status code {resp.status_code} in {time_spent} sec")
    except Exception:
        logger.error(traceback.format_exc())
        raise
    else:
        return resp


def _handle_csv_upload(url: str, column_name: str, data: list[str], params: dict) -> str:
    """Upload a CSV file for batch enrichment processing.

    Args:
        url: API endpoint URL for the upload.
        column_name: CSV column header (e.g., 'appId', 'adDomain').
        data: List of values to include in the CSV.
        params: Additional query parameters.

    Returns:
        Download URL for retrieving the batch results.
    """
    with tempfile.TemporaryFile() as fp:
        fp.write(str("\n".join([column_name, *data]) + "\n").encode())
        fp.seek(0)
        resp = request_handler(method=RequestMethod.POST, url=url, data=fp, params=params)
        resp.raise_for_status()
    return resp.json()


@exponential_backoff(initial_delay=1, max_retries=10, max_delay=10, jitter=True)
def _handle_download(download_url: str) -> requests.Response:
    """Poll a download URL until batch enrichment results are ready.

    Uses exponential backoff with jitter to retry up to 10 times.

    Args:
        download_url: URL to poll for the completed batch results.

    Returns:
        The HTTP response containing newline-delimited JSON results.
    """
    return request_handler(
        method=RequestMethod.GET,
        url=download_url,
    )


def _handle_download_response(response: requests.Response, data_key: str = "data") -> dict:
    """Parse newline-delimited JSON response from batch enrichment downloads.

    Args:
        response: HTTP response containing newline-delimited JSON.
        data_key: Key to extract from each JSON line (default: 'data').

    Returns:
        Aggregated list of data entries from all JSON lines.
    """
    json_objects = response.text.strip().split("\n")
    datas = []
    for json_data in json_objects:
        data = json.loads(json_data)
        if data.get(data_key) is None:
            continue
        datas += data.get(data_key)
    return datas
```

- [ ] **Step 4: Add docstrings to logging_config.py**

Update `src/pixalate_open_mcp/utils/logging_config.py` — add docstrings to `get_default_log_dir` and `setup_logging`:

Add to `get_default_log_dir` (after `def get_default_log_dir() -> Path:`):
```python
    """Determine the platform-appropriate directory for MCP server log files.

    Returns:
        Path to the log directory for the current operating system.
    """
```

Add to `setup_logging` (after `def setup_logging(server_config: Optional[ServerConfig] = None) -> None:`):
```python
    """Configure logging for the Pixalate MCP server.

    Sets up rotating file handler and stderr handler with the configured log level.
    Captures logs from the project, MCP framework, and Uvicorn.

    Args:
        server_config: Server configuration with log level. Falls back to LOG_LEVEL env var.
    """
```

- [ ] **Step 5: Add docstring to config.py load_config**

Add to `load_config` in `src/pixalate_open_mcp/models/config.py` (after `def load_config() -> ServerConfig:`):
```python
    """Load server configuration from environment variables.

    Returns:
        ServerConfig with name, log level, and API key from environment.
    """
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run python -m pytest tests/test_tool_annotations.py -v`
Expected: All PASS

- [ ] **Step 7: Run full quality checks**

Run: `uv run pre-commit run -a && uv run mypy`
Expected: All checks pass

- [ ] **Step 8: Commit**

```bash
git add src/pixalate_open_mcp/utils/request.py src/pixalate_open_mcp/utils/logging_config.py src/pixalate_open_mcp/models/config.py tests/test_tool_annotations.py
git commit -m "feat: remove user params from logs and add utility docstrings"
```

---

### Task 7: Add Privacy Policy to README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add Privacy section to README**

Add the following section after the "License" section and before the "Author" section in `README.md`:

```markdown
## Privacy

This MCP server sends user-provided parameters (such as IP addresses, device IDs, app IDs, and domain names) to
Pixalate's APIs for processing. No conversation data is collected or stored by the server.

For details on how Pixalate handles data, see the [Pixalate Privacy Policy](https://www.pixalate.com/privacy-policy).
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add privacy policy section to README"
```

---

### Task 8: Final Verification

- [ ] **Step 1: Run full test suite**

Run: `uv run python -m pytest tests/ -v --cov --cov-config=pyproject.toml`
Expected: All tests PASS

- [ ] **Step 2: Run all quality checks**

Run: `make check`
Expected: All checks pass (ruff, mypy, deptry)

- [ ] **Step 3: Run pre-commit hooks**

Run: `uv run pre-commit run -a`
Expected: All hooks pass

- [ ] **Step 4: Verify tool names under 64 characters**

Run: `uv run python -c "from pixalate_open_mcp.server.app import server; [print(f'{len(t.name):3d} {t.name}') for t in server._tool_manager._tools.values()]"`
Expected: All names under 64 characters

- [ ] **Step 5: Manual compliance checklist**

Verify each requirement:
- [ ] 5E: All tools have readOnlyHint, destructiveHint, title annotations
- [ ] 5A: All 11 tool handlers have try/except with helpful error messages
- [ ] 3A: README contains privacy policy link to pixalate.com/privacy-policy
- [ ] 1D: request.py no longer logs user-supplied params
- [ ] 5F: streamable-http transport option available
- [ ] 5C: All tool names under 64 characters
- [ ] All functions have docstrings
