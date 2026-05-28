# LangGraph Developer-Tester Loop

A multi-agent system where a **Developer agent** writes Python code and a **Tester agent** scores it, critiques it, and sends it back for revision — all orchestrated by a LangGraph `StateGraph` with a configurable reflection cap.

Built while learning LangGraph as part of my move from .NET/Azure development into GenAI engineering. The goal was to understand how to wire agents into a stateful graph with conditional routing and shared memory.

---

## How It Works

```
START
  |
  v
[developer_node]  -- Developer Agent writes/revises Python code
  |
  v
 should_continue()  -- checks reflection_count vs max_reflections
  |
  |-- under cap --> [tester_node]  -- Tester scores code (0-10) and critiques it
  |                      |
  |                      v
  |               [developer_node]  -- loop back for revision
  |
  |-- cap reached --> END
```

- The **Developer** uses `PythonREPLTool` to actually run code during generation
- The **Tester** reasons through test cases without executing them — pure LLM evaluation
- `GraphState` uses `Annotated[int, operator.add]` so `reflection_count` auto-increments without manual tracking
- The loop stops when `reflection_count >= max_reflections`

---

## Project Structure

```
langgraph-dev-tester-loop/
├── main.py          # entry point — run a task through the loop
├── graph.py         # StateGraph definition, node wiring, conditional edge
├── agents.py        # Developer and Tester agent setup, node functions
├── state.py         # GraphState TypedDict with Annotated reducers
├── prompts.py       # DEVELOPER_SYSTEM_PROMPT and TESTER_SYSTEM_PROMPT
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Setup

**1. Clone and create a virtual environment**

```bash
git clone https://github.com/imbhaskarm/langgraph-dev-tester-loop.git
cd langgraph-dev-tester-loop
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Set up your API key**

Copy `.env.example` to `.env` and add your Groq key:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Get a free key at [https://console.groq.com](https://console.groq.com)

**4. Run**

```bash
python main.py
```

You can also import `run()` directly and pass any task:

```python
from main import run

run(
    task="Write a Python function to validate an email address using regex.",
    max_reflections=2
)
```

---

## Example Output

```
============================================================
DEVELOPER AGENT -- generating / revising code...
============================================================
[green]
def flames(name1, name2):
    ...
[reset]

============================================================
TESTER AGENT -- critique iteration #1
============================================================
[blue]
Unit Test Report:
- test_basic_input: PASS
- test_empty_string: FAIL -- no validation for empty names
- test_special_chars: FAIL -- does not strip spaces before counting

Score: 6/10
Critique: Add input validation for empty strings and strip whitespace...
[reset]
```

---

## Things I Learned Building This

- `Annotated[int, operator.add]` as a LangGraph reducer is the cleanest way to accumulate a counter across nodes without passing it manually
- The Tester agent works better as a plain LCEL chain (`prompt | llm`) than as a full `AgentExecutor` — it has no tools to call, so the extra loop overhead just adds latency
- Wrapping `PythonREPLTool` with `@tool` gives Groq a simpler one-argument schema and avoids tool-calling format errors
- `graph.stream()` instead of `graph.invoke()` lets you see each agent's output as it happens rather than waiting for the whole loop to finish

---

## Tech Stack

| Tool | Purpose |
|---|---|
| LangGraph | Agent orchestration — StateGraph, conditional edges |
| LangChain | Agent executor, LCEL chains, prompt templates |
| Groq (Llama 3.3-70b) | LLM for both developer and tester agents |
| PythonREPLTool | Lets the developer agent actually run Python code |
| python-dotenv | Environment variable management |
