from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Import the Schema and Nodes we created previously
from backend.models import AgentState
from backend.graph.nodes import auditor_node, fixer_node

# --- 1. Routing Logic ---


def route_request(state: AgentState):
    """
    Determines the entry point of the graph.

    Logic:
    - If 'target_issue' is present in the state, it means the user clicked
      the 'Auto-Fix' button in the UI. Route to -> 'fixer'.
    - Otherwise, it is a standard check. Route to -> 'auditor'.
    """
    if state.get("target_issue"):
        return "fixer"
    return "auditor"


# --- 2. Graph Construction ---

# Initialize the graph with our TypedDict state
workflow = StateGraph(AgentState)

# Add the nodes (The Workers)
workflow.add_node("auditor", auditor_node)
workflow.add_node("fixer", fixer_node)

# Set the Entry Point
# Instead of a fixed start, we use a conditional entry point based on user intent
workflow.set_conditional_entry_point(
    route_request, {"auditor": "auditor", "fixer": "fixer"}
)

# Set the Edges (The Flow)
# After the Auditor runs, we stop (wait for user to review results).
workflow.add_edge("auditor", END)

# After the Fixer runs, we also stop (so the user can review the change).
# Note: You could route 'fixer' -> 'auditor' to auto-recheck, but
# manual review is safer for UX trust.
workflow.add_edge("fixer", END)

# --- 3. Compilation ---

# MemorySaver allows the graph to maintain state between Streamlit reruns
memory = MemorySaver()

# Compile the graph into a runnable application
graph = workflow.compile(checkpointer=memory)
