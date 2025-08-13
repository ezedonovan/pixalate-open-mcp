from pydantic import BaseModel, Field


class DatabaseMetadata(BaseModel):
    lastUpdated: str = Field(description="The date when the database was last updated. The date format is YYYY-MM-DD.")


class QuotaMetadata(BaseModel):
    available: int = Field(description="The amount of quota available for use.")
    used: int = Field(description="The amount of quota used.")
    expiry: str = Field(
        description="The datetime when the quota will be refreshed back to the limit. The datetime format is YYYY-MM-DDTHH:MM:SS.SSSZ."
    )
    limit: int = Field(description="The amount of quota to be made available for use when the quota is refreshed.")
    interval: int = Field(description="The number of time units used in calculating the quota refresh datetime.")
    timeUnit: str = Field(description="The time unit used in calculating the quota refresh datetime.")


class Metadata(BaseModel):
    database: DatabaseMetadata = Field(description="The database state information.")
    quota: QuotaMetadata = Field(description="The quota state information.")
