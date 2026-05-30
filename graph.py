from langgraph.graph import StateGraph, END

from state import GraphState
from agents import developer_node, tester_node


def should_continue(state: GraphState) -> str:
    if state["reflection_count"] >= state["max_reflections"]:
        print(f"\033[91mReflection cap reached ({state['reflection_count']}/{state['max_reflections']}). Stopping.\033[0m")
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
