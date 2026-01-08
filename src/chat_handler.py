"""Chat handler for managing conversations with Claude"""
from .errors import APICreditsError, APIAuthError, APIRateLimitError, MCPConnectionError
from .mcp_client import MCPClient
from .config import MODEL_NAME, MAX_TOKENS
import asyncio
import traceback
from typing import List, Dict, Any
from anthropic import Anthropic, BadRequestError, AuthenticationError, RateLimitError
import logging

logger = logging.getLogger(__name__)


class ChatHandler:
    """Handles chat interactions using MCP tools"""

    def __init__(self, anthropic_client: Anthropic):
        self.client = anthropic_client

    async def _process_message(self, messages: List[Dict[str, Any]]) -> tuple[str, Dict[str, Any]]:
        """Process a message with tool support"""
        total_usage = self._initialize_usage()
        mcp_client = MCPClient()
        stdio_conn = mcp_client.get_tools_and_session()

        async with stdio_conn as (read, write):
            session, tools = await mcp_client.initialize_session(read, write)
            response = await self._call_claude_api(messages, tools, total_usage)

            while response.stop_reason == "tool_use":
                tool_results = await self._handle_tool_calls(response, mcp_client, session)
                messages.extend(tool_results)
                response = await self._call_claude_api(messages, tools, total_usage)

            return self._extract_final_response(response), total_usage

    async def _call_claude_api(self, messages, tools, total_usage):
        """Call the Claude API and track usage."""
        try:
            response = self.client.messages.create(
                model=MODEL_NAME,
                max_tokens=MAX_TOKENS,
                tools=tools,
                messages=messages
            )
            self._track_usage(response, total_usage)
            return response
        except BadRequestError as e:
            self._handle_api_errors(e)

    async def _handle_tool_calls(self, response, mcp_client, session):
        """Process tool calls and return results."""
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result_str = await mcp_client.call_tool(session, block.name, block.input)
                tool_results.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str
                    }]
                })
        return tool_results

    def _initialize_usage(self):
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
        }

    def _track_usage(self, response, total_usage):
        if hasattr(response, 'usage'):
            total_usage["input_tokens"] += response.usage.input_tokens
            total_usage["output_tokens"] += response.usage.output_tokens
            total_usage["cache_creation_input_tokens"] += getattr(
                response.usage, 'cache_creation_input_tokens', 0)
            total_usage["cache_read_input_tokens"] += getattr(
                response.usage, 'cache_read_input_tokens', 0)

    def _extract_final_response(self, response):
        return "".join(block.text for block in response.content if hasattr(block, "text"))

    def _handle_api_errors(self, error):
        if "credit balance" in str(error).lower():
            raise APICreditsError()
        raise Exception(f"❌ **API Error**\n\n{str(error)}")

    def chat(self, messages: List[Dict[str, Any]]) -> tuple[str, Dict[str, Any]]:
        """Synchronous wrapper for chat processing"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._process_message(messages))
        except MCPConnectionError as e:
            logger.error(f"MCP Connection Error: {str(e)}")
            return f"🔧 **MCP Connection Failed**\n\n{str(e)}", {}
        except (APICreditsError, APIAuthError, APIRateLimitError) as e:
            logger.error(f"API Error: {str(e)}")
            return str(e), {}
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return f"❌ **Unexpected Error**\n\n{str(e)}", {}
        finally:
            loop.close()
