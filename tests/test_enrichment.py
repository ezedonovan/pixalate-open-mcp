"""Tests for enrichment API tools."""

from unittest.mock import MagicMock, patch

import requests

from pixalate_open_mcp.models.enrichment import (
    EnrichmentCTVRequest,
    EnrichmentDomainRequest,
    EnrichmentMobileRequest,
)
from pixalate_open_mcp.tools.enrichment.tools import (
    _handle_enrichment_request,
    get_enrichment_ctv_app,
    get_enrichment_ctv_metadata,
    get_enrichment_domains,
    get_enrichment_domains_metadata,
    get_enrichment_mobile_app,
    get_enrichment_mobile_metadata,
    toolset,
)

MODULE = "pixalate_open_mcp.tools.enrichment.tools"


# ---------------------------------------------------------------------------
# Metadata tests
# ---------------------------------------------------------------------------


class TestGetEnrichmentMobileMetadata:
    def test_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"quota": 100}

        with patch(f"{MODULE}.request_handler", return_value=mock_resp):
            result = get_enrichment_mobile_metadata()

        assert result == {"quota": 100}

    def test_http_error(self):
        mock_resp = MagicMock()
        http_err = requests.HTTPError(response=MagicMock(status_code=500))
        mock_resp.raise_for_status.side_effect = http_err

        with patch(f"{MODULE}.request_handler", return_value=mock_resp):
            result = get_enrichment_mobile_metadata()

        assert "error" in result
        assert "500" in result["error"]

    def test_connection_error(self):
        with patch(f"{MODULE}.request_handler", side_effect=requests.ConnectionError):
            result = get_enrichment_mobile_metadata()

        assert "error" in result
        assert "connect" in result["error"].lower()

    def test_timeout(self):
        with patch(f"{MODULE}.request_handler", side_effect=requests.Timeout):
            result = get_enrichment_mobile_metadata()

        assert "error" in result
        assert "timed out" in result["error"]

    def test_unexpected_exception(self):
        with patch(f"{MODULE}.request_handler", side_effect=Exception("boom")):
            result = get_enrichment_mobile_metadata()

        assert "error" in result
        assert "boom" in result["error"]


class TestGetEnrichmentCTVMetadata:
    def test_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"lastUpdated": "2025-01-01"}

        with patch(f"{MODULE}.request_handler", return_value=mock_resp):
            result = get_enrichment_ctv_metadata()

        assert result == {"lastUpdated": "2025-01-01"}

    def test_http_error(self):
        mock_resp = MagicMock()
        http_err = requests.HTTPError(response=MagicMock(status_code=404))
        mock_resp.raise_for_status.side_effect = http_err

        with patch(f"{MODULE}.request_handler", return_value=mock_resp):
            result = get_enrichment_ctv_metadata()

        assert "error" in result
        assert "404" in result["error"]

    def test_connection_error(self):
        with patch(f"{MODULE}.request_handler", side_effect=requests.ConnectionError):
            result = get_enrichment_ctv_metadata()

        assert "error" in result
        assert "connect" in result["error"].lower()

    def test_timeout(self):
        with patch(f"{MODULE}.request_handler", side_effect=requests.Timeout):
            result = get_enrichment_ctv_metadata()

        assert "error" in result
        assert "timed out" in result["error"]

    def test_unexpected_exception(self):
        with patch(f"{MODULE}.request_handler", side_effect=Exception("ctv boom")):
            result = get_enrichment_ctv_metadata()

        assert "error" in result
        assert "ctv boom" in result["error"]


class TestGetEnrichmentDomainsMetadata:
    def test_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"quota": 500, "lastUpdated": "2025-03-01"}

        with patch(f"{MODULE}.request_handler", return_value=mock_resp):
            result = get_enrichment_domains_metadata()

        assert result == {"quota": 500, "lastUpdated": "2025-03-01"}

    def test_http_error(self):
        mock_resp = MagicMock()
        http_err = requests.HTTPError(response=MagicMock(status_code=401))
        mock_resp.raise_for_status.side_effect = http_err

        with patch(f"{MODULE}.request_handler", return_value=mock_resp):
            result = get_enrichment_domains_metadata()

        assert "error" in result
        assert "401" in result["error"]

    def test_connection_error(self):
        with patch(f"{MODULE}.request_handler", side_effect=requests.ConnectionError):
            result = get_enrichment_domains_metadata()

        assert "error" in result
        assert "connect" in result["error"].lower()

    def test_timeout(self):
        with patch(f"{MODULE}.request_handler", side_effect=requests.Timeout):
            result = get_enrichment_domains_metadata()

        assert "error" in result
        assert "timed out" in result["error"]

    def test_unexpected_exception(self):
        with patch(f"{MODULE}.request_handler", side_effect=Exception("domains meta boom")):
            result = get_enrichment_domains_metadata()

        assert "error" in result
        assert "domains meta boom" in result["error"]


# ---------------------------------------------------------------------------
# App / domain tests
# ---------------------------------------------------------------------------


class TestGetEnrichmentMobileApp:
    def test_single_id(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"app": "data"}

        with patch(f"{MODULE}.request_handler", return_value=mock_resp):
            result = get_enrichment_mobile_app(EnrichmentMobileRequest(appIds=["123"]))

        assert result == {"app": "data"}

    def test_multiple_ids(self):
        with (
            patch(f"{MODULE}._handle_csv_upload", return_value="http://download") as mock_upload,
            patch(f"{MODULE}._handle_download", return_value=MagicMock()) as mock_download,
            patch(f"{MODULE}._handle_download_response", return_value=[{"data": 1}]) as mock_resp,
        ):
            result = get_enrichment_mobile_app(EnrichmentMobileRequest(appIds=["123", "456"]))

        assert result == [{"data": 1}]
        mock_upload.assert_called_once()
        mock_download.assert_called_once_with("http://download")
        mock_resp.assert_called_once()

    def test_http_error(self):
        http_err = requests.HTTPError(response=MagicMock(status_code=503))

        with patch(f"{MODULE}.request_handler", side_effect=http_err):
            result = get_enrichment_mobile_app(EnrichmentMobileRequest(appIds=["123"]))

        assert "error" in result
        assert "503" in result["error"]

    def test_connection_error(self):
        with patch(f"{MODULE}.request_handler", side_effect=requests.ConnectionError):
            result = get_enrichment_mobile_app(EnrichmentMobileRequest(appIds=["123"]))

        assert "error" in result
        assert "connect" in result["error"].lower()

    def test_timeout(self):
        with patch(f"{MODULE}.request_handler", side_effect=requests.Timeout):
            result = get_enrichment_mobile_app(EnrichmentMobileRequest(appIds=["123"]))

        assert "error" in result
        assert "timed out" in result["error"]

    def test_unexpected_exception(self):
        with patch(f"{MODULE}.request_handler", side_effect=Exception("mobile app boom")):
            result = get_enrichment_mobile_app(EnrichmentMobileRequest(appIds=["123"]))

        assert "error" in result
        assert "mobile app boom" in result["error"]


class TestGetEnrichmentCTVApp:
    def test_single_id(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ctv": "app_data"}

        with patch(f"{MODULE}.request_handler", return_value=mock_resp):
            result = get_enrichment_ctv_app(EnrichmentCTVRequest(appIds=["456"], device="roku"))

        assert result == {"ctv": "app_data"}

    def test_http_error(self):
        mock_resp = MagicMock()
        http_err = requests.HTTPError(response=MagicMock(status_code=403))
        mock_resp.raise_for_status.side_effect = http_err

        # request_handler itself raises for status internally; simulate that
        with patch(f"{MODULE}.request_handler", side_effect=http_err):
            result = get_enrichment_ctv_app(EnrichmentCTVRequest(appIds=["456"], device="roku"))

        assert "error" in result
        assert "403" in result["error"]

    def test_connection_error(self):
        with patch(f"{MODULE}.request_handler", side_effect=requests.ConnectionError):
            result = get_enrichment_ctv_app(EnrichmentCTVRequest(appIds=["456"], device="roku"))

        assert "error" in result
        assert "connect" in result["error"].lower()

    def test_timeout(self):
        with patch(f"{MODULE}.request_handler", side_effect=requests.Timeout):
            result = get_enrichment_ctv_app(EnrichmentCTVRequest(appIds=["456"], device="roku"))

        assert "error" in result
        assert "timed out" in result["error"]

    def test_unexpected_exception(self):
        with patch(f"{MODULE}.request_handler", side_effect=Exception("ctv app boom")):
            result = get_enrichment_ctv_app(EnrichmentCTVRequest(appIds=["456"], device="roku"))

        assert "error" in result
        assert "ctv app boom" in result["error"]


class TestGetEnrichmentDomains:
    def test_single_domain(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"domain": "cnn.com", "risk": "low"}

        with patch(f"{MODULE}.request_handler", return_value=mock_resp):
            result = get_enrichment_domains(EnrichmentDomainRequest(adDomain=["cnn.com"]))

        assert result == {"domain": "cnn.com", "risk": "low"}

    def test_http_error(self):
        http_err = requests.HTTPError(response=MagicMock(status_code=429))

        with patch(f"{MODULE}.request_handler", side_effect=http_err):
            result = get_enrichment_domains(EnrichmentDomainRequest(adDomain=["cnn.com"]))

        assert "error" in result
        assert "429" in result["error"]

    def test_connection_error(self):
        with patch(f"{MODULE}.request_handler", side_effect=requests.ConnectionError):
            result = get_enrichment_domains(EnrichmentDomainRequest(adDomain=["cnn.com"]))

        assert "error" in result
        assert "connect" in result["error"].lower()

    def test_timeout(self):
        with patch(f"{MODULE}.request_handler", side_effect=requests.Timeout):
            result = get_enrichment_domains(EnrichmentDomainRequest(adDomain=["cnn.com"]))

        assert "error" in result
        assert "timed out" in result["error"]

    def test_unexpected_exception(self):
        with patch(f"{MODULE}.request_handler", side_effect=Exception("domains boom")):
            result = get_enrichment_domains(EnrichmentDomainRequest(adDomain=["cnn.com"]))

        assert "error" in result
        assert "domains boom" in result["error"]


# ---------------------------------------------------------------------------
# Internal helper tests
# ---------------------------------------------------------------------------


class TestHandleEnrichmentRequest:
    def test_single_id_path_uses_request_handler(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"result": "ok"}

        with (
            patch(f"{MODULE}.request_handler", return_value=mock_resp) as mock_handler,
            patch(f"{MODULE}._handle_csv_upload") as mock_upload,
        ):
            result = _handle_enrichment_request(
                url="https://api.pixalate.com/api/v2/mrt/apps",
                app_or_domain_ids=["single_id"],
                column_name="appId",
                params={},
            )

        assert result == {"result": "ok"}
        mock_handler.assert_called_once()
        mock_upload.assert_not_called()

    def test_batch_path_uses_csv_upload(self):
        mock_download_resp = MagicMock()

        with (
            patch(f"{MODULE}.request_handler") as mock_handler,
            patch(f"{MODULE}._handle_csv_upload", return_value="http://download") as mock_upload,
            patch(f"{MODULE}._handle_download", return_value=mock_download_resp) as mock_download,
            patch(f"{MODULE}._handle_download_response", return_value=[{"batch": "data"}]) as mock_dl_resp,
        ):
            result = _handle_enrichment_request(
                url="https://api.pixalate.com/api/v2/mrt/apps",
                app_or_domain_ids=["id1", "id2"],
                column_name="appId",
                params={},
            )

        assert result == [{"batch": "data"}]
        mock_upload.assert_called_once()
        mock_download.assert_called_once_with("http://download")
        mock_dl_resp.assert_called_once_with(mock_download_resp)
        mock_handler.assert_not_called()


# ---------------------------------------------------------------------------
# Toolset
# ---------------------------------------------------------------------------


class TestEnrichmentToolset:
    def test_has_six_tools(self):
        assert toolset.name == "Enrichment API"
        assert len(toolset.tools) == 6
