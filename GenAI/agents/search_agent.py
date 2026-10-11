



import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the path to the parent directory (one level up)
parent_dir = os.path.dirname(current_dir)
# Add the parent directory to the system path
sys.path.append(parent_dir)



import asyncio
import os
from pyexpat import model

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from prompts.search_agent_prompt import SEARCH_SYSTEM_PROMPT
from tools.mcp_servers.kapruka_mcp import McpClient
from states.search_structure import ProductSearchResponse

load_dotenv()

tools =  asyncio.run(McpClient())

async def main(query: str):
    

    allowed_tools = {
    "kapruka_search_products"

}

    filtered_tools = [
        tool for tool in tools
        if tool.name in allowed_tools
    ]

    print("Available MCP tools:")
    for tool in filtered_tools:
        print(tool.name, "-", tool.description)

   

    llm = ChatOllama(model="llama3.2")

    llm_with_tools = llm.bind_tools(filtered_tools)

    llm_structured = llm.with_structured_output(ProductSearchResponse)

  

    agent = create_agent(
        model=llm_with_tools,
        tools=filtered_tools,
        system_prompt=(
            SEARCH_SYSTEM_PROMPT
        ),
        response_format= ProductSearchResponse,
    )

    # Run the agent
    result = await agent.ainvoke({
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ]
    })

    raw_answer = result['messages'][-1].content

    structured_final_output = llm_structured.invoke(
    f"Format the following answer into the requested schema: RAW_ANSWER: {raw_answer}"
)
    print(structured_final_output)

    """ structured_result = result.get("structured_response")

    if structured_result:
        print(structured_result.model_dump_json(indent=2))
    else:
        print("Structured response was not returned.")

        # Debug the agent's messages and tool calls
        for message in result["messages"]:
            print("\nMessage type:", type(message).__name__)
            print("Content:", message.content)

            if getattr(message, "tool_calls", None):
                print("Tool calls:", message.tool_calls) """


if __name__ == "__main__":
    query = "Smartwatches available in stock ?"
    asyncio.run(main(query))
