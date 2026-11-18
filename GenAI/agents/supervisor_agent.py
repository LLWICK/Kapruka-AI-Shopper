import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the path to the parent directory (one level up)
parent_dir = os.path.dirname(current_dir)
# Add the parent directory to the system path
sys.path.append(parent_dir)





from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from prompts.supervisor_agent_prompt import ROUTER_PROMPT
from utills.loggers import get_logger


""" router_llm = ChatGroq(
    model="openai/gpt-oss-120b",
) """

router_llm = ChatOllama(model="llama3.2")




VALID_INTENTS = {"search", "details", "cart", "checkout", "track", "chat"}


async def supervisor_agent(state: dict) -> dict:

    logger = get_logger("supervisor_agent")
    logger.info("Executing Supervisor Agent.....")

    

    query = state.get("query", "").strip()

    if not query:
        logger.info("Supervisor agent path : other")
        return {"intent": "other"}

    history = state.get("messages", [])
    recent_history = "\n".join(
        f"{msg.type}: {msg.content}"
        for msg in history[-8:]
    )

    search_output = state.get("search_agent_output") or {}
    if hasattr(search_output, "model_dump"):
        search_output = search_output.model_dump()

    products = search_output.get("products", [])

    router_input = f"""
        Previous conversation:
        {recent_history}

        Previously retrieved products:
        {products}

        Latest customer message:
        {query}

        Classify only the latest customer message.
        """

    


    response = await router_llm.ainvoke([
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=router_input),
    ])

    # Handle text responses and defensively normalize the result.
    content = response.content
    if not isinstance(content, str):
        content = str(content)

    intent = content.strip().lower().strip("`'\". \n")

    if intent not in VALID_INTENTS:
        # Safe fallback if the model returns unexpected output.
        intent = "search"


    logger.info("Supervisor agent path : %s" , intent)
    return {"intent": intent}
