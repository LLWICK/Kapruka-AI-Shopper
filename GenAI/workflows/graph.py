
import os
import sys

from langgraph.graph import START, END, StateGraph

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from states.agent_state import AgentState
from agents.search_agent import search_agent


def build_workflow():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("search_agent", search_agent)

    graph_builder.add_edge(START, "search_agent")
    graph_builder.add_edge("search_agent", END)

    return graph_builder.compile()


builder = build_workflow()


async def run_workflow(query: str) -> dict:
    state = {"query": query}
    return await builder.ainvoke(state)


""" if __name__ == "__main__":
    import asyncio

    result = asyncio.run(
        run_workflow(
            "What are the available birthday cakes under Rs. 7000?"
        )
    )

    print(result.get("searchItems", [])) """
