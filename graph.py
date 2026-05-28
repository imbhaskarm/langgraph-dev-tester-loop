from langgraph.graph import StateGraph, END

from state import GraphState
from agents import developer_node, tester_node


def should_continue(state: GraphState) -> str:
    """Conditional edge: keep looping or stop based on reflection count."""
    if state["reflection_count"] >= state["max_reflections"]:
        print("\033[91m")
        print(f"Reflection cap reached ({state['reflection_count']}/{state['max_reflections']}). Stopping.")
        print("\033[0m")
        return END
    return "tester_node"


def build_graph():
    builder = StateGraph(GraphState)

    builder.add_node("developer_node", developer_node)
    builder.add_node("tester_node", tester_node)

    builder.set_entry_point("developer_node")

    builder.add_conditional_edges(
        "developer_node",
        should_continue,
        {
            "tester_node": "tester_node",
            END: END,
        },
    )
    builder.add_edge("tester_node", "developer_node")

    return builder.compile()
