import json
import tempfile
import time
import traceback
from typing import Literal

import requests

from pixalate_open_mcp.models.config import load_config
from pixalate_open_mcp.utils.logging_config import logger

config = load_config()


class RequestMethod:
    POST = "POST"
    GET = "GET"


def raise_invalid_request():
    class InvalidRequestMethod(Exception):
        pass

    raise InvalidRequestMethod()


def request_handler(method: Literal[RequestMethod], url: str, **kwargs):
    try:
        params = {
            "url": url,
            "headers": {"x-api-key": config.x_api_key, "Accept": "application/json", "Content-Type": "text/csv"},
            **kwargs,
        }
        logger.debug(f"{method} {url} {params} start")
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
    with tempfile.TemporaryFile() as fp:
        fp.write(str("\n".join([column_name, *data]) + "\n").encode())
        fp.seek(0)
        resp = request_handler(method=RequestMethod.POST, url=url, data=fp, params=params)
        resp.raise_for_status()
    # download_url = resp.json()
    return resp.json()


class MaxRetriesExceeded(Exception):
    def __init__(self, message, max_retries, download_url):
        super().__init__(message)
        self.max_retries = max_retries
        self.download_url = download_url
        self.full_message = f"Retry max {self.max_retries} times to get document from {self.download_url}"


def _handle_download(
    download_url: str, max_retries: int = 10, ms_wait_between_retry: int = 100, data_key: str = "data"
) -> dict:
    retry, retry_count = True, 1
    while retry:
        response = request_handler(
            method=RequestMethod.GET,
            url=download_url,
        )
        if response.status_code == 200:
            retry = False
        else:
            time.sleep(ms_wait_between_retry)
            retry_count += 1
        if retry_count > max_retries:
            raise MaxRetriesExceeded("", max_retries, download_url)

    json_objects = response.text.strip().split("\n")
    datas = []
    for json_data in json_objects:
        data = json.loads(json_data)
        if data.get(data_key) is None:
            continue
        datas += data.get(data_key)
    return datas
