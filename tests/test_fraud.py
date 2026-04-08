"""Tests for fraud API tools."""

from unittest.mock import MagicMock, patch

import requests

from pixalate_open_mcp.models.fraud import FraudRequest
from pixalate_open_mcp.tools.fraud.tools import get_fraud, get_fraud_metadata, toolset

# ---------------------------------------------------------------------------
# get_fraud_metadata tests
# ---------------------------------------------------------------------------


def test_get_fraud_metadata_success():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"quota": 50}
    mock_resp.raise_for_status.return_value = None

    with patch("pixalate_open_mcp.tools.fraud.tools.request_handler", return_value=mock_resp):
        result = get_fraud_metadata()

    assert result == {"quota": 50}


def test_get_fraud_metadata_http_error():
    mock_response = MagicMock()
    mock_response.status_code = 401

    http_error = requests.HTTPError(response=mock_response)

    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = http_error

    with patch("pixalate_open_mcp.tools.fraud.tools.request_handler", return_value=mock_resp):
        result = get_fraud_metadata()

    assert "error" in result
    assert "401" in result["error"]


def test_get_fraud_metadata_timeout():
    with patch(
        "pixalate_open_mcp.tools.fraud.tools.request_handler",
        side_effect=requests.Timeout,
    ):
        result = get_fraud_metadata()

    assert "error" in result
    assert "timed out" in result["error"].lower()


# ---------------------------------------------------------------------------
# get_fraud tests
# ---------------------------------------------------------------------------


def test_get_fraud_success():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"probability": 0.85}

    with patch("pixalate_open_mcp.tools.fraud.tools.request_handler", return_value=mock_resp):
        result = get_fraud(FraudRequest(ip="1.2.3.4"))

    assert result == {"probability": 0.85}


def test_get_fraud_passes_params():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {}

    with patch("pixalate_open_mcp.tools.fraud.tools.request_handler", return_value=mock_resp) as mock_handler:
        get_fraud(FraudRequest(ip="1.2.3.4", deviceId="abc"))

    _args, kwargs = mock_handler.call_args
    assert kwargs["params"] == {"ip": "1.2.3.4", "deviceId": "abc"}


def test_get_fraud_connection_error():
    with patch(
        "pixalate_open_mcp.tools.fraud.tools.request_handler",
        side_effect=requests.ConnectionError,
    ):
        result = get_fraud(FraudRequest(ip="1.2.3.4"))

    assert "error" in result
    assert "connect" in result["error"].lower()


def test_get_fraud_http_error():
    mock_response = MagicMock()
    mock_response.status_code = 403

    http_error = requests.HTTPError(response=mock_response)

    mock_resp = MagicMock()
    mock_resp.json.side_effect = http_error

    with patch("pixalate_open_mcp.tools.fraud.tools.request_handler", return_value=mock_resp):
        result = get_fraud(FraudRequest(ip="1.2.3.4"))

    assert "error" in result
    assert "403" in result["error"]


# ---------------------------------------------------------------------------
# toolset tests
# ---------------------------------------------------------------------------


def test_fraud_toolset_has_two_tools():
    assert toolset.name == "Fraud API"
    assert len(toolset.tools) == 2
