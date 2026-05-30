from langgraph.graph import StateGraph, END
import re
from state import GraphState
from agents import developer_node, tester_node


def should_continue(state: GraphState) -> str:
    critique = state["conversation_history"][-1].content

    match = re.search(r"Score[:\s]+(\d+(?:\.\d+)?)\s*/\s*10", critique, re.IGNORECASE)
    score = float(match.group(1)) if match else 0.0

    if score >= 10:
        print("\n Score 10/10 achieved. Stopping loop.")
        return END

    if state["reflection_count"] > state["max_reflections"]:    # ← FIX: > instead of >=
        print(f"\nReflection cap reached ({state['reflection_count']}/{state['max_reflections']}). Stopping.")
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

     