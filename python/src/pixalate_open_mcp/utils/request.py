import json
import tempfile
import time
import traceback

import requests
from typing import Dict, Literal, List

from pixalate_open_mcp.utils.logging_config import logger
from pixalate_open_mcp.models.config import load_config

config = load_config()


class RequestMethod:
    POST = "POST"
    GET = "GET"


def request_handler(method: Literal[RequestMethod], url: str, **kwargs):
    try:
        params = {
            "url": url,
            "headers": {
                "x-api-key": config.x_api_key,
                "Accept": "application/json",
                "Content-Type": "text/csv"
            },
            **kwargs
        }
        logger.debug(f"{method} {url} {params} start")
        t0 = time.time()
        if method == RequestMethod.POST:
            resp = requests.post(**params)
        elif method == RequestMethod.GET:
            resp = requests.get(**params)
        else:
            raise ValueError(f"Invalid method: {method}")
        time_spent = t0 - time.time()
        resp.raise_for_status()
        logger.debug(f"{method} {url} complete - status code {resp.status_code} in {time_spent} sec")
        return resp
    except Exception as e:
        logger.error(traceback.format_exc())
        raise e


def _handle_csv_upload(url: str, column_name: str, data: List[str], params: Dict) -> str:
    with tempfile.TemporaryFile() as fp:
        fp.write(str("\n".join([column_name] + data) + "\n").encode())
        fp.seek(0)
        resp = request_handler(
            method=RequestMethod.POST,
            url=url,
            data=fp,
            params=params
        )
        resp.raise_for_status()
    # download_url = resp.json()
    return resp.json()


def _handle_download(
        download_url: str,
        max_retries: int = 10,
        ms_wait_between_retry: int = 100,
        data_key: str = "data"
) -> Dict:
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
            raise Exception(f"Retry max {max_retries} times to get document from {download_url}")

    json_objects = response.text.strip().split("\n")
    datas = []
    for json_data in json_objects:
        data = json.loads(json_data)
        if data.get(data_key) is None:
            continue
        datas += data.get(data_key)
    return datas
