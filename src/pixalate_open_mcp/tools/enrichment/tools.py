import os
from urllib.parse import urlencode

from pixalate_open_mcp.models.enrichment import EnrichmentCTVRequest, EnrichmentDomainRequest, EnrichmentMobileRequest
from pixalate_open_mcp.models.metadata import Metadata
from pixalate_open_mcp.models.tools import PixalateTool, PixalateToolset
from pixalate_open_mcp.utils.request import (
    RequestMethod,
    _handle_csv_upload,
    _handle_download,
    _handle_download_response,
    request_handler,
)

BASE_URL = "https://api.pixalate.com/api/v2/"


def get_enrichment_mobile_metadata(pretty: bool = False) -> dict | Metadata:
    resp = request_handler(
        method=RequestMethod.GET,
        url=os.path.join(BASE_URL, "mrt", "apps") + "?" + urlencode({"pretty": pretty}).lower(),
    )
    resp.raise_for_status()
    return resp.json()


def get_enrichment_mobile_app(request: EnrichmentMobileRequest) -> dict:
    return _handle_enrichment_request(
        url=os.path.join(BASE_URL, "mrt", "apps"),
        app_or_domain_ids=request.appIds,
        column_name="appId",
        params=request.to_params(),
    )


def get_enrichment_ctv_metadata(pretty: bool = False) -> dict | Metadata:
    resp = request_handler(
        method=RequestMethod.GET, url=os.path.join(BASE_URL, "mrt", "ctv") + "?" + urlencode({"pretty": pretty}).lower()
    )
    resp.raise_for_status()
    return resp.json()


def get_enrichment_ctv_app(request: EnrichmentCTVRequest) -> dict:
    return _handle_enrichment_request(
        url=os.path.join(BASE_URL, "mrt", "ctv"),
        app_or_domain_ids=request.appIds,
        column_name="appId",
        params=request.to_params(),
    )


def get_enrichment_domains_metadata(pretty: bool = False) -> dict | Metadata:
    resp = request_handler(
        method=RequestMethod.GET,
        url=os.path.join(BASE_URL, "mrt", "domains") + "?" + urlencode({"pretty": pretty}).lower(),
    )
    resp.raise_for_status()
    return resp.json()


def get_enrichment_domains(request: EnrichmentDomainRequest) -> dict:
    return _handle_enrichment_request(
        url=os.path.join(BASE_URL, "mrt", "domains"),
        app_or_domain_ids=request.adDomain,
        column_name="adDomain",
        params=request.to_params(),
    )


def _handle_enrichment_request(url, app_or_domain_ids: list[str], column_name: str, params: dict) -> dict:
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
