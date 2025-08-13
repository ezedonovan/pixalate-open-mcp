import os

from pydantic import BaseModel


class ServerConfig(BaseModel):
    name: str = "pixalate-open-mcp"
    log_level: str = os.getenv("LOG_LEVEL")
    x_api_key: str = os.getenv("X_API_KEY")


def load_config() -> ServerConfig:
    return ServerConfig(
        name=os.getenv("MCP_SERVER_NAME", "pixalate-open-mcp"),
        log_level=os.getenv("LOG_LEVEL", "DEBUG"),
        x_api_key=os.getenv("X_API_KEY"),
    )
