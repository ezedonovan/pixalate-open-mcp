"""Tests for HTTP request handling utilities."""

import logging
from unittest.mock import MagicMock, patch

import pytest
import requests

from pixalate_open_mcp.utils.request import (
    RequestMethod,
    _handle_csv_upload,
    _handle_download_response,
    request_handler,
)


def _make_mock_response(status_code=200, json_return=None):
    """Return a MagicMock response with raise_for_status as a no-op."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.raise_for_status = MagicMock()
    if json_return is not None:
        mock_resp.json.return_value = json_return
    return mock_resp


# ---------------------------------------------------------------------------
# request_handler - method dispatch
# ---------------------------------------------------------------------------


def test_request_handler_get_dispatches_to_requests_get():
    """request_handler with GET should call requests.get."""
    mock_resp = _make_mock_response()
    with patch("pixalate_open_mcp.utils.request.requests.get", return_value=mock_resp) as mock_get:
        request_handler(RequestMethod.GET, "https://example.com/api")
        mock_get.assert_called_once()


def test_request_handler_post_dispatches_to_requests_post():
    """request_handler with POST should call requests.post."""
    mock_resp = _make_mock_response()
    with patch("pixalate_open_mcp.utils.request.requests.post", return_value=mock_resp) as mock_post:
        request_handler(RequestMethod.POST, "https://example.com/api")
        mock_post.assert_called_once()


def test_request_handler_invalid_method_raises():
    """request_handler with an unsupported method should raise an exception."""
    with pytest.raises(BaseException):  # noqa: B017
        request_handler("DELETE", "https://example.com/api")


# ---------------------------------------------------------------------------
# request_handler - headers
# ---------------------------------------------------------------------------


def test_request_handler_sets_api_key_header():
    """request_handler should include the x-api-key header on every call."""
    mock_resp = _make_mock_response()
    with patch("pixalate_open_mcp.utils.request.requests.get", return_value=mock_resp) as mock_get:
        request_handler(RequestMethod.GET, "https://example.com/api")
        call_kwargs = mock_get.call_args.kwargs
        assert "headers" in call_kwargs
        assert "x-api-key" in call_kwargs["headers"]


# ---------------------------------------------------------------------------
# request_handler - logging
# ---------------------------------------------------------------------------


def test_request_handler_does_not_log_params(caplog):
    """Sensitive query-parameter values must not appear in log output."""
    mock_resp = _make_mock_response()
    with (
        patch("pixalate_open_mcp.utils.request.requests.get", return_value=mock_resp),
        caplog.at_level(logging.DEBUG, logger="pixalate_open_mcp"),
    ):
        request_handler(RequestMethod.GET, "https://example.com/api", params={"ip": "1.2.3.4"})

    for record in caplog.records:
        assert "1.2.3.4" not in record.message


def test_request_handler_logs_url_and_method(caplog):
    """request_handler should log the HTTP method and URL at DEBUG level."""
    mock_resp = _make_mock_response()
    with (
        patch("pixalate_open_mcp.utils.request.requests.get", return_value=mock_resp),
        caplog.at_level(logging.DEBUG, logger="pixalate_open_mcp"),
    ):
        request_handler(RequestMethod.GET, "https://example.com/api")

    all_messages = " ".join(record.message for record in caplog.records)
    assert "GET" in all_messages
    assert "example.com" in all_messages


# ---------------------------------------------------------------------------
# request_handler - HTTP error propagation
# ---------------------------------------------------------------------------


def test_request_handler_raises_on_http_error():
    """request_handler should propagate HTTPError raised by raise_for_status."""
    mock_resp = _make_mock_response()
    mock_resp.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
    with (
        patch("pixalate_open_mcp.utils.request.requests.get", return_value=mock_resp),
        pytest.raises(requests.HTTPError),
    ):
        request_handler(RequestMethod.GET, "https://example.com/api")


# ---------------------------------------------------------------------------
# _handle_csv_upload
# ---------------------------------------------------------------------------


def test_handle_csv_upload_returns_download_url():
    """_handle_csv_upload should return the JSON body from the server response."""
    mock_resp = _make_mock_response(json_return="http://download-url")
    with patch("pixalate_open_mcp.utils.request.request_handler", return_value=mock_resp):
        result = _handle_csv_upload(
            url="https://example.com/upload",
            column_name="ip",
            data=["1.1.1.1", "2.2.2.2"],
            params={"type": "ipv4"},
        )
    assert result == "http://download-url"


# ---------------------------------------------------------------------------
# _handle_download_response
# ---------------------------------------------------------------------------


def test_handle_download_response_parses_ndjson():
    """_handle_download_response should aggregate all 'data' arrays across NDJSON lines."""
    mock_resp = MagicMock()
    mock_resp.text = '{"data": [1, 2]}\n{"data": [3]}'
    result = _handle_download_response(mock_resp)
    assert result == [1, 2, 3]


def test_handle_download_response_skips_missing_data_key():
    """_handle_download_response should ignore lines that lack the target key."""
    mock_resp = MagicMock()
    mock_resp.text = '{"data": [1]}\n{"other": "value"}\n{"data": [2]}'
    result = _handle_download_response(mock_resp)
    assert result == [1, 2]
