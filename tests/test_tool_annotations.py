from pixalate_open_mcp.models.tools import PixalateTool


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
