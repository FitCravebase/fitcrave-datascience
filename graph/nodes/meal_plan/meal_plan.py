import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from graph.state import AgentState
from utils.logger import setup_logger

load_dotenv()
logger = setup_logger(__name__)

def meal_plan_node(state: AgentState):
    """
    Dedicated sub-agent node for handling Diet and Meal Plan inquiries.
    """
    logger.info("--- MEAL PLAN NODE ---")
    
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3,
            api_key=os.environ.get("GEMINI_API_KEY")
        )
        
        # Read user message history
        messages = state.get("messages", [])
        agent_data = state.get("agent_data", {})
        
        if not messages:
            return state
            
        last_msg_content = messages[-1].content
        if isinstance(last_msg_content, list):
            last_msg_content = " ".join([b.get("text", "") for b in last_msg_content if isinstance(b, dict)])
            
        # Static Prompt
        system_prompt = (
            "You are a specialized Nutritionist for the Fitcrave app. "
            "Your purpose is to provide detailed meal plans, calculate macros, and suggest recipes or grocery lists based on user constraints. "
            "Address the user's dietary needs clearly and concisely. "
            "Respond in plain text, do NOT use JSON. "
            "CRITICAL: Be extremely precise. Do not produce extra words, preamble, or conversational filler. Give only the exact diet plan requested."
        )
        
        # Build prompt thread from history
        invoke_messages = [SystemMessage(content=system_prompt)]
        
        # Dynamic Prompt: Conversation History from state
        history = agent_data.get("history", [])
        history_clean = [m for m in history if m.get("content", "").strip()]
        
        history_text = ""
        if history_clean:
            history_text = "\n\n--- RECENT CONVERSATION HISTORY ---\n"
            for msg in history_clean:
                role = "User" if msg.get("role") == "user" else "Fitcrave"
                history_text += f"{role}: {msg.get('content')}\n"
            history_text += "-----------------------------------\n"
            
        system_prompt += history_text
        
        invoke_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Latest User Message: {str(last_msg_content).strip()}")
        ]
        
        # Get meal response
        ai_response = llm.invoke(invoke_messages)
        content = ai_response.content
        
        if isinstance(content, list):
            content = " ".join([str(b.get("text", "")) for b in content if isinstance(b, dict)])
            
        logger.debug(f"RAW Meal Plan LLM Response: '{content}'")
        logger.debug(f"Meal Plan LLM Metadata: {ai_response.response_metadata}")
            
        agent_data["intent"] = "diet_plan"
        agent_data["source"] = "meal_plan_node"
            
        return {
            "messages": [AIMessage(content=content)],
            "agent_data": agent_data
        }
        
    except Exception as e:
        logger.error(f"Error in meal plan node: {e}", exc_info=True)
        
        agent_data["error"] = str(e)
        agent_data["source"] = "meal_plan_node"
        
        return {
            "messages": [AIMessage(content="I encountered an error trying to generate your nutrition plan.")],
            "agent_data": agent_data
        }
