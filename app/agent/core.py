"""LangGraph Agent 引擎。"""

from __future__ import annotations

from typing import Any

from app.agent.human_in_the_loop import human_in_the_loop
from app.agent.state import AgentState, TaskStep
from app.services.ai.manager import ai_manager
from app.tools.manager import tool_manager
from app.utils.logger import logger

# =============================================================================
# Agent 节点定义
# =============================================================================


async def planner_node(state: AgentState) -> dict[str, Any]:
    """规划器节点: 分析用户意图，生成执行计划。"""
    last_message = state.messages[-1].content if state.messages else ""

    # 电商客服场景的系统提示
    system_prompt = """你是电商智能客服 Agent 的规划器。分析用户意图，生成执行步骤。

业务场景：
1. 订单查询：用户询问订单状态、物流信息
2. 售后退款：用户申请退款、退货
3. 商品咨询：用户询问商品信息、库存、价格
4. 投诉建议：用户投诉或提出建议
5. 其他咨询：一般性问题

可用工具：
- get_current_time: 获取当前时间
- get_weather: 查询天气
- get_exchange_rate: 查询汇率
- calculate: 数学计算
- search_web: 网络搜索
- python_exec: 执行 Python 代码

输出 JSON 格式（不要包含其他内容）：
{"steps": [{"type": "tool", "name": "tool_name", "description": "步骤描述"}, ...]}"""

    try:
        response = await ai_manager.chat(
            state.provider,
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"用户问题：{last_message}"},
            ],
            temperature=0.3,
            max_tokens=256,
        )

        # 解析 JSON 响应
        import json
        import re

        # 提取 JSON
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            plan_data = json.loads(json_match.group())
            steps = []
            for s in plan_data.get("steps", []):
                steps.append(
                    TaskStep(
                        type=s.get("type", "think"),
                        name=s.get("name", s.get("description", "unknown")),
                        description=s.get("description", ""),
                    )
                )
        else:
            # 解析失败，使用默认计划
            steps = [
                TaskStep(type="think", name="分析用户意图", description="理解用户需求"),
                TaskStep(type="tool", name="generate_response", description="生成回复"),
            ]

        logger.info(f"Planner generated {len(steps)} steps")
        return {
            "plan": steps,
            "current_task": steps[0] if steps else None,
            "iteration": 0,
        }
    except Exception as e:
        logger.error(f"Planner error: {e}")
        # 降级：默认计划
        plan = [
            TaskStep(type="think", name="分析用户意图"),
            TaskStep(type="tool", name="generate_response"),
            TaskStep(type="think", name="整合回复"),
        ]
        return {
            "plan": plan,
            "current_task": plan[0],
            "iteration": 0,
        }


async def executor_node(state: AgentState) -> dict[str, Any]:
    """执行器节点: 执行当前任务步骤。"""
    task = state.current_task
    if task is None:
        return {"current_task": None, "tool_results": state.tool_results}

    # 人机协同检查：对所有步骤进行风险评估（不只是 tool）
    last_msg = state.messages[-1].content if state.messages else ""
    risk_level = human_in_the_loop.assess_risk(last_msg, tool_name=task.name)
    if human_in_the_loop.requires_manual_approval(risk_level):
        logger.info(f"Human-in-the-loop: blocking {task.name} (risk={risk_level.value})")
        return {
            "tool_results": [
                *state.tool_results,
                {
                    "tool": task.name,
                    "output": f"[人工审批] 该操作需要人工确认（风险级别：{risk_level.value}）",
                },
            ],
            "blocked": True,
            "risk_level": risk_level.value,
        }

    if task.type == "tool":
        # 尝试调用工具
        tool = tool_manager.get(task.name)
        if tool:
            try:
                # 构造工具输入（简化：直接用最后一条消息）
                last_msg = state.messages[-1].content if state.messages else ""
                result = await tool.run(last_msg)
                return {
                    "tool_results": [
                        *state.tool_results,
                        {"tool": task.name, "output": str(result)[:500]},
                    ]
                }
            except Exception as e:
                logger.error(f"Tool {task.name} error: {e}")
                return {
                    "tool_results": [
                        *state.tool_results,
                        {"tool": task.name, "output": f"Error: {e}"},
                    ]
                }
        else:
            # 工具不存在，回退到 LLM 生成
            result = await ai_manager.chat(
                state.provider,
                [
                    {
                        "role": "system",
                        "content": "你是电商智能客服。请根据用户问题提供详细、准确的回答。",
                    },
                    *[
                        {
                            "role": {"human": "user", "ai": "assistant", "system": "system"}.get(
                                m.type, m.type
                            ),
                            "content": m.content,
                        }
                        for m in state.messages
                    ],
                ],
            )
            return {"tool_results": [*state.tool_results, {"tool": "llm", "output": result[:500]}]}
    else:
        logger.info(f"Thinking: {task.name}")
        return {"iteration": state.iteration + 1}


async def reflector_node(state: AgentState) -> dict[str, Any]:
    """反思器节点: 评估执行结果，决定是否需要继续。"""
    # 如果有工具结果，评估质量
    if state.tool_results:
        last_result = state.tool_results[-1].get("output", "")
        # 简单启发式：如果结果太短或包含错误，标记需要重试
        if len(last_result) < 10 or "Error" in last_result:
            logger.info("Reflector: result insufficient, will retry")
            return {"needs_retry": True}

    # 如果迭代次数过多，结束
    if state.iteration >= 3:
        return {"current_task": state.plan[-1] if state.plan else None, "needs_retry": False}

    return {"needs_retry": False}


async def responder_node(state: AgentState) -> dict[str, Any]:
    """回复器节点: 整合结果并生成最终回复。"""
    # 如果有工具结果，基于工具结果生成最终回复
    if state.tool_results:
        last_result = state.tool_results[-1].get("output", "")
        # 如果已经是完整回复，直接使用
        if len(last_result) > 50:
            return {"final_answer": last_result}

    # 否则调用 LLM 生成最终回复
    try:
        response = await ai_manager.chat(
            state.provider,
            [
                {
                    "role": "system",
                    "content": "你是电商智能客服。请基于以下信息，生成友好、专业的最终回复。",
                },
                *[
                    {
                        "role": {"human": "user", "ai": "assistant", "system": "system"}.get(
                            m.type, m.type
                        ),
                        "content": m.content,
                    }
                    for m in state.messages
                ],
                {
                    "role": "assistant",
                    "content": f"执行结果：{state.tool_results[-1].get('output', '') if state.tool_results else '无'}",
                },
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        return {"final_answer": response}
    except Exception as e:
        logger.error(f"Responder error: {e}")
        return {"final_answer": "抱歉，我暂时无法处理您的请求，请稍后重试。"}


def should_continue(state: AgentState) -> str:
    """判断是否继续执行。"""
    if state.needs_retry and state.iteration < 3:
        return "executor"
    if state.iteration >= 3:
        return "responder"
    if not state.plan:
        return "responder"
    return "responder"


__all__ = [
    "executor_node",
    "planner_node",
    "reflector_node",
    "responder_node",
    "should_continue",
]
