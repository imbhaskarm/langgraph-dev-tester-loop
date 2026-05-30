from langchain_core.messages import HumanMessage
from graph import build_graph


def run(task: str, max_reflections: int = 3):
    """
    Run the developer-tester reflection loop for a given coding task.

    Args:
        task            -- plain-text description of the Python task to solve
        max_reflections -- max number of dev-test cycles before the loop stops
    """
    graph = build_graph()

    inputs = {
        "conversation_history": [HumanMessage(content=task,name="User")],
        "reflection_count": 0,
        "max_reflections": max_reflections,
    }

    for _ in graph.stream(inputs, stream_mode="values"):
        pass


 
if __name__ == "__main__":
    run(
    task=(
        "Write a Python program to implement Caesar Cipher encryption and decryption. "
        "Define encrypt(text, shift) and decrypt(text, shift) functions. "
        "Handle uppercase, lowercase, non-alpha characters, and wrap-around (z+1=a). "
        "Test with at least 3 examples including edge cases like shift=0 and shift=26. "
        "Add type hints, docstrings, and input validation."
    ),
    max_reflections=3,
)
