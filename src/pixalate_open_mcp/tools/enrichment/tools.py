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
    """Retrieve metadata information for mobile applications.

    Args:
        pretty: Whether to return pretty-printed JSON output.

    Returns:
        A dict containing the current user's quota state and the date the
        mobile applications database was last updated, or an error dict.
    """
    try:
        resp = request_handler(
            method=RequestMethod.GET,
            url=os.path.join(BASE_URL, "mrt", "apps") + "?" + urlencode({"pretty": pretty}).lower(),
        )
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        logger.error("HTTP error fetching mobile metadata: %s", e)
        return {"error": f"API request failed with status {e.response.status_code}", "details": str(e)}
    except requests.ConnectionError as e:
        logger.error("Connection error fetching mobile metadata: %s", e)
        return {"error": "Unable to connect to Pixalate API. Check your network connection."}
    except requests.Timeout as e:
        logger.error("Timeout fetching mobile metadata: %s", e)
        return {"error": "Request to Pixalate API timed out. Please try again."}
    except Exception as e:
        logger.error("Unexpected error fetching mobile metadata: %s", e)
        return {"error": f"Unexpected error: {e!s}"}


def get_enrichment_mobile_app(request: EnrichmentMobileRequest) -> dict:
    """Retrieve risk ratings and reputational data for mobile applications.

    Args:
        request: An EnrichmentMobileRequest containing app IDs and filter parameters.

    Returns:
        A dict containing a list of app information partitioned by region and device,
        or an error dict if the request fails.
    """
    try:
        return _handle_enrichment_request(
            url=os.path.join(BASE_URL, "mrt", "apps"),
            app_or_domain_ids=request.appIds,
            column_name="appId",
            params=request.to_params(),
        )
    except requests.HTTPError as e:
        logger.error("HTTP error fetching mobile app data: %s", e)
        return {"error": f"API request failed with status {e.response.status_code}", "details": str(e)}
    except requests.ConnectionError as e:
        logger.error("Connection error fetching mobile app data: %s", e)
        return {"error": "Unable to connect to Pixalate API. Check your network connection."}
    except requests.Timeout as e:
        logger.error("Timeout fetching mobile app data: %s", e)
        return {"error": "Request to Pixalate API timed out. Please try again."}
    except Exception as e:
        logger.error("Unexpected error fetching mobile app data: %s", e)
        return {"error": f"Unexpected error: {e!s}"}


def get_enrichment_ctv_metadata(pretty: bool = False) -> dict | Metadata:
    """Retrieve metadata information for connected TV applications.

    Args:
        pretty: Whether to return pretty-printed JSON output.

    Returns:
        A dict containing the current user's quota state and the date the
        Connected TV applications database was last updated, or an error dict.
    """
    try:
        resp = request_handler(
            method=RequestMethod.GET,
            url=os.path.join(BASE_URL, "mrt", "ctv") + "?" + urlencode({"pretty": pretty}).lower(),
        )
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        logger.error("HTTP error fetching CTV metadata: %s", e)
        return {"error": f"API request failed with status {e.response.status_code}", "details": str(e)}
    except requests.ConnectionError as e:
        logger.error("Connection error fetching CTV metadata: %s", e)
        return {"error": "Unable to connect to Pixalate API. Check your network connection."}
    except requests.Timeout as e:
        logger.error("Timeout fetching CTV metadata: %s", e)
        return {"error": "Request to Pixalate API timed out. Please try again."}
    except Exception as e:
        logger.error("Unexpected error fetching CTV metadata: %s", e)
        return {"error": f"Unexpected error: {e!s}"}


def get_enrichment_ctv_app(request: EnrichmentCTVRequest) -> dict:
    """Retrieve risk ratings and reputational data for CTV applications.

    Args:
        request: An EnrichmentCTVRequest containing app IDs and filter parameters.

    Returns:
        A dict containing a list of app information partitioned by region and device,
        or an error dict if the request fails.
    """
    try:
        return _handle_enrichment_request(
            url=os.path.join(BASE_URL, "mrt", "ctv"),
            app_or_domain_ids=request.appIds,
            column_name="appId",
            params=request.to_params(),
        )
    except requests.HTTPError as e:
        logger.error("HTTP error fetching CTV app data: %s", e)
        return {"error": f"API request failed with status {e.response.status_code}", "details": str(e)}
    except requests.ConnectionError as e:
        logger.error("Connection error fetching CTV app data: %s", e)
        return {"error": "Unable to connect to Pixalate API. Check your network connection."}
    except requests.Timeout as e:
        logger.error("Timeout fetching CTV app data: %s", e)
        return {"error": "Request to Pixalate API timed out. Please try again."}
    except Exception as e:
        logger.error("Unexpected error fetching CTV app data: %s", e)
        return {"error": f"Unexpected error: {e!s}"}


def get_enrichment_domains_metadata(pretty: bool = False) -> dict | Metadata:
    """Retrieve metadata information for domains.

    Args:
        pretty: Whether to return pretty-printed JSON output.

    Returns:
        A dict containing the current user's quota state and the date the
        domains database was last updated, or an error dict.
    """
    try:
        resp = request_handler(
            method=RequestMethod.GET,
            url=os.path.join(BASE_URL, "mrt", "domains") + "?" + urlencode({"pretty": pretty}).lower(),
        )
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        logger.error("HTTP error fetching domains metadata: %s", e)
        return {"error": f"API request failed with status {e.response.status_code}", "details": str(e)}
    except requests.ConnectionError as e:
        logger.error("Connection error fetching domains metadata: %s", e)
        return {"error": "Unable to connect to Pixalate API. Check your network connection."}
    except requests.Timeout as e:
        logger.error("Timeout fetching domains metadata: %s", e)
        return {"error": "Request to Pixalate API timed out. Please try again."}
    except Exception as e:
        logger.error("Unexpected error fetching domains metadata: %s", e)
        return {"error": f"Unexpected error: {e!s}"}


def get_enrichment_domains(request: EnrichmentDomainRequest) -> dict:
    """Retrieve risk ratings and reputational data for websites.

    Args:
        request: An EnrichmentDomainRequest containing ad domain names and filter parameters.

    Returns:
        A dict containing a list of domain information partitioned by region and device,
        or an error dict if the request fails.
    """
    try:
        return _handle_enrichment_request(
            url=os.path.join(BASE_URL, "mrt", "domains"),
            app_or_domain_ids=request.adDomain,
            column_name="adDomain",
            params=request.to_params(),
        )
    except requests.HTTPError as e:
        logger.error("HTTP error fetching domain data: %s", e)
        return {"error": f"API request failed with status {e.response.status_code}", "details": str(e)}
    except requests.ConnectionError as e:
        logger.error("Connection error fetching domain data: %s", e)
        return {"error": "Unable to connect to Pixalate API. Check your network connection."}
    except requests.Timeout as e:
        logger.error("Timeout fetching domain data: %s", e)
        return {"error": "Request to Pixalate API timed out. Please try again."}
    except Exception as e:
        logger.error("Unexpected error fetching domain data: %s", e)
        return {"error": f"Unexpected error: {e!s}"}


def _handle_enrichment_request(url, app_or_domain_ids: list[str], column_name: str, params: dict) -> dict:
    """Route an enrichment request to the appropriate handler based on input size.

    For bulk requests (more than one ID), uploads a CSV and polls for a download URL.
    For single-item requests, performs a direct GET request.

    Args:
        url: The base API endpoint URL.
        app_or_domain_ids: A list of app IDs or domain names to enrich.
        column_name: The column name to use in the CSV upload (e.g. "appId", "adDomain").
        params: Additional query parameters to include in the request.

    Returns:
        A dict containing the enrichment data returned by the Pixalate API.
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
