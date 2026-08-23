from config.agent_llms import search_agent_llm
from prompts.search_agent_prompt import search_agent_prompt

def search_agent(query: str) -> str:
    chat = search_agent_llm.invoke(search_agent_prompt(query))
    return chat.content