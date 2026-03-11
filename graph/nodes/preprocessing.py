from langchain_core.messages import HumanMessage
from graph.state import AgentState
from utils.logger import setup_logger
from utils.db import push_conversation

logger = setup_logger(__name__)

def preprocessing_node(state: AgentState):
    """
    Preprocess incoming messages dynamically.
    E.g., extracting intent, sanitizing input, recognizing user context.
    """
    logger.info("--- PREPROCESSING NODE ---")
    
    # Extract metadata context from graph execution
    messages = state.get("messages", [])
    agent_data = state.get("agent_data", {})
    
    # Extract properties passed in via the config
    # In newer langgraph contexts, these are usually retrieved downstream if injected directly 
    # to state, our state currently tracks user and session.
    # We will compute the sequence number by looking at the existing message list length.
    
    sequence_num = len(messages) if messages else 1
    
    if messages:
        last_message = messages[-1].content
        if isinstance(last_message, list):
            last_message = " ".join([b.get("text", "") for b in last_message if isinstance(b, dict)])
            
        logger.info(f"Processing user sequence #{sequence_num}")
        
        # We need the user and session ID, we'll extract it from the agent_data state
        session_id = agent_data.get("session_id", "default_session")
        user_id = agent_data.get("user_id", "default_user")
        
        # Structure the message for MongoDB
        db_message = {
            "type": "human",
            "content": str(last_message),
            "sequence_number": sequence_num
        }
        
        # Push to DB
        push_conversation(session_id, user_id, db_message, agent_data)
        
        # Fetch the conversation history once and store it in agent_data for all nodes
        from utils.db import get_conversation_history
        history = get_conversation_history(session_id, user_id, limit=10)
        agent_data["history"] = history
        
        # Keep track of the current sequence number in agent_data for downstream nodes
        agent_data["current_sequence"] = sequence_num
        
    return {"agent_data": agent_data}
