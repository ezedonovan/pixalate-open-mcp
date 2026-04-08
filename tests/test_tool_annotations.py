"""Tests for MCP tool annotation fields and registration."""

from unittest.mock import MagicMock

from mcp.types import ToolAnnotations

from pixalate_open_mcp.models.tools import PixalateTool
from pixalate_open_mcp.server.app import register_tools


def dummy_handler() -> dict:
    return {}


def test_pixalate_tool_has_annotation_defaults():
    tool = PixalateTool(
        title="Test",
        description="A test tool.",
        handler=dummy_handler,
    )
    assert tool.read_only_hint is True
    assert tool.destructive_hint is False
    assert tool.open_world_hint is True


def test_pixalate_tool_annotation_override():
    tool = PixalateTool(
        title="Version",
        description="Get version.",
        handler=dummy_handler,
        open_world_hint=False,
    )
    assert tool.open_world_hint is False
    assert tool.read_only_hint is True


def test_register_tools_passes_annotations():
    mock_server = MagicMock()
    register_tools(mock_server)

    for call in mock_server.add_tool.call_args_list:
        kwargs = call[1]
        assert "annotations" in kwargs, f"Tool '{kwargs.get('title')}' missing annotations"
        ann = kwargs["annotations"]
        assert isinstance(ann, ToolAnnotations)
        assert ann.readOnlyHint is True
        assert ann.destructiveHint is False


def test_version_tool_not_open_world():
    mock_server = MagicMock()
    register_tools(mock_server)

    version_call = [c for c in mock_server.add_tool.call_args_list if "Version" in c[1].get("title", "")]
    assert len(version_call) == 1
    ann = version_call[0][1]["annotations"]
    assert ann.openWorldHint is False
