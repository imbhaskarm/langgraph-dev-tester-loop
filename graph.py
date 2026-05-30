from langgraph.graph import StateGraph, END

from state import GraphState
from agents import developer_node, tester_node


def should_continue(state: GraphState) -> str:
    critique = state["conversation_history"][-1].content
    if "10/10" in critique or "Score: 10" in critique:
        return END
    if state["reflection_count"] >= state["max_reflections"]:
        return END
    return "developer_node"


def build_graph():
    builder = StateGraph(GraphState)
    builder.add_node("developer_node", developer_node)
    builder.add_node("tester_node", tester_node)
    builder.set_entry_point("developer_node")
    builder.add_edge("developer_node", "tester_node")
    builder.add_conditional_edges("tester_node", should_continue)   
    return builder.compile()

    return builder.compile()
