from typing import Callable

from pydantic import BaseModel, Field


class PixalateTool(BaseModel):
    """A tool definition for the Pixalate MCP server.

    Attributes:
        title: Human-readable name of the tool.
        description: Description of the tool's functionality and usage.
        handler: Async or sync function that implements the tool.
        read_only_hint: Whether the tool only reads data without side effects.
        destructive_hint: Whether the tool may perform destructive operations.
        open_world_hint: Whether the tool interacts with external services.
    """

    title: str = Field(description="Human readable name of the tool.")
    description: str = Field(description="Description of the tool.")
    handler: Callable = Field(description="Handler function for the tool.")
    read_only_hint: bool = Field(default=True, description="Whether the tool only reads data.")
    destructive_hint: bool = Field(default=False, description="Whether the tool may perform destructive operations.")
    open_world_hint: bool = Field(default=True, description="Whether the tool interacts with external services.")


class PixalateToolset(BaseModel):
    """A named group of related Pixalate tools.

    Attributes:
        name: Name of the toolset (e.g., 'Analytics API').
        tools: List of tools in this toolset.
    """

    name: str = Field(description="Name of the toolset.")
    tools: list[PixalateTool] = Field(description="List of tools.")
