from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Import the Schema and Nodes we created previously
from backend.models import AgentState
from backend.graph.nodes import auditor_node, fixer_node, consistency_node

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


# --- 4. Batch Audit Helper ---
def run_batch_audit(sections: list) -> dict:
    """
    Runs the auditor node for ALL sections sequentially (to avoid rate limits/complexity),
    and then runs the Consistency Check on the full text.
    """
    results_map = {}
    full_text = []

    # 1. Audit Individual Sections
    for section in sections:
        sec_id = section["id"]
        meta = section["meta"]
        content = section["user_data"]["content"]

        # Collect text for global check
        full_text.append(f"SECTION: {meta['title']}\nCONTENT:\n{content}\n")

        # Prepare state for single audit
        # Note: We can reuse the graph, or just call the auditor_node directly for simplicity and speed
        # calling node directly avoids state overhead for batch jobs
        state = {
            "section_title": meta["title"],
            "criteria": meta["criteria"],
            "template_structure": meta["template_structure"],
            "user_content": content,
        }
        
        # Run Auditor
        audit_result = auditor_node(state)
        results_map[sec_id] = audit_result

    # 2. Run Global Consistency Check
    combined_content = "\n---\n".join(full_text)
    global_result = consistency_node(combined_content)

    return {
        "section_results": results_map,
        "global_result": global_result
    }
