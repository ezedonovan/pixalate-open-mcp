from typing import Literal

from pydantic import BaseModel, Field

MOBILE_WIDGETS = [
    "appOverview",
    "appDetails",
    "pixalateAdvisories",
    "appAdvisories",
    "riskOverview",
    "developerOverview",
    "trafficOverview",
    "brandSafety",
    "appPermissions",
    "trafficOverlap",
    "authorizedSellers",
    "invalidTraffic",
    "viewability",
    "inventory",
    "ctr",
    "availableCountries",
    "rankings",
    "rankingsByCountry",
    "coppa",
]


class EnrichmentMobileRequest(BaseModel):
    appIds: list[str] = Field(
        description="List of one or many mobile app's unique identifier. This is a package name on Google Play or a track id on Apple app Store."
    )
    device: Literal["GLOBAL", "smartphone", "tablet"] = Field(
        default="GLOBAL",
        description="Filter by device. All devices are returned by default. GLOBAL indicates aggregated traffic from all devices.",
    )
    region: Literal["GLOBAL", "NA", "EMEA", "LATAM", "APAC"] = Field(
        default="GLOBAL",
        description="Filter by region. All regions are returned by default. GLOBAL indicates aggregated traffic from all regions.",
    )
    widget: list[Literal[tuple(MOBILE_WIDGETS)]] = Field(
        default=MOBILE_WIDGETS, description="Filter by widgets to return. All widgets are returned by default."
    )

    def to_params(self):
        return {
            "device": self.device,
            "region": self.region,
            "widget": self.widget,
        }


class EnrichmentDomainRequest(BaseModel):
    adDomain: list[str] = Field(description="List of one or many domains.")
    device: Literal["GLOBAL", "desktop", "mobile"] = Field(
        default="GLOBAL", description="Filter by device. All devices are returned by default."
    )
    region: Literal["GLOBAL", "US", "NON-US"] = Field(
        default="GLOBAL",
        description="Filter by region. All regions are returned by default. GLOBAL indicates aggregated traffic from all regions.",
    )

    def to_params(self):
        return {
            "device": self.device,
            "region": self.region,
        }


class EnrichmentCTVRequest(BaseModel):
    appIds: list[str] = Field(description="List of one or many CTV app IDs.")
    device: Literal["roku", "firetv", "tvos", "samsung"] = Field(
        description="Filter by device. All devices are returned by default."
    )
    region: Literal["GLOBAL", "NA", "EMEA", "LATAM", "APAC"] = Field(
        default="GLOBAL",
        description="Filter by region. All regions are returned by default. GLOBAL indicates aggregated traffic from all regions.",
    )
    includeSpoofing: bool = Field(
        default=True, description="A true indicates that spoofing information should be included."
    )

    def to_params(self):
        return {
            "device": self.device,
            "region": self.region,
            "includeSpoofing": self.includeSpoofing,
        }
