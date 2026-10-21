import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the path to the parent directory (one level up)
parent_dir = os.path.dirname(current_dir)
# Add the parent directory to the system path
sys.path.append(parent_dir)

from langchain_ollama import ChatOllama
from dotenv import load_dotenv
from states.agent_state import GovPilotState
from prompts.orchestrator_prompt import orchestrator_prompt
from langgraph.types import interrupt
from langchain_core.output_parsers import JsonOutputParser
from utills.agent_routing import route_to_next_agent
from utills.loggers import get_logger

from langchain_core.messages import HumanMessage


load_dotenv()

logger = get_logger("orchestrator_agent")


def supervisor_agent(state: GovPilotState) -> dict:
    llm = ChatOllama

    user_query = state["messages"][-1]
    #user_query = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    logger.info("Starting Orchestrator for query: %s", user_query)

    
    
    # Step 3: Route based on what's been completed
    return route_to_next_agent(state)

    






    




 
