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
    """Handles chat interactions with Claude using MCP tools"""

    def __init__(self, anthropic_client: Anthropic):
        self.client = anthropic_client
        # DON'T create MCP client here anymore

    async def _process_message(
        self,
        messages: List[Dict[str, Any]],
    ) -> tuple[str, Dict[str, Any]]:
        """Process a message through Claude with tool support"""

        total_usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
        }

        # Create MCP client fresh for this request
        mcp_client = MCPClient()

        # Get MCP connection
        stdio_conn = mcp_client.get_tools_and_session()
        async with stdio_conn as (read, write):
            session, tools = await mcp_client.initialize_session(read, write)

            # Initial API call
            logger.info("Calling Claude API...")
            try:
                response = self.client.messages.create(
                    model=MODEL_NAME,
                    max_tokens=MAX_TOKENS,
                    tools=tools,
                    messages=messages
                )
                logger.info(
                    f"Claude responded with stop_reason: {response.stop_reason}")

                # Track usage from first response
                if hasattr(response, 'usage'):
                    total_usage["input_tokens"] += response.usage.input_tokens
                    total_usage["output_tokens"] += response.usage.output_tokens
                    if hasattr(response.usage, 'cache_creation_input_tokens'):
                        total_usage["cache_creation_input_tokens"] += response.usage.cache_creation_input_tokens or 0
                    if hasattr(response.usage, 'cache_read_input_tokens'):
                        total_usage["cache_read_input_tokens"] += response.usage.cache_read_input_tokens or 0

            except BadRequestError as e:
                if "credit balance" in str(e).lower():
                    raise APICreditsError()
                raise Exception(f"❌ **API Error**\n\n{str(e)}")
            except AuthenticationError:
                raise APIAuthError()
            except RateLimitError:
                raise APIRateLimitError()

            # Handle tool calls in a loop
            while response.stop_reason == "tool_use":
                logger.info(
                    f"Tool use detected, stop_reason: {response.stop_reason}")
                assistant_content = response.content

                # Process tool calls
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        logger.info(f"Calling tool: {block.name}")
                        result_str = await mcp_client.call_tool(
                            session,
                            block.name,
                            block.input
                        )
                        logger.info(
                            f"Tool result received: {result_str[:100]}")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_str
                        })

                logger.info(
                    f"Sending {len(tool_results)} tool results back to Claude")

                # Continue conversation with tool results
                messages.append({
                    "role": "assistant",
                    "content": assistant_content
                })
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

                # Get next response
                try:
                    response = self.client.messages.create(
                        model=MODEL_NAME,
                        max_tokens=MAX_TOKENS,
                        tools=tools,
                        messages=messages
                    )

                    # Track usage from follow-up responses
                    if hasattr(response, 'usage'):
                        total_usage["input_tokens"] += response.usage.input_tokens
                        total_usage["output_tokens"] += response.usage.output_tokens
                        if hasattr(response.usage, 'cache_creation_input_tokens'):
                            total_usage["cache_creation_input_tokens"] += response.usage.cache_creation_input_tokens or 0
                        if hasattr(response.usage, 'cache_read_input_tokens'):
                            total_usage["cache_read_input_tokens"] += response.usage.cache_read_input_tokens or 0

                except BadRequestError as e:
                    if "credit balance" in str(e).lower():
                        raise APICreditsError()
                    raise Exception(f"❌ **API Error**\n\n{str(e)}")

            # Extract final text response
            text_response = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text_response += block.text

            return text_response, total_usage

    def chat(self, messages: List[Dict[str, Any]]) -> tuple[str, Dict[str, Any]]:
        """Synchronous wrapper for chat processing"""

        # Create new event loop for this call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._process_message(messages))
        except MCPConnectionError as e:
            logger.error(f"MCP Connection Error: {str(e)}")
            logger.error(traceback.format_exc())
            return f"🔧 **MCP Connection Failed**\n\n{str(e)}\n\nMake sure the MCP server is built and the path is correct.", {}
        except (APICreditsError, APIAuthError, APIRateLimitError) as e:
            logger.error(f"API Error: {str(e)}")
            logger.error(traceback.format_exc())
            return str(e), {}
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(traceback.format_exc())
            error_str = str(e)
            if error_str.startswith(("💳", "❌", "🔑", "⏱️", "🔧")):
                return error_str, {}
            return f"❌ **Unexpected Error**\n\n{error_str}", {}
        finally:
            loop.close()
