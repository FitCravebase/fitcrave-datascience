from graph.state import AgentState
from utils.logger import setup_logger
from utils.db import push_conversation

logger = setup_logger(__name__)

def response_node(state: AgentState):
    """
    Final node that structures the agent payload, logs the response before returning.
    This separates the LLM generation step from the formatted JSON response step.
    """
    logger.info("--- RESPONSE NODE ---")
    
    # Retrieve the active messages/data that were computed by earlier nodes
    messages = state.get("messages", [])
    agent_data = state.get("agent_data", {})
    
    # We need the user and session ID
    session_id = agent_data.get("session_id", "default_session")
    user_id = agent_data.get("user_id", "default_user")
    
    # The current sequence number of the corresponding user message earlier
    user_sequence = agent_data.get("current_sequence", 0)
    ai_sequence = user_sequence + 1
    
    # For now, we simply extract the last generated AI message
    if messages:
        last_message = messages[-1].content
    else:
        last_message = "No response generated."
        
    logger.info(f"Final Response to User (Seq {ai_sequence}): {last_message}")
    logger.debug(f"Attached Agent Data payload: {agent_data}")
    
    # Structure the message for MongoDB — only persist non-empty AI responses
    if messages and str(last_message).strip():
        db_message = {
            "type": "ai",
            "content": str(last_message),
            "sequence_number": ai_sequence,
            "generated_by": agent_data.get("active_subagent", "system")
        }
        
        # Push to DB
        push_conversation(session_id, user_id, db_message, agent_data)
        agent_data["current_sequence"] = ai_sequence
    elif messages and not str(last_message).strip():
        logger.warning(f"Skipping empty AI response for session {session_id} — not persisting to DB.")
    
    # Returning the final structured state
    return {"agent_data": agent_data}
