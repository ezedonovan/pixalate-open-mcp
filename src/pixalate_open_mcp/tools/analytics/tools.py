import os
import traceback
from urllib.parse import urlencode

from pixalate_open_mcp.models.analytics import AnalyticsRequest, AnalyticsResponse
from pixalate_open_mcp.models.metadata import Metadata
from pixalate_open_mcp.models.tools import PixalateTool, PixalateToolset
from pixalate_open_mcp.utils.logging_config import logger
from pixalate_open_mcp.utils.request import RequestMethod, request_handler

BASE_URL = "https://api.pixalate.com/api/v2/"


def get_analytics_metadata(pretty: bool = False) -> dict | Metadata:
    resp = request_handler(
        method=RequestMethod.GET,
        url=os.path.join(BASE_URL, "analytics", "reports") + "?" + urlencode({"pretty": pretty}).lower(),
    )
    resp.raise_for_status()
    return resp.json()


def get_analytics_report(request: AnalyticsRequest) -> dict | AnalyticsResponse:
    try:
        logger.debug(f"Request: {request}")
        logger.debug(f"Query: {request.q.construct_query()}")
        resp = request_handler(
            method=RequestMethod.GET,
            url=os.path.join(BASE_URL, "analytics", "reports", request.reportId),
            params=request.to_params(),
        )
        return resp.json()
    except Exception as e:
        logger.error(traceback.format_exc())
        return {"error": str(e)}


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
