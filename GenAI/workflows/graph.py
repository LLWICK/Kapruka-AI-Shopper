import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient  
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-120b")

async def main():
    client = MultiServerMCPClient(
        {
      "kapruka": {
    "transport": "http",
      "url": "https://mcp.kapruka.com/mcp"
    
  }

        }
    )

    tools = await client.get_tools()
    agent = create_agent(
        model = llm,
        tools = tools
    )
    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "what are the available product categories on Kapruka?"}]}
    )

    print(response['messages'][-1].content)


if __name__ == "__main__":
    asyncio.run(main())