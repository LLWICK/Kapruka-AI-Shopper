"""
Search agent — full implementation.

Scoped tools: kapruka_search_products, kapruka_get_product,
              kapruka_list_categories, kapruka_render_options_card

Responsibilities beyond "call the right tool":
1. Populate state["last_search_results"] with product_ids so cart_node
   can resolve "add the second one" later.
2. Decide WHEN to call render_options_card (2+ products) vs. answer in
   text (1 product, or a category listing).
3. Assign non-reused ref numbers using state["ref_counter"].
4. Handle Kapruka's own edge cases: zero results, category stubs
   (CATSYM, price=0) leaking into results, pagination capped at 3 pages.
"""

from __future__ import annotations

import json
from typing import Literal

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.prebuilt import ToolNode

from kapruka_agent_state import AgentState





def build_search_agent(tools: list, model: str = "llama-3.3-70b-versatile"):
    llm = ChatGroq(model=model, temperature=0.2).bind_tools(tools)
    tool_node = ToolNode(tools)

    async def search_agent_node(state: AgentState) -> dict:
        prompt = SEARCH_SYSTEM_PROMPT.format(
            used_refs=list(range(1, state["ref_counter"] + 1)) or "none",
            currency="LKR",  # swap in a per-user/session currency if you support it
        )
        messages = [SystemMessage(content=prompt)] + state["messages"]
        response: AIMessage = await llm.ainvoke(messages)
        return {"messages": [response]}

    async def search_tools_node(state: AgentState) -> dict:
        """Wraps the prebuilt ToolNode to also update last_search_results and
        ref_counter by inspecting what the LLM actually called, since
        ToolNode itself doesn't know about our AgentState-specific bookkeeping."""

        tool_result = await tool_node.ainvoke(state)
        new_messages = tool_result["messages"]

        last_ai_msg = state["messages"][-1]
        product_ids: list[str] = list(state["last_search_results"])
        ref_counter = state["ref_counter"]

        for tool_call in getattr(last_ai_msg, "tool_calls", []):
            name = tool_call["name"]
            args = tool_call.get("args", {})

            if name == "kapruka_search_products":
                # find the matching ToolMessage to pull product_ids out of its JSON
                for m in new_messages:
                    if isinstance(m, ToolMessage) and m.tool_call_id == tool_call["id"]:
                        try:
                            data = json.loads(m.content)
                            product_ids = [r["id"] for r in data.get("results", [])]
                        except (json.JSONDecodeError, KeyError, TypeError):
                            # tool_call didn't request json format, or search
                            # returned an error string — nothing to extract
                            pass

            if name == "kapruka_render_options_card":
                items = args.get("params", {}).get("items", [])
                if items:
                    ref_counter = max(ref_counter, max(i["ref"] for i in items))

        return {
            "messages": new_messages,
            "last_search_results": product_ids,
            "ref_counter": ref_counter,
        }

    def should_continue(state: AgentState) -> Literal["tools", "supervisor"]:
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            return "tools"
        return "supervisor"

    return search_agent_node, search_tools_node, should_continue