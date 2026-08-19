"""
Connects to Kapruka's MCP server and lists every available tool,
including its name, description, and input schema.

Run with:  python list_kapruka_tools.py
Requires:  pip install mcp
"""
import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

KAPRUKA_MCP_URL = "https://mcp.kapruka.com/mcp"


async def main():
    async with streamablehttp_client(KAPRUKA_MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            print(f"Found {len(tools_result.tools)} tools:\n")

            for tool in tools_result.tools:
                print(f"### {tool.name}")
                print(f"Description: {tool.description}")
                print(f"Input schema: {tool.inputSchema}")
                print()


if __name__ == "__main__":
    asyncio.run(main())