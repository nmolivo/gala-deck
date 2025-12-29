"""Configuration and constants"""
import os
from typing import Dict

# Model configuration
MODEL_NAME = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096

# MCP Server configuration
MCP_SERVER_COMMAND = "node"
MCP_SERVER_PATH = os.path.abspath("vapi-doc-coding-mcp/build/index.js")

# UI configuration
APP_TITLE = "💬 Gala Deck Chat"
CHAT_PLACEHOLDER = "Ask about Vedic Astro API..."
PRICING = {
    "claude-sonnet-4-20250514": {
        "input": 3.00,   # $3 per million input tokens
        "output": 15.00,  # $15 per million output tokens
        "cache_write": 3.75,  # $3.75 per million tokens
        "cache_read": 0.30,   # $0.30 per million tokens
    }
}


def calculate_cost(usage: Dict[str, int], model: str = MODEL_NAME) -> float:
    """Calculate approximate cost in USD"""
    if model not in PRICING:
        return 0.0

    prices = PRICING[model]

    input_cost = (usage.get("input_tokens", 0) / 1_000_000) * prices["input"]
    output_cost = (usage.get("output_tokens", 0) /
                   1_000_000) * prices["output"]
    cache_write_cost = (usage.get("cache_creation_input_tokens",
                        0) / 1_000_000) * prices["cache_write"]
    cache_read_cost = (usage.get("cache_read_input_tokens",
                       0) / 1_000_000) * prices["cache_read"]

    return input_cost + output_cost + cache_write_cost + cache_read_cost
