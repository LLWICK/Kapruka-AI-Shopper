import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the path to the parent directory (one level up)
parent_dir = os.path.dirname(current_dir)
# Add the parent directory to the system path
sys.path.append(parent_dir)

from states.agent_state import AgentState


def route_to_next_agent(state: AgentState) -> dict:
    """Determines the next agent in the pipeline."""
    
    if not state.get("search_agent_output"):
        return {"next_agent": "search_agent"}

    

    return {"next_agent": None, "final_response": state.get("final_response")}
