"""nexTrip AI MCP Server Package."""


def __getattr__(name):
    """Lazy-load server and client submodules to avoid import-time crashes
    when optional dependencies (e.g. langchain-mcp-adapters) are missing or
    have version conflicts."""
    if name == "server":
        from nextrip_ai.mcp import server
        return server
    if name == "client":
        from nextrip_ai.mcp import client
        return client
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["server", "client"]
