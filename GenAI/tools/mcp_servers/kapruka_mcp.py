
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient



async def McpClient():
    # Connect to an external MCP server
    mcp_client = MultiServerMCPClient({
        "external_service": {
            "transport": "http",
            "url": "https://mcp.kapruka.com/mcp",
            
        }
    })

    # Discover and load the tools
    tools = await mcp_client.get_tools()

    return tools;



