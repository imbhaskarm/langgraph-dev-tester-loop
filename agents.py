import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.messages import ToolMessage
import re

from langgraph.prebuilt import create_react_agent
from prompts import DEVELOPER_SYSTEM_PROMPT, TESTER_SYSTEM_PROMPT
from state import GraphState
 
import io     
import contextlib  
load_dotenv()
developer_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
tester_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.0)

# Wrap PythonREPLTool with @tool so Groq receives a clean single-argument schema.
# The base PythonREPLTool has a multi-field schema that confuses the Groq tool-calling format.
 

@tool
def python_repl_tool(code: str) -> str:
    """Execute Python code and return printed output. Never use input() in code."""
    stdout_capture = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout_capture):
            exec(code, {"__builtins__": __builtins__})   # ← FIX: restore builtins
        return stdout_capture.getvalue() or "Code executed with no output."
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"





def _create_tester_chain(llm, system_prompt):
    """Build a simple LCEL chain for the Tester -- no tool calls needed, just LLM reasoning."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    return prompt | llm


# Instantiate both agents at module level so graph.py can import them directly.
developer_agent = create_react_agent(
    developer_llm,
    tools=[python_repl_tool],
    state_modifier=DEVELOPER_SYSTEM_PROMPT,
)
tester_agent = _create_tester_chain(tester_llm, TESTER_SYSTEM_PROMPT)


def _extract_python_code(text: str) -> str:
    match = re.search(r"```python\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()

def developer_node(state: GraphState) -> dict:
    print("\n" + "="*60)
    print("DEVELOPER AGENT -- generating / revising code...")
    print("="*60)

    response = developer_agent.invoke({"messages": state["conversation_history"]})
    messages = response["messages"]

    content = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and not msg.tool_calls and msg.content and msg.content.strip():
            content = _extract_python_code(msg.content)
            break

    if not content:
        content = (
            "Developer failed to provide a final code response.\n"
            "Return the complete Python solution in a ```python fenced block."
        )

    print("\033[92m")
    print(content)
    print("\033[0m")

    new_message = AIMessage(content=content, name="Developer")
    return {"conversation_history": [new_message]}
     


def tester_node(state: GraphState) -> dict:
    print("\n" + "="*60)
    print(f"TESTER AGENT -- critique iteration #{state['reflection_count'] + 1}")
    print("="*60)

    response = tester_agent.invoke({"messages": state["conversation_history"]})
    raw = response.content

    if isinstance(raw, str):
        content = raw.strip()
    elif isinstance(raw, list):
        parts = []
        for item in raw:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        content = "\n".join(parts).strip()
    else:
        content = str(raw).strip()

    if not content:
        content = (
            "Unit Test Report\n"
            "- Tester returned empty output.\n\n"
            "Score: 0/10\n\n"
            "Critique & Suggestions\n"
            "- No valid test review was produced.\n"
            "- Re-run the tester with the full developer code.\n"
        )
        print("⚠️ Tester returned empty — forcing retry path with Score: 0/10.")

    print("\033[94m")
    print(content)
    print("\033[0m")

    critique = AIMessage(content=content, name="Tester")
    return {
        "conversation_history": [critique],
        "reflection_count": 1
    }
