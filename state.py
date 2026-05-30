import operator
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage


class GraphState(TypedDict):
    """
    Shared state that flows through every node in the LangGraph.

    Fields:
        max_reflections      -- hard ceiling on dev-test cycles
        reflection_count     -- running counter; auto-incremented by operator.add reducer
        conversation_history -- full message log across all agent turns
    """
    max_reflections: int
    reflection_count: int
    conversation_history: Annotated[list[BaseMessage], operator.add]
