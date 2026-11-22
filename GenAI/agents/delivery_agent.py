



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
import asyncio
load_dotenv()

from functools import lru_cache

_tools = None

def get_tools():
    global _tools

    if _tools is None:
        _tools = McpClient()

    return _tools


    

async def tool_check():
    tools = await get_tools()
    allowed_tools = {
        "kapruka_list_delivery_cities",
        "kapruka_check_delivery",
        "kapruka_create_order",
        "kapruka_list_categories",
        "kapruka_gift_countries",
        "kapruka_gift_country_products",
        "kapruka_track_order"


    }

    filtered_tools = [
            tool for tool in tools
            if tool.name in allowed_tools
        ]

    print("Available MCP tools:")
    for tool in filtered_tools:
        print(tool.name, "-", tool.description) 

async def delivery_agent(state: AgentState)-> AgentState:

    logger = get_logger("Delivery Agent")

    logger.info("Executing Delivery Agent.......")

    query = state['query']

    products = state.get("last_search_results", [])

    selected_product_id = state.get("selected_product_id")

    
    

    selected_product = next(
        (
            product for product in products
            if str(product.get("id")) == str(selected_product_id)
        ),
        None
    )



    

    if not selected_product:
        return {
            "response": {
                "message": (
                    "Please select a product first, "
                    "so I can retrieve the delivery information."
                ),
                "agent": "delivery_agent"
            }
        }

    # Use the selected product's actual ID.
    product_id = selected_product["id"]


    

    tools = await get_tools()
    

    allowed_tools = {
    "kapruka_get_product"

}

    filtered_tools = [
        tool for tool in tools
        if tool.name in allowed_tools
    ]


   

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
                "content": f"USER QUERY - {query}  SELECTED PRODUCT ID - {product_id}",
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


results = asyncio.run(tool_check())



