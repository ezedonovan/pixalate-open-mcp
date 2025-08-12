from typing import Callable

from pydantic import BaseModel, Field


class PixalateTool(BaseModel):
    title: str = Field(description="Human readable name of the tool.")
    description: str = Field(description="Description of the tool.")
    handler: Callable = Field(description="Handler function for the tool.")


class PixalateToolset(BaseModel):
    name: str = Field(description="Name of the toolset.")
    tools: list[PixalateTool] = Field(description="List of tools.")
