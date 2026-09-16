import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the path to the parent directory (one level up)
parent_dir = os.path.dirname(current_dir)
# Add the parent directory to the system path
sys.path.append(parent_dir)


from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq


from states.agent_state import AgentState
from tools.kapruka_mcp import build_scoped_toolsets
import asyncio

t = asyncio.run(build_scoped_toolsets())
print(t)




