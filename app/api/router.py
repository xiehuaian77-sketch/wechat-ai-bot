"""管理 API 路由。"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from app.agent.engine import agent_engine
from app.agent.human_in_the_loop import human_in_the_loop, RiskLevel
from app.auth import (
    create_access_token,
    get_current_active_user,
    require_agent,
    require_admin,
    require_customer,
    require_roles,
)
from app.database.models import AuditLog, Conversation, Message, Ticket, ToolCallLog, User
from app.database.session import get_session
from app.knowledge.vector_store import knowledge_store
from app.models.schemas import (
    ApprovalRequest,
    DocumentUploadRequest,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    LoginRequest,
    LoginResponse,
    MessageRequest,
    MessageResponse,
    ToolCallRequest,
    ToolCallResponse,
)
from app.tools import tool_manager
from sqlalchemy import select, insert, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


# ============================================================================
# 数据库辅助函数
# ============================================================================

async def _get_or_create_user(session: AsyncSession, wechat_id: str, nickname: str | None = None) -> User:
    """根据微信 ID 获取或创建用户。"""
    result = await session.execute(select(User).where(User.wechat_id == wechat_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(wechat_id=wechat_id, nickname=nickname, role="customer")
        session.add(user)
        await session.flush()
    return user


async def _get_or_create_conversation(session: AsyncSession, user_id: uuid.UUID, session_id: str) -> Conversation:
    """获取或创建对话会话。"""
    result = await session.execute(
        select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.session_id == session_id,
            Conversation.status == "active",
        )
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        conv = Conversation(user_id=user_id, session_id=session_id, status="active")
        session.add(conv)
        await session.flush()
    return conv


async def _save_message(
    session: AsyncSession,
    conversation_id: uuid.UUID,
    role: str,
    content: str,
    model: str | None = None,
    tokens_used: int | None = None,
    latency_ms: int | None = None,
    tool_calls: str | None = None,
    extra_metadata: str | None = None,
) -> Message:
    """保存消息到数据库。"""
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        model=model,
        tokens_used=tokens_used,
        latency_ms=latency_ms,
        tool_calls=tool_calls,
        extra_metadata=extra_metadata,
    )
    session.add(msg)
    await session.flush()
    return msg


# ============================================================================
# 认证 API
# ============================================================================


@router.post("/auth/login", tags=["auth"], response_model=LoginResponse)
async def login(request: LoginRequest, session: AsyncSession = Depends(get_session)) -> LoginResponse:
    """微信用户登录（获取 JWT Token）。"""
    user = await _get_or_create_user(session, request.wechat_id, request.nickname)
    token = create_access_token(user.id, user.wechat_id, user.role)
    return LoginResponse(access_token=token, role=user.role, user_id=str(user.id))


# ============================================================================
# 聊天 API
# ============================================================================

@router.get("/chat/history", tags=["chat"])
async def get_chat_history(
    user_id: str,
    session_id: str,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """获取聊天历史。"""
    # 获取用户
    user_result = await session.execute(select(User).where(User.wechat_id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        return {"messages": [], "total": 0}

    # 获取会话
    conv_result = await session.execute(
        select(Conversation).where(
            Conversation.user_id == user.id,
            Conversation.session_id == session_id,
            Conversation.status == "active",
        )
    )
    conv = conv_result.scalar_one_or_none()
    if conv is None:
        return {"messages": [], "total": 0}

    # 获取消息
    msgs_result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.asc())
        .limit(limit)
    )
    messages = [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "model": m.model,
            "tokens_used": m.tokens_used,
            "latency_ms": m.latency_ms,
            "tool_calls": m.tool_calls,
            "metadata": m.extra_metadata,
            "created_at": m.created_at.isoformat(),
        }
        for m in msgs_result.scalars().all()
    ]
    return {"messages": messages, "total": len(messages)}


@router.post("/chat", tags=["chat"], response_model=MessageResponse)
async def chat_message(
    request: MessageRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """发送聊天消息。"""
    # 1. 根据 wechat_id 获取或创建用户
    user = await _get_or_create_user(session, request.user_id, getattr(request, "nickname", None))

    # 2. 获取或创建会话
    conv = await _get_or_create_conversation(session, user.id, request.session_id)

    # 3. 保存用户消息
    await _save_message(session, conv.id, "user", request.content)

    try:
        # 上下文工程：注入用户记忆 + 知识库检索
        from app.context import UserMemory, KnowledgeBase

        user_memory = await UserMemory.get_user_memory(str(user.id))
        knowledge_docs = await KnowledgeBase.search(request.content, top_k=2)
        knowledge_context = "\n\n".join([d["content"] for d in knowledge_docs]) if knowledge_docs else None

        # 4. 调用 Agent（带上下文）
        messages = [{"role": "user", "content": request.content}]
        result = await agent_engine.run(
            messages,
            provider="custom",
            user_memory=user_memory,
            knowledge_context=knowledge_context,
        )

        reply = result.get("final_answer", "")
        model_used = None
        tool_results = result.get("tool_results", [])
        latency_ms = result.get("latency_ms")
        tokens_used = result.get("tokens_used")

        # 序列化 tool_calls（转为字符串列表）
        tool_calls_serialized = [str(t) for t in tool_results] if tool_results else None

        # 保存 AI 回复
        await _save_message(
            session,
            conv.id,
            "assistant",
            reply,
            model=model_used,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            tool_calls=str(tool_results) if tool_results else None,
            extra_metadata=None,
        )

        return MessageResponse(
            content=reply,
            model=model_used,
            tool_calls=tool_calls_serialized,
        )
    except Exception as e:
        await session.rollback()
        logger.error(f"[/api/chat] error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误，请稍后重试",
        )


@router.post("/tools/call", tags=["tools"])
async def call_tool(
    request: ToolCallRequest,
    current_user: User = Depends(get_current_active_user),
) -> ToolCallResponse:
    """手动调用工具。"""
    result = await tool_manager.execute(request.tool_name, request.arguments)
    return ToolCallResponse(
        success=result.success,
        output=result.output,
        error=result.error,
    )


@router.post("/knowledge/upload", tags=["knowledge"])
async def upload_document(
    request: DocumentUploadRequest,
    current_user: User = Depends(require_agent),
) -> dict[str, str]:
    """上传知识库文档。"""
    await knowledge_store.add_documents(
        documents=[request.content],
        metadatas=[{"title": request.title, "source": "api"}],
    )
    return {"status": "ok", "message": f"文档「{request.title}」已上传"}


@router.post("/knowledge/search", tags=["knowledge"])
async def search_knowledge(
    request: KnowledgeSearchRequest,
    current_user: User = Depends(get_current_active_user),
) -> KnowledgeSearchResponse:
    """检索知识库。"""
    raw = await knowledge_store.search(request.query, top_k=request.top_k)
    results = [
        {"content": item["text"], "score": item["score"]}
        for item in raw
    ]
    return KnowledgeSearchResponse(results=results, total=len(results))


@router.get("/admin/whitelist", tags=["admin"])
async def get_whitelist(
    current_user: User = Depends(require_admin),
) -> dict[str, list[str]]:
    """获取管理员白名单。"""
    from config.settings import settings
    items = [w.strip() for w in settings.ADMIN_WHITELIST.split(",") if w.strip()]
    return {"whitelist": items}


@router.post("/admin/whitelist", tags=["admin"])
async def update_whitelist(
    wxids: list[str],
    current_user: User = Depends(require_admin),
) -> dict[str, str]:
    """更新管理员白名单。"""
    from config.settings import settings
    import pathlib

    settings.ADMIN_WHITELIST = ",".join(wxids)

    # 写回 .env
    env_path = pathlib.Path(".env")
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
        new_lines = []
        found = False
        for line in lines:
            if line.startswith("ADMIN_WHITELIST="):
                new_lines.append(f"ADMIN_WHITELIST={','.join(wxids)}")
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f"ADMIN_WHITELIST={','.join(wxids)}")
        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    return {"status": "ok", "count": len(wxids)}


@router.get("/admin/blacklist", tags=["admin"])
async def get_blacklist(
    current_user: User = Depends(require_admin),
) -> dict[str, list[str]]:
    """获取群黑名单。"""
    from config.settings import settings
    items = [g.strip() for g in settings.GROUP_BLACKLIST.split(",") if g.strip()]
    return {"blacklist": items}


@router.post("/admin/blacklist", tags=["admin"])
async def update_blacklist(
    group_ids: list[str],
    current_user: User = Depends(require_admin),
) -> dict[str, str]:
    """更新群黑名单。"""
    from config.settings import settings
    import pathlib

    settings.GROUP_BLACKLIST = ",".join(group_ids)

    # 写回 .env
    env_path = pathlib.Path(".env")
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
        new_lines = []
        found = False
        for line in lines:
            if line.startswith("GROUP_BLACKLIST="):
                new_lines.append(f"GROUP_BLACKLIST={','.join(group_ids)}")
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f"GROUP_BLACKLIST={','.join(group_ids)}")
        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    return {"status": "ok", "count": len(group_ids)}


# ============================================================================
# 工单 API
# ============================================================================

@router.post("/tickets", tags=["tickets"])
async def create_ticket(
    request: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_agent),
) -> dict[str, Any]:
    """创建售后工单。"""
    try:
        user_id = uuid.UUID(request.get("user_id"))
        conversation_id = uuid.UUID(request.get("conversation_id"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid user_id or conversation_id")

    ticket = Ticket(
        conversation_id=conversation_id,
        user_id=user_id,
        order_id=request.get("order_id"),
        type=request.get("type", "other"),
        priority=request.get("priority", "medium"),
        subject=request.get("subject", ""),
        description=request.get("description"),
    )
    session.add(ticket)
    await session.flush()

    # 审计日志
    await _create_audit_log(
        session,
        actor_id=user_id,
        action="create",
        resource_type="ticket",
        resource_id=str(ticket.id),
        changes={"type": ticket.type, "priority": ticket.priority},
    )

    return {"id": str(ticket.id), "status": ticket.status, "created_at": ticket.created_at.isoformat()}


@router.get("/tickets", tags=["tickets"])
async def list_tickets(
    status: str | None = None,
    priority: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_agent),
) -> dict[str, Any]:
    """查询工单列表。"""
    query = select(Ticket).order_by(Ticket.created_at.desc())
    if status:
        query = query.where(Ticket.status == status)
    if priority:
        query = query.where(Ticket.priority == priority)

    result = await session.execute(query)
    tickets = result.scalars().all()
    return {
        "items": [
            {
                "id": str(t.id),
                "type": t.type,
                "priority": t.priority,
                "status": t.status,
                "subject": t.subject,
                "order_id": t.order_id,
                "created_at": t.created_at.isoformat(),
            }
            for t in tickets
        ],
        "total": len(tickets),
    }


@router.post("/tickets/{ticket_id}/resolve", tags=["tickets"])
async def resolve_ticket(
    ticket_id: str,
    request: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_agent),
) -> dict[str, Any]:
    """解决工单。"""
    try:
        t_id = uuid.UUID(ticket_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ticket_id")

    result = await session.execute(select(Ticket).where(Ticket.id == t_id))
    ticket = result.scalar_one_or_none()
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = "resolved"
    ticket.resolution = request.get("resolution")
    ticket.resolved_at = datetime.utcnow()
    await session.flush()

    # 审计日志
    await _create_audit_log(
        session,
        actor_id=current_user.id,
        action="resolve",
        resource_type="ticket",
        resource_id=str(ticket.id),
        changes={"status": "resolved", "resolution": request.get("resolution")},
    )

    return {"id": str(ticket.id), "status": ticket.status, "resolved_at": ticket.resolved_at.isoformat()}


# ============================================================================
# 人机协同 API
# ============================================================================


@router.post("/human-in-the-loop/request", tags=["human-in-the-loop"])
async def request_manual_approval(
    request: ApprovalRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """创建人工审批请求（Agent 调用）。"""
    try:
        risk_level = RiskLevel(request.risk_level)
    except ValueError:
        risk_level = RiskLevel.MEDIUM

    user_id = uuid.UUID(request.user_id) if request.user_id else current_user.id
    conversation_id = uuid.UUID(request.conversation_id) if request.conversation_id else None

    if conversation_id is None:
        raise HTTPException(status_code=400, detail="conversation_id is required")

    result = await human_in_the_loop.create_approval_request(
        session=session,
        user_id=user_id,
        conversation_id=conversation_id,
        action=request.action,
        details=request.details,
        risk_level=risk_level,
    )
    return result


# ============================================================================
# 订单 API
# ============================================================================

@router.get("/orders/{order_id}", tags=["orders"])
async def get_order(
    order_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_agent),
) -> dict[str, Any]:
    """查询订单信息。"""
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "id": order.id,
        "status": order.status,
        "total_amount": order.total_amount,
        "currency": order.currency,
        "product_info": order.product_info,
        "shipping_info": order.shipping_info,
        "created_at": order.created_at.isoformat(),
    }


# ============================================================================
# 审计日志 API
# ============================================================================

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


@router.get("/audit/logs", tags=["audit"])
async def list_audit_logs(
    resource_type: str | None = None,
    action: str | None = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    """查询审计日志。"""
    query = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if action:
        query = query.where(AuditLog.action == action)

    result = await session.execute(query)
    logs = result.scalars().all()
    return {
        "items": [
            {
                "id": str(l.id),
                "action": l.action,
                "resource_type": l.resource_type,
                "resource_id": l.resource_id,
                "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ],
        "total": len(logs),
    }


@router.get("/observability/metrics", tags=["observability"])
async def get_observability_metrics(
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    """获取可观测性指标（仪表盘用）。"""
    # 消息统计
    msgs_result = await session.execute(select(Message))
    messages = msgs_result.scalars().all()
    total_conversations = len({m.conversation_id for m in messages})
    total_tokens = sum(m.tokens_used or 0 for m in messages if m.tokens_used)
    latencies = [m.latency_ms for m in messages if m.latency_ms]
    avg_latency = int(sum(latencies) / len(latencies)) if latencies else None

    # 工具成功率：基于 ToolCallLog 表准确统计
    tool_logs_result = await session.execute(select(ToolCallLog))
    tool_logs = tool_logs_result.scalars().all()
    if tool_logs:
        success_count = sum(1 for log in tool_logs if log.success)
        tool_success_rate = round(success_count / len(tool_logs), 2)
    else:
        tool_success_rate = 1.0

    # 最近追踪：按消息时间倒序
    recent = []
    for m in sorted(messages, key=lambda x: x.created_at, reverse=True)[:limit]:
        if m.role == "assistant":
            # 获取该消息关联的工具调用日志
            tool_logs_for_msg = [log for log in tool_logs if log.message_id == m.id]
            msg_tool_success_rate = (
                round(sum(1 for log in tool_logs_for_msg if log.success) / len(tool_logs_for_msg), 2)
                if tool_logs_for_msg else None
            )
            recent.append({
                "conversation_id": str(m.conversation_id),
                "user_id": str(m.id),
                "model": m.model,
                "tool_calls": len(m.tool_calls.split(";")) if m.tool_calls else 0,
                "latency_ms": m.latency_ms,
                "tokens_used": m.tokens_used,
                "tool_success_rate": msg_tool_success_rate,
                "status": "blocked" if "人工" in (m.tool_calls or "") else "done",
            })

    return {
        "total_conversations": total_conversations,
        "avg_latency_ms": avg_latency,
        "tool_success_rate": tool_success_rate,
        "total_tokens": total_tokens,
        "recent_traces": recent,
    }


__all__ = ["router"]
