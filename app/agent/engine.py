"""Agent 引擎运行时。"""
from __future__ import annotations

import time
from typing import Any

from langgraph.graph import END, StateGraph

from app.agent.core import (
    planner_node,
    executor_node,
    reflector_node,
    responder_node,
    should_continue,
)
from app.agent.state import AgentState
from app.context import UserMemory, KnowledgeBase, tool_result_cache
from app.utils.logger import logger


class AgentEngine:
    """LangGraph Agent 引擎运行时。"""

    def __init__(self) -> None:
        self._graph: StateGraph | None = None
        self._app = None

    def _build(self) -> None:
        """构建并编译 Agent 图（懒加载）。"""
        if self._app is not None:
            return

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

        self._graph = graph
        self._app = graph.compile()
        logger.info("Agent graph compiled")

    async def run(self, messages: list[dict[str, str]], provider: str = "openai", **kwargs: Any) -> dict[str, Any]:
        """运行 Agent。

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            provider: AI 提供商名称

        Returns:
            {
                "final_answer": str,
                "tool_results": list,
                "iterations": int,
                "plan": list,
                "latency_ms": int,
                "tokens_used": int,
                "tool_success_rate": float,
            }
        """
        self._build()

        start_time = time.perf_counter()

        # 转换为 LangChain 消息格式
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

        lc_messages = []
        for msg in messages:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))

        # 上下文工程：注入用户记忆 + 知识库检索（如果有 user_id）
        user_memory = kwargs.get("user_memory")
        knowledge_context = kwargs.get("knowledge_context")
        system_prompt = kwargs.get("system_prompt", "你是电商智能客服。")
        context_parts = [system_prompt]
        if user_memory:
            context_parts.append(f"用户画像：{json.dumps(user_memory, ensure_ascii=False)}")
        if knowledge_context:
            context_parts.append(f"知识库检索结果：{knowledge_context}")
        context_parts.append("请基于以上信息，生成专业、友好的回复。")
        augmented_system = "\n\n".join(context_parts)
        if lc_messages and lc_messages[0].__class__.__name__ == "SystemMessage":
            lc_messages[0] = SystemMessage(content=augmented_system)
        else:
            lc_messages = [SystemMessage(content=augmented_system)] + lc_messages

        initial_state: AgentState = {
            "messages": lc_messages,
            "plan": [],
            "current_task": None,
            "tool_results": [],
            "iteration": 0,
            "final_answer": None,
            "needs_retry": False,
            "provider": provider,
        }

        try:
            # LangGraph 异步节点使用 ainvoke
            result = await self._app.ainvoke(initial_state)
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            tool_results = result.get("tool_results", [])
            tool_success_count = sum(1 for r in tool_results if not str(r.get("output", "")).startswith("Error"))
            tool_success_rate = tool_success_count / len(tool_results) if tool_results else 1.0

            # 人机协同：如果被拦截，直接返回拦截信息
            if result.get("blocked"):
                return {
                    "final_answer": result.get("tool_results", [{}])[-1].get("output", "操作需要人工审批"),
                    "tool_results": result.get("tool_results", []),
                    "iterations": result.get("iteration", 0),
                    "plan": [{"type": s.type, "name": s.name} for s in result.get("plan", [])],
                    "latency_ms": latency_ms,
                    "tokens_used": result.get("tokens_used", 0),
                    "tool_success_rate": round(tool_success_rate, 2),
                    "blocked": True,
                    "risk_level": result.get("risk_level"),
                }

            return {
                "final_answer": result.get("final_answer", ""),
                "tool_results": tool_results,
                "iterations": result.get("iteration", 0),
                "plan": [{"type": s.type, "name": s.name} for s in result.get("plan", [])],
                "latency_ms": latency_ms,
                "tokens_used": result.get("tokens_used", 0),
                "tool_success_rate": round(tool_success_rate, 2),
            }
        except Exception as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Agent run error: {e}")
            # 降级：直接调用 LLM
            from app.services.ai.manager import ai_manager

            response = await ai_manager.chat(provider, messages)
            return {
                "final_answer": response,
                "tool_results": [],
                "iterations": 0,
                "plan": [],
                "latency_ms": latency_ms,
                "tokens_used": 0,
                "tool_success_rate": 0.0,
            }


agent_engine = AgentEngine()