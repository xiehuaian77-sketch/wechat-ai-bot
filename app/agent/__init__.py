"""Agent 核心模块 —— LangGraph 多步推理引擎。

模块结构:
    state.py   — AgentState + TaskStep (纯数据，无依赖)
    graph.py   — LangGraph 图构建
    core.py    — 节点实现（planner / executor / reflector / responder）
    engine.py  — Agent 运行时（编译 + 执行）
    memory.py  — SQLite 持久化记忆
    rag.py     — 轻量级 RAG 知识库
"""

from app.agent.state import AgentState, TaskStep
from app.agent.graph import build_agent_graph
from app.agent.engine import agent_engine
from app.agent.core import (
    planner_node,
    executor_node,
    reflector_node,
    responder_node,
    should_continue,
)

__all__ = [
    "AgentState",
    "TaskStep",
    "agent_engine",
    "build_agent_graph",
    "planner_node",
    "executor_node",
    "reflector_node",
    "responder_node",
    "should_continue",
]
