"""人机协同机制：高风险场景人工确认。"""

from __future__ import annotations

import uuid
from enum import StrEnum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AuditLog, Ticket, ToolCallLog

# =============================================================================
# 风险级别定义
# =============================================================================


class RiskLevel(StrEnum):
    """操作风险级别。"""

    LOW = "low"  # 一般咨询，可直接处理
    MEDIUM = "medium"  # 需要记录，可自动处理
    HIGH = "high"  # 高风险，需人工确认
    CRITICAL = "critical"  # 最高风险，必须人工审批


# 高风险场景关键词映射
HIGH_RISK_KEYWORDS: dict[str, RiskLevel] = {
    "退款": RiskLevel.HIGH,
    "退货": RiskLevel.HIGH,
    "投诉": RiskLevel.HIGH,
    "赔偿": RiskLevel.HIGH,
    "个人信息": RiskLevel.CRITICAL,
    "密码": RiskLevel.CRITICAL,
    "银行卡": RiskLevel.CRITICAL,
    "身份证": RiskLevel.CRITICAL,
    "订单取消": RiskLevel.HIGH,
    "发票": RiskLevel.MEDIUM,
    "换货": RiskLevel.HIGH,
    "运费": RiskLevel.MEDIUM,
    "地址修改": RiskLevel.MEDIUM,
}

# =============================================================================
# 人机协同核心逻辑
# =============================================================================


class HumanInTheLoop:
    """人工干预控制器。"""

    def __init__(self) -> None:
        self._pending_confirmations: dict[str, dict[str, Any]] = {}

    def assess_risk(
        self, user_message: str, tool_name: str | None = None, context: str | None = None
    ) -> RiskLevel:
        """评估操作风险级别。"""
        combined = f"{user_message} {context or ''} {tool_name or ''}"
        for keyword, level in HIGH_RISK_KEYWORDS.items():
            if keyword in combined:
                return level
        return RiskLevel.LOW

    def requires_manual_approval(self, risk_level: RiskLevel) -> bool:
        """是否需要人工审批。"""
        return risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    async def create_approval_request(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        action: str,
        details: dict[str, Any],
        risk_level: RiskLevel,
    ) -> dict[str, Any]:
        """创建人工审批请求（创建工单并标记为待审批）。"""
        ticket = Ticket(
            conversation_id=conversation_id,
            user_id=user_id,
            type="inquiry",  # 默认类型，可根据 action 调整
            priority="high" if risk_level == RiskLevel.HIGH else "urgent",
            status="pending",  # 待人工处理
            subject=f"[人工审批] {action}",
            description=f"风险级别：{risk_level.value}\n详情：{details}",
        )
        session.add(ticket)
        await session.flush()

        # 审计日志
        await _create_audit_log(
            session,
            actor_id=user_id,
            action="request_approval",
            resource_type="ticket",
            resource_id=str(ticket.id),
            changes={"action": action, "risk_level": risk_level.value, "details": details},
        )

        return {
            "ticket_id": str(ticket.id),
            "status": "pending_approval",
            "risk_level": risk_level.value,
            "message": f"该操作需要人工审批（风险级别：{risk_level.value}），工单已创建，请等待客服处理。",
        }

    async def record_tool_call(
        self,
        session: AsyncSession,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID | None,
        tool_name: str,
        arguments: dict,
        result: str,
        success: bool,
        duration_ms: int | None,
        error_message: str | None = None,
    ) -> None:
        """记录工具调用日志。"""
        log = ToolCallLog(
            conversation_id=conversation_id,
            message_id=message_id,
            tool_name=tool_name,
            arguments=str(arguments),
            result=result,
            success=success,
            duration_ms=duration_ms,
            error_message=error_message,
        )
        session.add(log)
        await session.flush()


# =============================================================================
# 审计日志辅助
# =============================================================================


async def _create_audit_log(
    session: AsyncSession,
    actor_id: uuid.UUID | None,
    action: str,
    resource_type: str,
    resource_id: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
    changes: dict | None = None,
) -> AuditLog:
    """创建审计日志。"""
    import json

    log = AuditLog(
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        changes=json.dumps(changes, ensure_ascii=False) if changes else None,
    )
    session.add(log)
    await session.flush()
    return log


# 全局实例
human_in_the_loop = HumanInTheLoop()
