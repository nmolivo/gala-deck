import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp():
    server_params = StdioServerParameters(
        command="node",
        args=["vapi-doc-coding-mcp/build/index.js"]
    )

    print("Connecting to MCP server...")
    try:
        async with stdio_client(server_params) as (read, write):
            print("Connection established!")

            print("Initializing session...")
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("Session initialized!")

                print("Listing tools...")
                tools = await session.list_tools()
                print(f"Found {len(tools.tools)} tools:")
                for tool in tools.tools:
                    print(f"  - {tool.name}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_mcp())
