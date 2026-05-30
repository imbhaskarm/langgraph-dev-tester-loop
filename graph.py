from langgraph.graph import StateGraph, END
import re
from state import GraphState
from agents import developer_node, tester_node


def should_continue(state: GraphState) -> str:
    critique = state["conversation_history"][-1].content

    match = re.search(r"Score[:\s]+(\d+(?:\.\d+)?)\s*/\s*10", critique, re.IGNORECASE)
    if not match:
        print("\nNo valid score found in tester output. Continuing loop.")
        return "developer_node"

    score = float(match.group(1))

    if "Tester returned empty output" in critique:
        print("\nTester output was empty earlier. Continuing loop.")
        return "developer_node"

    if score >= 10 and "ALL TESTS PASSED. Score: 10/10" in critique:
        print("\nScore 10/10 achieved. Stopping loop.")
        return END

    if state["reflection_count"] >= state["max_reflections"]:
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

     