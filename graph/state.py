from typing import TypedDict, Annotated, Dict, Any
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    Represents the state of our health and fitness agent.
    """
    # Contains the list of messages in the conversation
    messages: Annotated[list, add_messages]
    
    # Store dynamic JSON payload data fetched from agents
    agent_data: Dict[str, Any]
