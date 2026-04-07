from unittest.mock import MagicMock, patch

import requests
from mcp.types import ToolAnnotations

from pixalate_open_mcp.models.tools import PixalateTool
from pixalate_open_mcp.server.app import register_tools


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

    version_call = [c for c in mock_server.add_tool.call_args_list if "Version" in c[1].get("title", "")]
    assert len(version_call) == 1
    ann = version_call[0][1]["annotations"]
    assert ann.openWorldHint is False


def test_analytics_metadata_handles_http_error():
    with patch("pixalate_open_mcp.tools.analytics.tools.request_handler") as mock:
        response = MagicMock()
        response.raise_for_status.side_effect = requests.HTTPError(response=MagicMock(status_code=403))
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


def test_fraud_metadata_handles_http_error():
    with patch("pixalate_open_mcp.tools.fraud.tools.request_handler") as mock:
        response = MagicMock()
        response.raise_for_status.side_effect = requests.HTTPError(response=MagicMock(status_code=401))
        mock.return_value = response
        from pixalate_open_mcp.tools.fraud.tools import get_fraud_metadata

        result = get_fraud_metadata()
        assert "error" in result


def test_fraud_handles_connection_error():
    with patch("pixalate_open_mcp.tools.fraud.tools.request_handler") as mock:
        mock.side_effect = requests.ConnectionError("Connection refused")
        from pixalate_open_mcp.models.fraud import FraudRequest
        from pixalate_open_mcp.tools.fraud.tools import get_fraud

        result = get_fraud(FraudRequest(ip="1.2.3.4"))
        assert "error" in result
        assert "connect" in result["error"].lower()


def test_enrichment_mobile_metadata_handles_http_error():
    with patch("pixalate_open_mcp.tools.enrichment.tools.request_handler") as mock:
        response = MagicMock()
        response.raise_for_status.side_effect = requests.HTTPError(response=MagicMock(status_code=500))
        mock.return_value = response
        from pixalate_open_mcp.tools.enrichment.tools import get_enrichment_mobile_metadata

        result = get_enrichment_mobile_metadata()
        assert "error" in result


def test_enrichment_domains_handles_connection_error():
    with patch("pixalate_open_mcp.tools.enrichment.tools.request_handler") as mock:
        mock.side_effect = requests.ConnectionError("Connection refused")
        from pixalate_open_mcp.models.enrichment import EnrichmentDomainRequest
        from pixalate_open_mcp.tools.enrichment.tools import get_enrichment_domains

        result = get_enrichment_domains(EnrichmentDomainRequest(adDomain=["cnn.com"]))
        assert "error" in result
        assert "connect" in result["error"].lower()
