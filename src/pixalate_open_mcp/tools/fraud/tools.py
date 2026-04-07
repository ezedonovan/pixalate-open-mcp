import os
from urllib.parse import urlencode

import requests

from pixalate_open_mcp.models.fraud import FraudRequest, FraudResponse
from pixalate_open_mcp.models.metadata import Metadata
from pixalate_open_mcp.models.tools import PixalateTool, PixalateToolset
from pixalate_open_mcp.utils.logging_config import logger
from pixalate_open_mcp.utils.request import RequestMethod, request_handler

BASE_URL = "https://fraud-api.pixalate.com/api/v2/"


def get_fraud_metadata(pretty: bool = False) -> dict | Metadata:
    """Retrieve metadata information for the Pixalate Fraud API.

    Fetches the current user's quota state and the date the fraud database
    was last updated.

    Args:
        pretty: Whether to return pretty-printed JSON. Defaults to False.

    Returns:
        A dict containing quota and database metadata, or a Metadata object.
        On error, returns a dict with an "error" key describing the failure.
    """
    try:
        resp = request_handler(
            method=RequestMethod.GET, url=os.path.join(BASE_URL, "fraud") + "?" + urlencode({"pretty": pretty}).lower()
        )
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        logger.error("HTTP error fetching fraud metadata: %s", e)
        return {"error": f"API request failed with status {e.response.status_code}", "details": str(e)}
    except requests.ConnectionError as e:
        logger.error("Connection error fetching fraud metadata: %s", e)
        return {"error": "Unable to connect to Pixalate API. Check your network connection."}
    except requests.Timeout as e:
        logger.error("Timeout fetching fraud metadata: %s", e)
        return {"error": "Request to Pixalate API timed out. Please try again."}
    except Exception as e:
        logger.error("Unexpected error fetching fraud metadata: %s", e)
        return {"error": f"Unexpected error: {e!s}"}


def get_fraud(request: FraudRequest) -> dict | FraudResponse:
    """Retrieve fraud probability for a specific IP, Device, or Agent.

    Returns a probability (risk score) from 0.01 to 1.0 representing the
    likelihood a given value is related to malicious or compromised devices,
    calculated by Pixalate's proprietary machine-learning algorithm.

    Args:
        request: A FraudRequest containing one or more of ip, device, or agent
            parameters to assess for fraud risk.

    Returns:
        A dict or FraudResponse containing the fraud probability score.
        On error, returns a dict with an "error" key describing the failure.
    """
    try:
        resp = request_handler(
            method=RequestMethod.GET, url=os.path.join(BASE_URL, "fraud"), params=request.to_params()
        )
        return resp.json()
    except requests.HTTPError as e:
        logger.error("HTTP error fetching fraud data: %s", e)
        return {"error": f"API request failed with status {e.response.status_code}", "details": str(e)}
    except requests.ConnectionError as e:
        logger.error("Connection error fetching fraud data: %s", e)
        return {"error": "Unable to connect to Pixalate API. Check your network connection."}
    except requests.Timeout as e:
        logger.error("Timeout fetching fraud data: %s", e)
        return {"error": "Request to Pixalate API timed out. Please try again."}
    except Exception as e:
        logger.error("Unexpected error fetching fraud data: %s", e)
        return {"error": f"Unexpected error: {e!s}"}


toolset = PixalateToolset(
    name="Fraud API",
    tools=[
        PixalateTool(
            title="Metadata",
            description="""The purpose of this API is to provide metadata information for Fraud API in general. The response is a JSON formatted object containing the current user's quota state and the date the fraud database was last updated.""",
            handler=get_fraud_metadata,
        ),
        PixalateTool(
            title="Fraud",
            description="""Retrieve probability of fraud for a specific IP, Device, or Agent. The Fraud Blocking API returns a probability (risk score) 0.01 to 1.0 representing the likelihood a given value is related to malicious or compromised devices. This risk scoring is calculated by Pixalate's proprietary machine-learning algorithm and allows clients to set their own blocking thresholds based on the quality and scale of their supply inventory. The following is a general guideline for setting fraud blocking thresholds:

Probability equal to 1.0, for filtering out only the worst offender for blocking (deterministic).
Probability is greater than or equal to 0.90 for filtering out users that are fraudulent beyond a reasonable doubt.
Probability between 0.75 (inclusive) and 0.90 (exclusive) to filter out users associated with clear and convincing evidence that they are fraudulent.
Probability between 0.5 (inclusive) and 0.75 (exclusive) to filter out users that it is more likely than not that they are fraudulent (also known as preponderance of the evidence standard).
Pixalate does not recommend blocking any probabilities less than 0.5. When making adjustments to the probability threshold, Pixalate highly recommends regular checks and balances against impression delivery as lowering the probabilistic threshold can potentially impact the impression count.

Zero or more of the following parameters may be provided. If more than one parameter is specified, the probability returned is determined by assessing risk based on the combination of each parameter's individual risk probability.

Not specifying an IP, Device, or Agent will return the metadata for fraud, including the user's current quota. See alternate response schema below.""",
            handler=get_fraud,
        ),
    ],
)
