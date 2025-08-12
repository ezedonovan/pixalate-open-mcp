import asyncio
import sys
from typing import Optional

import click
from mcp.server.fastmcp import FastMCP

from pixalate_open_mcp.models.config import ServerConfig, load_config
from pixalate_open_mcp.utils.logging_config import logger, setup_logging
from pixalate_open_mcp.tools.enrichment.tools import toolset as enrichment_toolset


def create_mcp_server(config: Optional[ServerConfig] = None) -> FastMCP:
    if config is None:
        config = load_config()
    setup_logging(config)
    server = FastMCP(config.name)
    register_tools(server)
    return server


def register_tools(mcp_server: FastMCP) -> None:
    for toolset in [
        enrichment_toolset
    ]:
        for tool in toolset.tools:
            mcp_server.add_tool(
                fn=tool.handler,
                title=tool.title,
                description=tool.description
            )


server = create_mcp_server()


@click.command()
@click.option("--port", default=3001, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type (stdio or sse)",
)
def main(port: int, transport: str) -> int:
    try:
        if transport == "stdio":
            asyncio.run(server.run_stdio_async())
        else:
            server.settings.port = port
            asyncio.run(server.run_sse_async())
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
