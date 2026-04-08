"""Tests for MCP server initialization and transport configuration."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from pixalate_open_mcp.models.config import ServerConfig
from pixalate_open_mcp.server.app import (
    create_mcp_server,
    get_mcp_server_version,
    main,
    register_tools,
)


def test_create_mcp_server_default_config():
    """create_mcp_server() with no args returns a FastMCP instance with a name."""
    server = create_mcp_server()
    assert hasattr(server, "name")


def test_create_mcp_server_custom_config():
    """create_mcp_server() with a custom ServerConfig uses the config's name."""
    config = ServerConfig(name="test-server", log_level="INFO", x_api_key="key")
    server = create_mcp_server(config=config)
    assert server.name == "test-server"


def test_register_tools_registers_all_tools():
    """register_tools() calls add_tool exactly 11 times (10 domain tools + version)."""
    mock_server = MagicMock()
    register_tools(mock_server)
    assert mock_server.add_tool.call_count == 11


def test_register_tools_titles_prefixed():
    """All registered tool titles contain ' - ' as a separator."""
    mock_server = MagicMock()
    register_tools(mock_server)
    titles = [call.kwargs["title"] for call in mock_server.add_tool.call_args_list]
    for title in titles:
        assert " - " in title, f"Title missing ' - ' separator: {title!r}"


def test_register_tools_version_title():
    """The version tool is registered with title 'Pixalate Open MCP - Version'."""
    mock_server = MagicMock()
    register_tools(mock_server)
    titles = [call.kwargs["title"] for call in mock_server.add_tool.call_args_list]
    assert "Pixalate Open MCP - Version" in titles


def test_get_mcp_server_version():
    """get_mcp_server_version() returns name 'Pixalate Open MCP' and a version key."""
    result = get_mcp_server_version()
    assert result["name"] == "Pixalate Open MCP"
    assert "version" in result


def test_main_stdio_transport():
    """main --transport stdio exits with code 0."""
    with patch("pixalate_open_mcp.server.app.asyncio.run"):
        result = CliRunner().invoke(main, ["--transport", "stdio"])
    assert result.exit_code == 0


def test_main_sse_transport():
    """main --transport sse --port 8080 exits with code 0."""
    with patch("pixalate_open_mcp.server.app.asyncio.run"):
        result = CliRunner().invoke(main, ["--transport", "sse", "--port", "8080"])
    assert result.exit_code == 0


def test_main_streamable_http_transport():
    """main --transport streamable-http exits with code 0."""
    with patch("pixalate_open_mcp.server.app.asyncio.run"):
        result = CliRunner().invoke(main, ["--transport", "streamable-http"])
    assert result.exit_code == 0


def test_main_keyboard_interrupt_returns_zero():
    """KeyboardInterrupt during server run results in exit code 0."""
    with patch("pixalate_open_mcp.server.app.asyncio.run", side_effect=KeyboardInterrupt):
        result = CliRunner().invoke(main, ["--transport", "stdio"])
    assert result.exit_code == 0


def test_main_exception_logs_error():
    """An unexpected exception during server run is caught and logged; CLI exits cleanly."""
    with patch("pixalate_open_mcp.server.app.asyncio.run", side_effect=Exception("fail")):
        result = CliRunner().invoke(main, ["--transport", "stdio"])
    # Click @command does not propagate the integer return value as exit code;
    # the exception is caught and logged inside main(), so the CLI itself exits 0.
    assert result.exit_code == 0
    assert result.exception is None
