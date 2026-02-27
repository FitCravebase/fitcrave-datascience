"""
LangGraph Orchestrator Agent

The central brain that coordinates all FitCrave AI engines.
Every user interaction flows through here:
  1. Pull user context from the database
  2. Classify intent (nutrition, workout, coaching, general chat)
  3. Delegate to the appropriate engine
  4. Return a unified, coherent response
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel


# ------------------------------------------------------------------
# Intent Classification
# ------------------------------------------------------------------
class UserIntent(str, Enum):
    """Possible user intents that the orchestrator can route."""

    MEAL_PLAN = "meal_plan"           # Generate or modify meal plan
    MEAL_LOG = "meal_log"             # Log a meal manually
    MEAL_SNAP = "meal_snap"           # Analyze food image
    MACRO_QUERY = "macro_query"       # Ask about macros/calories
    WORKOUT_PLAN = "workout_plan"     # Generate or modify workout plan
    WORKOUT_LOG = "workout_log"       # Log a workout session
    COACHING = "coaching"             # Ask for coaching advice
    GENERAL_CHAT = "general_chat"     # General health/fitness question
    PROGRESS_CHECK = "progress_check" # Check progress/stats
    SETTINGS = "settings"            # Update preferences/profile


class OrchestratorState(BaseModel):
    """State maintained across the orchestrator graph."""

    user_id: str
    messages: list[dict[str, Any]] = []
    intent: UserIntent | None = None
    user_context: dict[str, Any] = {}
    engine_response: dict[str, Any] = {}
    final_response: str = ""


# ------------------------------------------------------------------
# Orchestrator Graph (LangGraph)
# ------------------------------------------------------------------
async def create_orchestrator_graph():
    """
    Build the LangGraph state graph for the orchestrator.

    Graph flow:
        classify_intent → route_to_engine → [nutrition|workout|coaching] → format_response

    TODO: Implement the full LangGraph graph with:
        - StateGraph definition
        - Node functions for each step
        - Conditional edges based on intent
        - Memory/checkpointing for conversation history
    """
    # from langgraph.graph import StateGraph, END
    # graph = StateGraph(OrchestratorState)
    # graph.add_node("classify_intent", classify_intent_node)
    # graph.add_node("fetch_context", fetch_context_node)
    # graph.add_node("nutrition_engine", nutrition_engine_node)
    # graph.add_node("workout_engine", workout_engine_node)
    # graph.add_node("coaching_engine", coaching_engine_node)
    # graph.add_node("format_response", format_response_node)
    # ...
    pass
