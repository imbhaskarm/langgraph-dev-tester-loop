import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_experimental.tools import PythonREPLTool

from prompts import DEVELOPER_SYSTEM_PROMPT, TESTER_SYSTEM_PROMPT
from state import GraphState

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
    """Execute Python code and return the printed output.
    Pass ONLY the raw Python code string as the 'code' parameter.
    Do NOT wrap in markdown, JSON, or XML tags."""
    return _base_repl.run(code)


def _create_agent(llm, tools, system_prompt) -> AgentExecutor:
    """Build a LangChain tool-calling agent wrapped in an AgentExecutor."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, handle_parsing_errors=True)


def _create_tester_chain(llm, system_prompt):
    """Build a simple LCEL chain for the Tester -- no tool calls needed, just LLM reasoning."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    return prompt | llm


# Instantiate both agents at module level so graph.py can import them directly.
developer_agent = _create_agent(llm, [python_repl_tool], DEVELOPER_SYSTEM_PROMPT)
tester_agent = _create_tester_chain(llm, TESTER_SYSTEM_PROMPT)


def developer_node(state: GraphState) -> dict:
    """LangGraph node: invokes the Developer Agent to write or revise code."""
    print("\n" + "="*60)
    print("DEVELOPER AGENT -- generating / revising code...")
    print("="*60)

    response = developer_agent.invoke({"messages": state["conversation_history"]})

    print("\033[92m")         # green
    print(response["output"])
    print("\033[0m")          # reset

    new_message = AIMessage(content=response["output"], name="Developer")
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

    critique = HumanMessage(content=response.content, name="Tester")
    return {
        "conversation_history": [critique],
        "reflection_count": 1,
    }
