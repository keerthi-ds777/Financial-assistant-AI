from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from backend.agent.state import AgentState
from backend.agent.tools.yfinance_tool import get_stock_price, get_stock_history
from backend.agent.tools.tavily_tool import web_search
from backend.agent.tools.currency_tool import convert_currency, get_exchange_rate
from backend.agent.tools.vector_db_tool import search_stock_knowledge
from backend.config import settings

# ─── Tools ───────────────────────────────────────────────────────────────────

ALL_TOOLS = [
    get_stock_price,
    get_stock_history,
    web_search,
    convert_currency,
    get_exchange_rate,
    search_stock_knowledge,
]

# ─── LLM ─────────────────────────────────────────────────────────────────────

def _build_llm():
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        temperature=0.1,
        max_tokens=2048,
    ).bind_tools(ALL_TOOLS)

SYSTEM_PROMPT = """You are a smart financial assistant.

You have access to tools that can:
- Get current stock prices, key metrics, and historical stock data.
- Search the web for current news and events.
- Convert currencies and fetch exchange rates.
- Search a stock market knowledge base.

Always use tools when the question involves real-time data, stocks, currencies, or current events.
Be concise, factual, and structured in your responses.
"""

# ─── Graph Nodes ─────────────────────────────────────────────────────────────

def call_model(state: AgentState) -> AgentState:
    llm = _build_llm()
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    try:
        response = llm.invoke(messages)
    except Exception:
        # Fallback: plain LLM without tools if tool-call generation fails
        plain_llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            temperature=0.1,
            max_tokens=2048,
        )
        response = plain_llm.invoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END

# ─── Build Graph ─────────────────────────────────────────────────────────────

def build_graph():
    tool_node = ToolNode(ALL_TOOLS)

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()

# Singleton graph
_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
