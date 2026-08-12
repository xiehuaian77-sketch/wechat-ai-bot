"""LangGraph Agent 图构建。"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agent.core import (
    executor_node,
    planner_node,
    reflector_node,
    responder_node,
    should_continue,
)
from app.agent.state import AgentState


def build_agent_graph() -> StateGraph:
    """构建 LangGraph Agent 图。"""
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("reflector", reflector_node)
    graph.add_node("responder", responder_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "executor")
    graph.add_conditional_edges(
        "executor",
        should_continue,
        {
            "reflector": "reflector",
            "responder": "responder",
        },
    )
    graph.add_edge("reflector", "executor")
    graph.add_edge("responder", END)

    return graph


__all__ = ["build_agent_graph"]
