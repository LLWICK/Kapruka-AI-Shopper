



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
from prompts.detail_agent_prompt import detail_agent_prompt
from tools.mcp_servers.kapruka_mcp import McpClient
from states.product_details_schema import DetailsAgentOutput
from states.agent_state import AgentState
from utills.loggers import get_logger
from langchain_core.messages import AIMessage
load_dotenv()

from functools import lru_cache

_tools = None

async def get_tools():
    global _tools

    if _tools is None:
        _tools = await McpClient()

    return _tools

async def detail_agent(state: AgentState)-> AgentState:

    logger = get_logger("Detail Agent")

    logger.info("Executing Detail Agent.......")

    query = state['query']

    search_output = state.get("search_agent_output", {})

    if hasattr(search_output, "model_dump"):
        search_output = search_output.model_dump()

    products = search_output.get("products", [])

    

    tools = await get_tools()
    

    allowed_tools = {
    "kapruka_get_product"

}

    filtered_tools = [
        tool for tool in tools
        if tool.name in allowed_tools
    ]

    """ print("Available MCP tools:")
    for tool in filtered_tools:
        print(tool.name, "-", tool.description) """

   

    llm = ChatGroq(model="openai/gpt-oss-120b",
     max_tokens=2000,
     reasoning_effort="low",
    )
    llm_structured = ChatOllama(model="llama3.2").with_structured_output(
        DetailsAgentOutput
    )

    agent = create_agent(
        model=llm,
        tools=filtered_tools,
        system_prompt=detail_agent_prompt,
    )

    result = await agent.ainvoke({
        "messages": [
            {
                "role": "user",
                "content": f"USER QUERY - {query}  PRODUCTS - {products}",
            }
        ],
    })

    raw_answer = result["messages"][-1].content

    structured_final_output = llm_structured.invoke(
    f"Format the following answer into the requested schema. Deeply analyze the RAW_ANSWER to extract the necessary information: RAW_ANSWER: {raw_answer}"
)
    payload = (
        structured_final_output.model_dump()
        if hasattr(structured_final_output, "model_dump")
        else structured_final_output
    )
    message = (
        structured_final_output.message
        if getattr(structured_final_output, "message", None)
        else str(payload)
    )
    return {
        "detail_agent_output": payload,
        "response": payload,
        "messages": [AIMessage(content=message)],
    }


