"""Tests for analytics API tools."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from pixalate_open_mcp.models.analytics import AnalyticsRequest, QueryConstruct
from pixalate_open_mcp.tools.analytics.tools import get_analytics_metadata, get_analytics_report


@pytest.fixture
def minimal_analytics_request():
    """Return a minimal valid AnalyticsRequest for testing."""
    query = QueryConstruct(
        selectDimension=["adDomain"],
        selectMetric=["impressions"],
        dateFrom="2025-01-01",
        dateTo="2025-01-31",
    )
    return AnalyticsRequest(reportId="default", q=query)


# ---------------------------------------------------------------------------
# get_analytics_metadata tests
# ---------------------------------------------------------------------------


def test_get_analytics_metadata_success():
    mock_response = MagicMock()
    mock_response.json.return_value = {"quota": 100}
    mock_response.raise_for_status.return_value = None

    with patch("pixalate_open_mcp.tools.analytics.tools.request_handler", return_value=mock_response):
        result = get_analytics_metadata()

    assert result == {"quota": 100}


def test_get_analytics_metadata_http_error():
    mock_response = MagicMock()
    http_error = requests.HTTPError(response=MagicMock(status_code=403))
    mock_response.raise_for_status.side_effect = http_error

    with patch("pixalate_open_mcp.tools.analytics.tools.request_handler", return_value=mock_response):
        result = get_analytics_metadata()

    assert "error" in result
    assert "403" in result["error"]


def test_get_analytics_metadata_connection_error():
    with patch(
        "pixalate_open_mcp.tools.analytics.tools.request_handler",
        side_effect=requests.ConnectionError("connection refused"),
    ):
        result = get_analytics_metadata()

    assert "error" in result
    assert "connect" in result["error"].lower()


def test_get_analytics_metadata_timeout():
    with patch(
        "pixalate_open_mcp.tools.analytics.tools.request_handler",
        side_effect=requests.Timeout("request timed out"),
    ):
        result = get_analytics_metadata()

    assert "error" in result
    assert "timed out" in result["error"].lower()


# ---------------------------------------------------------------------------
# get_analytics_report tests
# ---------------------------------------------------------------------------


def test_get_analytics_report_success(minimal_analytics_request):
    mock_response = MagicMock()
    mock_response.json.return_value = {"docs": []}

    with patch("pixalate_open_mcp.tools.analytics.tools.request_handler", return_value=mock_response):
        result = get_analytics_report(minimal_analytics_request)

    assert result == {"docs": []}


def test_get_analytics_report_passes_correct_url(minimal_analytics_request):
    mock_response = MagicMock()
    mock_response.json.return_value = {"docs": []}

    with patch("pixalate_open_mcp.tools.analytics.tools.request_handler", return_value=mock_response) as mock_handler:
        get_analytics_report(minimal_analytics_request)

    called_kwargs = mock_handler.call_args
    url = (
        called_kwargs.kwargs.get("url") or called_kwargs.args[0] if called_kwargs.args else called_kwargs.kwargs["url"]
    )
    assert minimal_analytics_request.reportId in url


def test_get_analytics_report_http_error(minimal_analytics_request):
    http_error = requests.HTTPError(response=MagicMock(status_code=500))

    with patch(
        "pixalate_open_mcp.tools.analytics.tools.request_handler",
        side_effect=http_error,
    ):
        result = get_analytics_report(minimal_analytics_request)

    assert "error" in result


def test_get_analytics_report_connection_error(minimal_analytics_request):
    with patch(
        "pixalate_open_mcp.tools.analytics.tools.request_handler",
        side_effect=requests.ConnectionError("connection refused"),
    ):
        result = get_analytics_report(minimal_analytics_request)

    assert "error" in result
    assert "connect" in result["error"].lower()


# ---------------------------------------------------------------------------
# Toolset structure tests
# ---------------------------------------------------------------------------


def test_analytics_toolset_has_two_tools():
    from pixalate_open_mcp.tools.analytics.tools import toolset

    assert toolset.name == "Analytics API"
    assert len(toolset.tools) == 2


def test_get_analytics_metadata_generic_exception():
    with patch(
        "pixalate_open_mcp.tools.analytics.tools.request_handler",
        side_effect=Exception("something broke"),
    ):
        result = get_analytics_metadata()

    assert "error" in result
    assert "Unexpected" in result["error"]


def test_get_analytics_report_timeout():
    query = QueryConstruct(
        selectDimension=["day"],
        selectMetric=["impressions"],
        dateFrom="2025-01-01",
        dateTo="2025-01-31",
    )
    request = AnalyticsRequest(reportId="default", q=query)

    with patch(
        "pixalate_open_mcp.tools.analytics.tools.request_handler",
        side_effect=requests.Timeout("request timed out"),
    ):
        result = get_analytics_report(request)

    assert "error" in result
    assert "timed out" in result["error"].lower()


def test_get_analytics_report_generic_exception():
    query = QueryConstruct(
        selectDimension=["day"],
        selectMetric=["impressions"],
        dateFrom="2025-01-01",
        dateTo="2025-01-31",
    )
    request = AnalyticsRequest(reportId="default", q=query)

    with patch(
        "pixalate_open_mcp.tools.analytics.tools.request_handler",
        side_effect=Exception("something broke"),
    ):
        result = get_analytics_report(request)

    assert "error" in result
    assert "Unexpected" in result["error"]
