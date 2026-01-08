"""MCP client wrapper for tool management"""
from datetime import datetime
from .errors import MCPConnectionError
from .config import MCP_SERVER_COMMAND, MCP_SERVER_PATH
import asyncio
import os
import subprocess
from typing import List, Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import StdioServerParameters as StdioParams
from mcp.client.stdio import get_default_environment, stdio_client
from contextlib import asynccontextmanager

import logging
logger = logging.getLogger(__name__)


class MCPClient:
    """Manages MCP server connection and tool retrieval"""

    def __init__(self):
        self.command = MCP_SERVER_COMMAND
        self.args = [MCP_SERVER_PATH]
        self.tool_call_history = []

    @asynccontextmanager
    async def get_tools_and_session(self):
        """Create MCP connection using direct subprocess"""
        params = StdioServerParameters(
            command=self.command,
            args=self.args,
            env=get_default_environment()
        )

        async with stdio_client(params) as (read, write):
            yield read, write

    async def initialize_session(self, read, write):
        """Initialize a session and return tools"""
        try:
            logger.info("Creating ClientSession...")
            session = ClientSession(read, write)

            logger.info("Calling session.initialize()...")
            await asyncio.wait_for(session.initialize(), timeout=10.0)
            logger.info("Session initialized successfully!")

            logger.info("Calling session.list_tools()...")
            tools_result = await asyncio.wait_for(session.list_tools(), timeout=10.0)
            logger.info(f"Got {len(tools_result.tools)} tools")

            logger.info(
                f"Available MCP tools: {[t.name for t in tools_result.tools]}")

            # Convert to Anthropic format
            anthropic_tools = []
            for tool in tools_result.tools:
                anthropic_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })

            logger.info("Returning session and tools")
            return session, anthropic_tools

        except asyncio.TimeoutError:
            logger.error("Timeout during MCP initialization")
            raise MCPConnectionError(
                MCP_SERVER_PATH, "MCP server not responding to initialization")
        except Exception as e:
            logger.error(f"Error initializing MCP session: {e}", exc_info=True)
            raise MCPConnectionError(MCP_SERVER_PATH, str(e))

    async def call_tool(self, session, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool call on the MCP server and return string content"""
        logger.info(f"🔧 Calling tool: {tool_name}")
        logger.info(f"   Arguments: {arguments}")

        try:
            result = await asyncio.wait_for(
                session.call_tool(tool_name, arguments=arguments),
                timeout=30.0
            )

            result_str = str(result.content) if hasattr(
                result, 'content') else str(result)

            call_record = {
                "timestamp": datetime.now().isoformat(),
                "tool": tool_name,
                "arguments": arguments,
                "result": result_str[:500]
            }
            self.tool_call_history.append(call_record)

            logger.info(f"   Result preview: {result_str[:100]}...")

            return result_str

        except asyncio.TimeoutError:
            error_msg = f"Tool call '{tool_name}' timed out after 30 seconds"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"Tool call '{tool_name}' failed: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
