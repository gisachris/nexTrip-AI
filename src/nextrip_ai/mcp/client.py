"""
MCP Client — connects to the nexTrip MCP server and provides tools to LangGraph.
"""
import asyncio
import logging
import sys
from pathlib import Path
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from nextrip_ai.core.config import settings

logger = logging.getLogger(__name__)


async def get_mcp_tools():
    """Connect to the nexTrip MCP server via stdio and return LangChain-compatible tools."""
    server_script = Path(settings.MCP_SERVER_SCRIPT).resolve()
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_script)],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            return tools


def get_mcp_tools_sync():
    """Synchronous wrapper for get_mcp_tools()."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(get_mcp_tools())
        else:
            return asyncio.run(get_mcp_tools())
    except Exception as e:
        logger.warning(f"Failed to run MCP client async loop: {e}")
        return asyncio.run(get_mcp_tools())
