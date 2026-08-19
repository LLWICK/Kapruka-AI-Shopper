from langchain_mcp_adapters.client import MultiServerMCPClient  

from dotenv import load_dotenv
load_dotenv()


client = MultiServerMCPClient(
        {
      "kapruka": {
    "transport": "http",
      "url": "https://mcp.kapruka.com/mcp"
    
  }

        }
    )

kapruka_tools = client.get_tools()









