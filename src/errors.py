"""Custom exceptions for better error handling"""


class MCPError(Exception):
    """Base exception for MCP-related errors"""
    pass


class MCPConnectionError(MCPError):
    """MCP server connection failed"""

    def __init__(self, server_path: str, original_error: str):
        self.message = f"""🔧 **MCP Server Connection Failed**

Could not connect to the MCP server. Please check:

1. **Node.js installed**: Run `node --version` in terminal
2. **MCP built**: Run `cd vapi-doc-coding-mcp && npm run build`
3. **Path correct**: Verify the build exists

Current path: `{server_path}`

Error details: {original_error}"""
        super().__init__(self.message)


class APICreditsError(MCPError):
    """Anthropic API credits exhausted"""

    def __init__(self):
        self.message = """💳 **Anthropic API Credits Low**

Your API account needs more credits. Please:
1. Visit https://console.anthropic.com/settings/billing
2. Add credits or upgrade your plan
3. Try again"""
        super().__init__(self.message)


class APIAuthError(MCPError):
    """Anthropic API authentication failed"""

    def __init__(self):
        self.message = """🔑 **Authentication Failed**

Your ANTHROPIC_API_KEY is invalid. Please check `.streamlit/secrets.toml`"""
        super().__init__(self.message)


class APIRateLimitError(MCPError):
    """Anthropic API rate limit exceeded"""

    def __init__(self):
        self.message = """⏱️ **Rate Limit Exceeded**

Too many requests. Please wait a moment and try again."""
        super().__init__(self.message)
