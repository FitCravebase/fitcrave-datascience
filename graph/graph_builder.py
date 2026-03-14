from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from graph.state import AgentState
from graph.nodes.preprocessing import preprocessing_node
from graph.nodes.routing import routing_node
from graph.nodes.response import response_node
from graph.nodes.workout.workout import workout_node
from graph.nodes.meal_plan.meal_plan import meal_plan_node

# Router Function
def route_to_subagent(state: AgentState):
    """
    Reads the intent off the state's agent_data to decide where to route next.
    """
    data = state.get("agent_data", {})
    intent = data.get("active_subagent", "workout")
    if intent == "meal_plan":
        return "meal_plan"
    return "workout"

# Initialize the StateGraph with our AgentState TypedDict
builder = StateGraph(AgentState)

# Add our core nodes
builder.add_node("preprocessing", preprocessing_node)
builder.add_node("routing", routing_node)
builder.add_node("workout", workout_node)
builder.add_node("meal_plan", meal_plan_node)
builder.add_node("response", response_node)

# Define the flow (Edges)
builder.add_edge(START, "preprocessing")
builder.add_edge("preprocessing", "routing")

# Conditional Edge from Routing Node -> Sub Agents
builder.add_conditional_edges(
    "routing", 
    route_to_subagent, 
    {
        "workout": "workout",
        "meal_plan": "meal_plan"
    }
)

# Subagents always map to Response Node
builder.add_edge("workout", "response")
builder.add_edge("meal_plan", "response")

# Response node maps to End
builder.add_edge("response", END)

# Compile the graph with a checkpointer to persist state between turns
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
