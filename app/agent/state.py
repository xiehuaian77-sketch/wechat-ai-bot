"""Agent 状态定义。"""
from __future__ import annotations

from typing import Any, Literal, Optional, Sequence

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


class TaskStep(BaseModel):
    """任务步骤。"""

    type: Literal["tool", "think"] = Field(..., description="步骤类型")
    name: str = Field(..., description="工具名称或推理内容")
    status: Literal["pending", "running", "done", "failed"] = Field(
        default="pending", description="步骤状态"
    )
    result: Optional[str] = Field(default=None, description="执行结果")
    latency_ms: Optional[int] = Field(default=None, description="执行耗时")
    tokens_used: Optional[int] = Field(default=None, description="Token 消耗")


class AgentState(BaseModel):
    """LangGraph Agent 状态。"""

    messages: list[BaseMessage] = Field(default_factory=list, description="对话历史")
    plan: list[TaskStep] = Field(default_factory=list, description="任务计划")
    current_task: Optional[TaskStep] = Field(default=None, description="当前任务")
    tool_results: list[dict[str, Any]] = Field(default_factory=list, description="工具执行结果")
    iteration: int = Field(default=0, description="当前迭代次数")
    final_answer: Optional[str] = Field(default=None, description="最终回复")
    needs_retry: bool = Field(default=False, description="是否需要重试")
    provider: str = Field(default="openai", description="AI 提供商名称")
    latency_ms: Optional[int] = Field(default=None, description="总响应耗时")
    tokens_used: Optional[int] = Field(default=None, description="总 Token 消耗")
    tool_success_rate: Optional[float] = Field(default=None, description="工具成功率")
    blocked: Optional[bool] = Field(default=False, description="是否被人机协同拦截")
    risk_level: Optional[str] = Field(default=None, description="风险级别")


__all__ = ["AgentState", "TaskStep"]
