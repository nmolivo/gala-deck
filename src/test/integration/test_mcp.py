import pytest
import asyncio
import subprocess
from src.mcp_client import MCPClient


@pytest.fixture(scope="module", autouse=True)
def start_mcp_server():
    """Start the MCP server before running the test."""
    process = subprocess.Popen(
        ["node", "vapi-doc-coding-mcp/build/index.js"],
        cwd="/Users/nmolivo/Documents/Repos/gala-deck",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    yield
    process.terminate()  # Ensure the server is terminated after the test


@pytest.mark.asyncio
async def test_mcp_client():
    """Integration test for MCPClient"""
    client = MCPClient()
    async with client.get_tools_and_session() as (read, write):
        session, tools = await client.initialize_session(read, write)

        # Validate the session and tools
        assert session is not None, "Session should not be None"
        assert isinstance(tools, list), "Tools should be a list"
        assert len(tools) > 0, "Tools list should not be empty"
