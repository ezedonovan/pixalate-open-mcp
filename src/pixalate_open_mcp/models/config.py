import os

from pydantic import BaseModel


class ServerConfig(BaseModel):
    name: str = "pixalate-open-mcp"
    log_level: str = os.getenv("LOG_LEVEL")
    x_api_key: str = os.getenv("X_API_KEY")


def load_config() -> ServerConfig:
    """Load server configuration from environment variables.

    Reads ``MCP_SERVER_NAME``, ``LOG_LEVEL``, and ``X_API_KEY`` from the
    process environment and returns a populated ``ServerConfig`` instance.

    Returns:
        A ``ServerConfig`` with values sourced from environment variables,
        falling back to ``"pixalate-open-mcp"`` for the server name and
        ``"DEBUG"`` for the log level when those variables are not set.
    """
    return ServerConfig(
        name=os.getenv("MCP_SERVER_NAME", "pixalate-open-mcp"),
        log_level=os.getenv("LOG_LEVEL", "DEBUG"),
        x_api_key=os.getenv("X_API_KEY"),
    )
