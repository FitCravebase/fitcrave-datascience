import os
import json
import logging
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from graph.state import AgentState
from utils.logger import setup_logger

load_dotenv()
logger = setup_logger(__name__)

def routing_node(state: AgentState):
    """
    Routing node that classifies the user intent and sets the active subagent.
    """
    logger.info("--- ROUTING NODE: INTENT CLASSIFICATION ---")
    
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.0, # low temp for precise classification
            max_tokens=100, # Allow buffer for JSON framing
            api_key=os.environ.get("GEMINI_API_KEY")
        )
        
        messages = state.get("messages", [])
        agent_data = state.get("agent_data", {})
        
        if not messages:
            return state
            
        # Temporary debug to check which API key is being loaded
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            masked_key = f"{api_key[:8]}...{api_key[-4:]}"
        else:
            masked_key = "None"
        logger.warning(f"USING GEMINI API KEY: {masked_key}")

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.0, # low temp for precise classification
            api_key=api_key
        )
        
        last_msg_content = messages[-1].content
        if isinstance(last_msg_content, list):
            last_msg_content = " ".join([b.get("text", "") for b in last_msg_content if isinstance(b, dict)])
            
        # Format the history into a string with clear role labels
        history = agent_data.get("history", [])
        history_clean = [m for m in history if m.get("content", "").strip()]
        last_2 = history_clean[-2:]
        
        history_text = ""
        if last_2:
            history_text = "\n\n--- RECENT CONVERSATION HISTORY ---\n"
            for msg in last_2:
                role = "User" if msg.get("role") == "user" else "Fitcrave"
                history_text += f"{role}: {msg.get('content')}\n"
            history_text += "-----------------------------------\n"
            
        current_user_msg = str(last_msg_content).strip()
            
        # Static Prompt
        system_prompt = (
            "You are an intent classifier for the Fitcrave app. "
            "Classify the user's LATEST intent as EXACTLY one of two options: 'workout' or 'meal_plan'. "
            "Use 'workout' for: exercises, gym, routines, splits, form advice, or ambiguous queries. "
            "Use 'meal_plan' for: diet, food, macros, calories, recipes, nutrition, or meal prep. "
            "OUTPUT FORMAT: Return ONLY a raw JSON object. No explanation, no apology, no markdown. "
            f"Example: {{\"intent\": \"workout\"}} or {{\"intent\": \"meal_plan\"}}. Nothing else.{history_text}"
        )
        
        invoke_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Latest User Message: {current_user_msg}")
        ]
        
        logger.debug(f"LLM Prompt for Routing: {[m.content for m in invoke_messages]}")
            
        ai_response = llm.invoke(invoke_messages)
        content = ai_response.content
        
        if isinstance(content, list):
            content = " ".join([b.get("text", "") for b in content if isinstance(b, dict)])
            
        # Log exact raw response for debugging
        logger.debug(f"RAW LLM Response Content: '{content}'")
        logger.debug(f"LLM Metadata/Stop Reason: {ai_response.response_metadata}")
            
        # Try to parse the JSON intent
        try:
            cleaned_content = content.strip()
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:]
            if cleaned_content.startswith("```"):
                cleaned_content = cleaned_content[3:]
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]
                
            parsed_data = json.loads(cleaned_content.strip())
            intent = parsed_data.get("intent", "workout") # fallback
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON intent from LLM: {content}. Defaulting to workout.")
            intent = "workout"
            
    except Exception as e:
        logger.error(f"Error in routing_node: {e}. Defaulting to workout.")
        intent = "workout"
        
    logger.info(f"Classified intent as: {intent}")
    
    agent_data["active_subagent"] = intent
    
    return {
        "agent_data": agent_data
    }
