
import os
import sys

from langgraph.graph import START, END, StateGraph

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from states.agent_state import AgentState
from agents.search_agent import search_agent
from agents.details_agent import detail_agent
from agents.cart_agent import cart_agent
from agents.product_resolver_agent import product_resolver_agent
from agents.supervisor_agent import supervisor_agent


def choose_agent(state: AgentState) -> str:
    intent = state.get("intent")
    cart_action = state.get("cart_action")

    if intent == "details":
        return "product_resolver"

    if intent == "cart":
        if cart_action == "view":
            return "cart"

        if cart_action in {"add", "remove", "update"}:
            return "product_resolver"
        return "cart"


    if intent == "checkout":
        return "checkout"
    
    if intent == "track":
        return "track"

    return "search"


def route_after_product_resolution(state):

    resolution = state.get("product_resolution", {})

    if resolution.get("status") != "resolved":
        return "end"

    if state.get("intent") == "details":
        return "detail_agent"

    if state.get("intent") == "cart":
        return "cart_agent"

    return "end"


def build_workflow():

    checkpoint = MemorySaver()
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("search_agent", search_agent)
    graph_builder.add_node("detail_agent", detail_agent)
    graph_builder.add_node("supervisor_agent", supervisor_agent)
    graph_builder.add_node("cart_agent", cart_agent)
    graph_builder.add_node("product_resolver", product_resolver_agent)

    graph_builder.add_edge(START, "supervisor_agent")

    graph_builder.add_conditional_edges(
    "supervisor_agent",
    choose_agent,
    {
        "search": "search_agent",
        "product_resolver": "product_resolver",
        "details": "detail_agent",
        "cart": "cart_agent"
    }
)

    graph_builder.add_conditional_edges(
    "product_resolver",
    route_after_product_resolution,
    {
        "detail_agent": "detail_agent",
        "cart_agent": "cart_agent",
        "end": END,
    }
)

   
    graph_builder.add_edge("search_agent", END)
    graph_builder.add_edge("detail_agent", END)
    graph_builder.add_edge("cart_agent", END)

    return graph_builder.compile(checkpointer=checkpoint)


builder = build_workflow()


async def run_workflow(query: str, thread_id: str, selected_product_id: str | None = None) -> dict:
    
    initial_state = {"query": query,
     "messages": [HumanMessage(content=query)],
      "selected_product_id": selected_product_id,}

    config = {"configurable": {"thread_id": thread_id}}

    return await builder.ainvoke(initial_state, config=config)


""" if __name__ == "__main__":
    import asyncio

    result = asyncio.run(
        run_workflow(    
            "What are the available birthday cakes under Rs. 7000?"
        )
    )

    print(result.get("searchItems", [])) """
