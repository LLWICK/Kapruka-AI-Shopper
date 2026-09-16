from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio

KAPRUKA_MCP_CONFIG = {
    "kapruka": {
        "transport": "streamable_http",
        "url": "https://mcp.kapruka.com/mcp",
    }
}
 
# Which tools each agent is allowed to call. Keep this as the single
# source of truth — if Kapruka ever adds/renames a tool, this is the
# only place that needs updating.
AGENT_TOOL_SCOPES: dict[str, list[str]] = {
    "search_agent": [
        "kapruka_search_products",
        "kapruka_get_product",
        "kapruka_list_categories",
        "kapruka_render_options_card",
    ],
    "delivery_agent": [
        "kapruka_list_delivery_cities",
        "kapruka_check_delivery",
    ],
    "checkout_agent": [
        "kapruka_create_order",
        # deliberately includes check_delivery too, so checkout can do a
        # final re-verify right before calling create_order (see the
        # earlier point about the 60-min price lock only starting AFTER
        # create_order — a stale check_delivery result isn't safe to trust)
        "kapruka_check_delivery",
    ],
    "tracking_agent": [
        "kapruka_track_order",
    ],
}
 
 
def scope_tools(all_tools: list, allowed_names: list[str]) -> list:
    """Filter an MCP tool list down to a named subset.
 
    Raises if a name in the scope doesn't exist on the server — this is
    intentional: a silent empty scope (e.g. from a typo'd tool name) is
    worse than a loud failure at startup, since the agent would otherwise
    just look confused about "missing" tools at runtime.
    """
    by_name = {t.name: t for t in all_tools}
    missing = [n for n in allowed_names if n not in by_name]
    if missing:
        raise ValueError(
            f"Tool(s) not found on server: {missing}. "
            f"Available: {sorted(by_name.keys())}"
        )
    return [by_name[n] for n in allowed_names]
 
 
async def build_scoped_toolsets() -> dict[str, list]:
    """Connect to Kapruka's MCP once, fetch the full tool list once,
    and return a dict of agent_name -> its scoped tool list.
 
    Doing this once at startup (not per-agent, not per-turn) matters:
    Kapruka's server-side caching aside, there's no reason to pay the
    connection + list_tools round trip more than once per process.
    """
    client = MultiServerMCPClient(KAPRUKA_MCP_CONFIG)
    all_tools = await client.get_tools()  # full list of 8, once
 
    return {
        agent_name: scope_tools(all_tools, allowed_names)
        for agent_name, allowed_names in AGENT_TOOL_SCOPES.items()
    }
 
 
# ---------------------------------------------------------------------------
# Wiring into LangGraph nodes
# ---------------------------------------------------------------------------
# Each agent node binds only its scoped subset to the LLM — the model
# literally cannot call a tool it wasn't given, so this is a hard
# boundary, not just a prompting convention.
 
""" async def example_usage():
    scoped = await build_scoped_toolsets()
 
    # e.g. inside search_node:
    #   llm_with_tools = llm.bind_tools(scoped["search_agent"])
    #
    # e.g. inside checkout_node:
    #   llm_with_tools = llm.bind_tools(scoped["checkout_agent"])
 
    for agent_name, tools in scoped.items():
        print(f"{agent_name}: {[t.name for t in tools]}")
 
 
if __name__ == "__main__":
    asyncio.run(example_usage()) """