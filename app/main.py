from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any
from graph.graph_builder import graph
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ChatRequest(BaseModel):
    latest_message: str
    session_id: str
    user_id: str
    user_name: Optional[str] = None
    location: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    user_id: str
    session_id: str
    user_name: Optional[str] = None
    location: Optional[str] = None
    agent_data: Optional[Dict[str, Any]] = None

app = FastAPI(
    title="Health and Fitness Chatbot API",
    description="API for the Nutrition and Fitness AI Agent",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Health and Fitness Chatbot API"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    logger.info(f"Received /chat request - Session: {request.session_id}, User: {request.user_id}")
    logger.debug(f"Request payload: {request.model_dump()}")
    
    try:
        # Invoke the LangGraph agent asynchronously to prevent CancelledError
        result = await graph.ainvoke(
            {
                "messages": [("user", request.latest_message)],
                "agent_data": {
                    "session_id": request.session_id,
                    "user_id": request.user_id,
                    "user_name": request.user_name,
                    "location": request.location
                }
            }, 
            config={"configurable": {"thread_id": request.session_id, "user_id": request.user_id}}
        )
        
        logger.debug(f"LangGraph computation complete. Final state: {result}")
        
        # Extract the last message safely
        messages = result.get("messages", [])
        if messages:
            last_msg = messages[-1].content
            if isinstance(last_msg, list):
                response_text = " ".join([str(b.get("text", "")) for b in last_msg if isinstance(b, dict) and "text" in b])
            else:
                response_text = str(last_msg)
        else:
            response_text = "No response generated"
            
        agent_data = result.get("agent_data", {})
        
        logger.info(f"Successfully processed response for Session: {request.session_id}")
        
        return ChatResponse(
            response=response_text,
            user_id=request.user_id,
            session_id=request.session_id,
            user_name=request.user_name,
            location=request.location,
            agent_data=agent_data
        )
    except Exception as e:
        logger.error(f"Exception during /chat: {e}", exc_info=True)
        return ChatResponse(
            response="An unexpected server error occurred while contacting the AI.",
            user_id=request.user_id,
            session_id=request.session_id,
            agent_data={"error": str(e)}
        )
