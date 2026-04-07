import asyncio
import sys
from typing import Optional

import click
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from pixalate_open_mcp.__version__ import __version__
from pixalate_open_mcp.models.config import ServerConfig, load_config
from pixalate_open_mcp.tools.analytics.tools import toolset as analytics_toolset
from pixalate_open_mcp.tools.enrichment.tools import toolset as enrichment_toolset
from pixalate_open_mcp.tools.fraud.tools import toolset as fraud_toolset
from pixalate_open_mcp.utils.logging_config import logger, setup_logging


def create_mcp_server(config: Optional[ServerConfig] = None) -> FastMCP:
    """Create and configure the MCP server with all toolsets registered.

    Args:
        config: Optional server configuration. If not provided, configuration is
                loaded from environment variables via ``load_config()``.

    Returns:
        A fully configured :class:`FastMCP` server instance.
    """
    if config is None:
        config = load_config()
    setup_logging(config)
    server = FastMCP(config.name)
    register_tools(server)
    return server


def register_tools(mcp_server: FastMCP) -> None:
    """Register all Pixalate toolsets and the version tool with the MCP server.

    Iterates over the enrichment, fraud, and analytics toolsets and registers
    each tool's handler together with its title, description, and
    :class:`~mcp.types.ToolAnnotations` derived from the tool's hint fields.
    The built-in version tool is registered last with ``openWorldHint=False``
    because it only returns static, locally-known data.

    Args:
        mcp_server: The :class:`FastMCP` server instance to register tools on.
    """
    for toolset in [enrichment_toolset, fraud_toolset, analytics_toolset]:
        toolset_name = toolset.name
        for tool in toolset.tools:
            mcp_server.add_tool(
                fn=tool.handler,
                title=f"{toolset_name} - {tool.title}",
                description=tool.description,
                annotations=ToolAnnotations(
                    readOnlyHint=tool.read_only_hint,
                    destructiveHint=tool.destructive_hint,
                    openWorldHint=tool.open_world_hint,
                ),
            )
    mcp_server.add_tool(
        fn=get_mcp_server_version,
        title="Pixalate Open MCP - Version",
        description="Get the version of the Pixalate Open MCP server",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=False,
        ),
    )


def get_mcp_server_version() -> dict:
    """Return the name and current version of the Pixalate Open MCP server.

    Returns:
        A dictionary with ``name`` and ``version`` keys.
    """
    return {
        "name": "Pixalate Open MCP",
        "version": __version__,
    }


server = create_mcp_server()


@click.command()
@click.option("--port", default=3001, help="Port to listen on for SSE or streamable-http")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse", "streamable-http"]),
    default="stdio",
    help="Transport type (stdio, sse, or streamable-http)",
)
def main(port: int, transport: str) -> int:
    """Start the Pixalate Open MCP server with the chosen transport.

    Args:
        port: TCP port used when ``transport`` is ``sse`` or ``streamable-http``.
        transport: One of ``stdio``, ``sse``, or ``streamable-http``.

    Returns:
        Exit code: ``0`` on success or clean shutdown, ``1`` on error.
    """
    try:
        if transport == "stdio":
            asyncio.run(server.run_stdio_async())
        elif transport == "sse":
            server.settings.port = port
            asyncio.run(server.run_sse_async())
        else:
            server.settings.port = port
            asyncio.run(server.run_streamable_http_async())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
