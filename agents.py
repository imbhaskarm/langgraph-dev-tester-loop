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
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.7)

# Wrap PythonREPLTool with @tool so Groq receives a clean single-argument schema.
# The base PythonREPLTool has a multi-field schema that confuses the Groq tool-calling format.
 

@tool
def python_repl_tool(code: str) -> str:
    """Execute Python code and return printed output. Never use input() in code."""
    stdout_capture = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout_capture):
            exec(code, {})
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
developer_agent = create_react_agent(llm, tools=[python_repl_tool],state_modifier=DEVELOPER_SYSTEM_PROMPT)
tester_agent = _create_tester_chain(llm, TESTER_SYSTEM_PROMPT)


def developer_node(state: GraphState) -> dict:
    """LangGraph node: invokes the Developer Agent to write or revise code."""
    print("\n" + "="*60)
    print("DEVELOPER AGENT -- generating / revising code...")
    print("="*60)

    response = developer_agent.invoke({"messages": state["conversation_history"]})
    messages = response["messages"]

    

    TESTER_PATTERNS = (
        "### Unit Test Report",
        "Unit Test Report",
        "Score:",
        "Test Case",
        "Here's a detailed",
        "Here is a detailed",
        "We will write test",
    )

    content = ""

    # First priority: last AIMessage with text, no tool calls, not a tester report
    for msg in reversed(messages):
        if (isinstance(msg, AIMessage)
                and not msg.tool_calls
                and msg.content
                and msg.content.strip()
                and not any(msg.content.strip().startswith(p) for p in TESTER_PATTERNS)):
            content = msg.content
            break

    # Second priority: last ToolMessage (actual code execution output)
    if not content:
        for msg in reversed(messages):
            if isinstance(msg, ToolMessage) and msg.content and msg.content.strip():
                content = msg.content
                break

    print("\033[92m")
    print(content)
    print("\033[0m")

        # Strip raw JSON tool call text that llama sometimes appends
     
    content = re.sub(r'\{[\s\S]*?"code"[\s\S]*?\}', '', content).strip()

    new_message = AIMessage(content=content, name="Developer")
    return {"conversation_history": [new_message]}
     


def tester_node(state: GraphState) -> dict:
    """LangGraph node: invokes the Tester Agent to score and critique the latest code."""
    print("\n" + "="*60)
    print(f"TESTER AGENT -- critique iteration #{state['reflection_count'] + 1}")
    print("="*60)

    response = tester_agent.invoke({"messages": state["conversation_history"]})

    print("\033[94m")         # blue
    print(response.content)
    print("\033[0m")          # reset

    # In tester_node:
    critique = AIMessage(content=response.content, name="Tester")   
    return {
        "conversation_history": [critique],
         "reflection_count": state["reflection_count"] + 1
    }
