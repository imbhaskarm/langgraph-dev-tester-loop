import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, HumanMessage
 
from langchain_experimental.tools import PythonREPLTool
from langgraph.prebuilt import create_react_agent
from prompts import DEVELOPER_SYSTEM_PROMPT, TESTER_SYSTEM_PROMPT
from state import GraphState
 
import io     
import contextlib  
load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
)

# Wrap PythonREPLTool with @tool so Groq receives a clean single-argument schema.
# The base PythonREPLTool has a multi-field schema that confuses the Groq tool-calling format.
_base_repl = PythonREPLTool()

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
developer_agent = create_react_agent(llm, tools=[python_repl_tool])
tester_agent = _create_tester_chain(llm, TESTER_SYSTEM_PROMPT)


def developer_node(state: GraphState) -> dict:
    """LangGraph node: invokes the Developer Agent to write or revise code."""
    print("\n" + "="*60)
    print("DEVELOPER AGENT -- generating / revising code...")
    print("="*60)

    response = developer_agent.invoke({"messages": state["conversation_history"]})
    last_message = response["messages"][-1]
    print("\033[92m")         # green
    print(last_message.content)
    print("\033[0m")          # reset

    new_message = AIMessage(content=last_message.content, name="Developer")
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
        "reflection_count": 1,
    }
