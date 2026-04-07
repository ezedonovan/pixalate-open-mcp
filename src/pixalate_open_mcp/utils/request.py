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
    """Raise an exception for an unsupported HTTP request method.

    Raises:
        InvalidRequestMethod: Always raised to signal an invalid method was provided.
    """

    class InvalidRequestMethod(Exception):
        pass

    raise InvalidRequestMethod()


def request_handler(method: Literal[RequestMethod], url: str, **kwargs) -> requests.Response:
    """Send an HTTP request to the Pixalate API and return the response.

    Args:
        method: The HTTP method to use (GET or POST).
        url: The fully-qualified URL to send the request to.
        **kwargs: Additional keyword arguments passed to the underlying requests call
            (e.g., ``params``, ``data``).

    Returns:
        The HTTP response object from the successful request.

    Raises:
        requests.HTTPError: If the server returns a non-2xx status code.
        InvalidRequestMethod: If ``method`` is not GET or POST.
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
    """Upload a list of values as a CSV file to the given URL.

    Args:
        url: The endpoint URL to POST the CSV data to.
        column_name: The header name written as the first row of the CSV.
        data: The list of values to include in the CSV body.
        params: Query parameters to include with the request.

    Returns:
        The JSON response body returned by the server.
    """
    with tempfile.TemporaryFile() as fp:
        fp.write(str("\n".join([column_name, *data]) + "\n").encode())
        fp.seek(0)
        resp = request_handler(method=RequestMethod.POST, url=url, data=fp, params=params)
        resp.raise_for_status()
    return resp.json()


@exponential_backoff(initial_delay=1, max_retries=10, max_delay=10, jitter=True)
def _handle_download(download_url: str) -> requests.Response:
    """Fetch a download URL, retrying with exponential backoff on failure.

    Args:
        download_url: The URL to download data from.

    Returns:
        The HTTP response object from the successful GET request.
    """
    return request_handler(
        method=RequestMethod.GET,
        url=download_url,
    )


def _handle_download_response(response: requests.Response, data_key: str = "data") -> dict:
    """Parse a newline-delimited JSON response and extract records by key.

    Args:
        response: The HTTP response whose text contains newline-delimited JSON.
        data_key: The key within each JSON object whose value is appended to
            the result list. Defaults to ``"data"``.

    Returns:
        A list of all records collected from the ``data_key`` field across
        every JSON object in the response body.
    """
    json_objects = response.text.strip().split("\n")
    datas = []
    for json_data in json_objects:
        data = json.loads(json_data)
        if data.get(data_key) is None:
            continue
        datas += data.get(data_key)
    return datas
