# backend/app/agents/agent.py
"""
LangGraph Agent (Gemini + ToolNode + Stable Output)
✔ Proper LangGraph state management
"""

from typing import Annotated, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langchain_core.tools import tool

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

import wikipedia

import os
from dotenv import load_dotenv

load_dotenv() 
# =====================================================
# GEMINI LLM
# =====================================================
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)


# =====================================================
# STATE
# MUST use add_messages for ToolNode to work properly
# =====================================================
class State(TypedDict):
    messages: Annotated[list, add_messages]


# =====================================================
# TOOLS (ONLY 2)
# =====================================================

# Tavily Search Tool
tavily = TavilySearch(max_results=2)


# Wikipedia Tool
@tool
def wikipedia_search(query: str) -> str:
    """Search Wikipedia and return summary."""

    try:
        results = wikipedia.search(query)

        if not results:
            return "No Wikipedia results found."

        page = wikipedia.page(results[0])

        # 🔥 limit tokens to avoid rate limit issues
        return page.summary[:1000]

    except Exception as e:
        return f"Wikipedia error: {str(e)}"


tools = [tavily, wikipedia_search]


# =====================================================
# TOOL-ENABLED MODEL
# =====================================================
llm_with_tools = llm.bind_tools(tools)


# =====================================================
# 🤖 CHAT NODE
# =====================================================
def chatbot(state: State):
    """
    Main LLM node
    """

    response = llm_with_tools.invoke(state["messages"])

    return {"messages": [response]}


# =====================================================
# TOOL NODE
# =====================================================
tool_node = ToolNode(tools=tools)


# =====================================================
# GRAPH BUILDING
# =====================================================
graph_builder = StateGraph(State)

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "chatbot")

# If tool is needed → go to tools
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition
)

# After tool execution → go back to chatbot
graph_builder.add_edge("tools", "chatbot")


# =====================================================
# MEMORY (IMPORTANT FOR CHAT CONTEXT)
# =====================================================
memory = MemorySaver()

graph = graph_builder.compile(checkpointer=memory)


# =====================================================
# RUN FUNCTION
# Handles Gemini structured outputs safely
# =====================================================
def run_agent(session_id: str, user_input: str):

    config = {"configurable": {"thread_id": session_id}}

    result = graph.invoke(
        {"messages": [("user", user_input)]},
        config=config
    )

    # =================================================
    # SAFE OUTPUT NORMALIZATION
    # =================================================
    last_msg = result["messages"][-1]

    content = getattr(last_msg, "content", "")

    # Case 1: normal string
    if isinstance(content, str):
        return content

    # Case 2: Gemini structured output (list of dicts)
    if isinstance(content, list):
        texts = []

        for item in content:
            if isinstance(item, dict) and "text" in item:
                texts.append(item["text"])
            elif isinstance(item, str):
                texts.append(item)

        return " ".join(texts).strip()

    return str(content)