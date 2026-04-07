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
    """Retrieve metadata information for Pixalate analytics reports.

    Args:
        pretty: Whether to pretty-print the JSON response.

    Returns:
        A dict containing the current user's quota state and the date the
        analytics reports database was last updated, or an error dict if
        the request fails.
    """
    try:
        resp = request_handler(
            method=RequestMethod.GET,
            url=os.path.join(BASE_URL, "analytics", "reports") + "?" + urlencode({"pretty": pretty}).lower(),
        )
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        logger.error(f"HTTP error fetching analytics metadata: {e}")
        return {"error": f"API request failed with status {e.response.status_code}", "details": str(e)}
    except requests.ConnectionError as e:
        logger.error(f"Connection error fetching analytics metadata: {e}")
        return {"error": "Unable to connect to Pixalate API. Check your network connection."}
    except requests.Timeout as e:
        logger.error(f"Timeout fetching analytics metadata: {e}")
        return {"error": "Request to Pixalate API timed out. Please try again."}
    except Exception as e:
        logger.error(f"Unexpected error fetching analytics metadata: {e}")
        return {"error": f"Unexpected error: {e!s}"}


def get_analytics_report(request: AnalyticsRequest) -> dict | AnalyticsResponse:
    """Retrieve an analytics report from the Pixalate API.

    Args:
        request: An AnalyticsRequest object specifying the report ID and query parameters.

    Returns:
        A dict containing the list of report items, or an error dict if the
        request fails.
    """
    try:
        resp = request_handler(
            method=RequestMethod.GET,
            url=os.path.join(BASE_URL, "analytics", "reports", request.reportId),
            params=request.to_params(),
        )
        return resp.json()
    except requests.HTTPError as e:
        logger.error(f"HTTP error fetching analytics report: {e}")
        return {"error": f"API request failed with status {e.response.status_code}", "details": str(e)}
    except requests.ConnectionError as e:
        logger.error(f"Connection error fetching analytics report: {e}")
        return {"error": "Unable to connect to Pixalate API. Check your network connection."}
    except requests.Timeout as e:
        logger.error(f"Timeout fetching analytics report: {e}")
        return {"error": "Request to Pixalate API timed out. Please try again."}
    except Exception as e:
        logger.error(f"Unexpected error fetching analytics report: {e}")
        return {"error": f"Unexpected error: {e!s}"}


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
