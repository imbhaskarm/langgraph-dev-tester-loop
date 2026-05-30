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
            "Write a Python program to implement the FLAMES game. "
            "FLAMES stands for Friends, Love, Affection, Marriage, Enemies, Siblings. "
            "The program should define a flames_game(name1, name2) function that: "
            "1. Takes two name strings as input. "
            "2. Removes spaces and converts to lowercase. "
            "3. Cancels out common letters between the two names (each matched letter removed once from both). "
            "4. Counts the total remaining letters. "
            "5. Uses that count to cyclically eliminate letters from 'FLAMES' until one remains. "
            "6. Returns the full word corresponding to the surviving letter "
            "   (F=Friends, L=Love, A=Affection, M=Marriage, E=Enemies, S=Siblings). "
            "Test the function with at least 3 hardcoded name pairs and print the results. "
            "Add type hints, a docstring, and handle edge cases like empty strings or identical names."
        ),
        max_reflections=3,
    )

