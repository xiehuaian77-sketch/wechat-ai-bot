"""数据库 ORM 模型。"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy import UUID
from app.database.session import Base


class User(Base):
    """用户表（客户/客服/管理员）。"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wechat_id = Column(String(128), nullable=False, unique=True, index=True)
    nickname = Column(String(128), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    role = Column(String(32), nullable=False, default="customer", index=True)  # customer / agent / admin
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Conversation(Base):
    """对话会话表。"""

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(128), nullable=False, index=True)
    status = Column(String(32), default="active", nullable=False, index=True)  # active / closed / transferred
    assigned_agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    context = Column(Text, nullable=True)  # JSON：用户画像、当前场景、意图等
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True, index=True)


class Message(Base):
    """消息记录表。"""

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(32), nullable=False, index=True)  # user / assistant / system / tool
    content = Column(Text, nullable=False)
    model = Column(String(128), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    tool_calls = Column(Text, nullable=True)  # JSON
    extra_metadata = Column(Text, nullable=True)  # JSON：置信度、来源、rag 等
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class Ticket(Base):
    """售后工单表。"""

    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    order_id = Column(String(64), nullable=True, index=True)
    type = Column(String(32), nullable=False, index=True)  # refund / complaint / inquiry / other
    priority = Column(String(16), default="medium", nullable=False, index=True)  # low / medium / high / urgent
    status = Column(String(32), default="open", nullable=False, index=True)  # open / pending / resolved / closed
    subject = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    resolution = Column(Text, nullable=True)
    assigned_agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    satisfaction_score = Column(Integer, nullable=True)  # 1-5
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Order(Base):
    """电商订单表（简化）。"""

    __tablename__ = "orders"

    id = Column(String(64), primary_key=True, unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(32), default="created", nullable=False, index=True)  # created / paid / shipped / completed / cancelled
    total_amount = Column(Float, nullable=True)
    currency = Column(String(16), default="CNY")
    product_info = Column(Text, nullable=True)  # JSON：商品摘要
    shipping_info = Column(Text, nullable=True)  # JSON：地址摘要
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class KnowledgeDocument(Base):
    """知识库文档表。"""

    __tablename__ = "knowledge_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(256), nullable=False, index=True)
    source = Column(String(512), nullable=True)
    category = Column(String(64), nullable=True, index=True)
    chunk_count = Column(Integer, default=0)
    embedding_model = Column(String(128), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ToolCallLog(Base):
    """工具调用日志表。"""

    __tablename__ = "tool_call_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)
    tool_name = Column(String(128), nullable=False, index=True)
    arguments = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    success = Column(Boolean, default=True, nullable=False, index=True)
    duration_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class AuditLog(Base):
    """审计日志表。"""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(64), nullable=False, index=True)  # create / update / delete / transfer / resolve
    resource_type = Column(String(64), nullable=False, index=True)  # conversation / ticket / order / knowledge
    resource_id = Column(String(128), nullable=True, index=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(256), nullable=True)
    changes = Column(Text, nullable=True)  # JSON：变更前后
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


__all__ = [
    "Base",
    "User",
    "Conversation",
    "Message",
    "Ticket",
    "Order",
    "KnowledgeDocument",
    "ToolCallLog",
    "AuditLog",
]
