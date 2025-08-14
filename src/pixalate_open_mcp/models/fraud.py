from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self


class FraudRequest(BaseModel):
    _AT_LEAST_ONE_REQUIRED_MSG = "At least one of ip, deviceId, or userAgent must be provided."

    ip: str = Field(default=None, description="The internet protocol address.")
    deviceId: str = Field(
        default=None,
        description="""An ID that characterizes a mobile device. Various types are acceptable, including but not limited to the following:
ADID (Android): Google advertising ID, 36 characters (e.g., FF67345D-BF11-7823-1111-FFED421776FC)
IDFA (iOS): Apple advertising ID, 36 characters (e.g., A217D9FC-C1BE-4BEF-94CD-1EE82147C1AA)
IDFV (iOS): Apple's Identifier for Vendor, 36 characters (e.g., B927E7D7-63A7-4D7D-BF11-34D62A6C6E0B)
MD5 (Multiple): The MD5 hash of a hardware device identifier (e.g., MAC address, IMEI, or advertising ID), 32 characters (e.g., d9527b5207097c5770ca448322489426)
SHA1 (Multiple): The SHA-1 hash of a hardware device identifier (e.g., MAC address, IMEI, or advertising ID), 40 characters (e.g., 2971074629cc8f33146c5eb08b39f157da5ce356)
WAID (Windows): Windows advertising ID, 36 characters (e.g., 97615775-57b5-4300-90b4-ba0c22b60e34)
RIDA (Roku OS): Roku's privacy-friendly device ID, 36 characters (e.g., 331319d2-4cc2-51ac-de21-aa62f1e143c1)
MSAI (Xbox): Advertising ID for Microsoft's Xbox, 36 characters (e.g., bc23c3de-5d32-4d0c-de3a-94ce878a0379)
GAID (Android): Google's Advertising ID, 36 characters (e.g., AE63F1D9-0F3A-4B7A-891D-5E23F12C9B1A)""",
    )
    userAgent: str = Field(default=None, description="The browser or device supplied agent string.")

    @model_validator(mode="after")
    def check_ip_or_device_id_or_user_agent(self) -> Self:
        if self.ip is None and self.deviceId is None and self.userAgent is None:
            raise ValueError(self._AT_LEAST_ONE_REQUIRED_MSG)
        return self

    def to_params(self):
        return {k: getattr(self, k) for k in ["ip", "deviceId", "userAgent"] if getattr(self, k)}


class FraudResponse(BaseModel):
    probability: float = Field(description="The probability of fraud (0.1 through 1.0). 0.0 indicates unknown.")
