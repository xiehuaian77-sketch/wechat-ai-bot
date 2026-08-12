"""Pydantic 模型。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    providers: list[str]


class MessageRequest(BaseModel):
    user_id: str = Field(..., description="微信用户 ID")
    session_id: str = Field(..., description="会话 ID")
    content: str = Field(..., description="消息内容")
    is_group: bool = Field(default=False, description="是否群消息")
    mentioned: bool = Field(default=False, description="是否 @机器人")


class MessageResponse(BaseModel):
    content: str
    model: str | None = None
    tool_calls: list[str] | None = None


class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: dict = Field(default_factory=dict)


class ToolCallResponse(BaseModel):
    success: bool
    output: str
    error: str | None = None


class DocumentUploadRequest(BaseModel):
    title: str
    content: str


class KnowledgeSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)


class KnowledgeSearchResponse(BaseModel):
    results: list[dict]
    total: int


class TicketCreateRequest(BaseModel):
    user_id: str = Field(..., description="微信用户 ID")
    conversation_id: str = Field(..., description="关联会话 ID")
    order_id: str | None = Field(default=None, description="关联订单 ID")
    type: str = Field(default="other", description="工单类型：refund / complaint / inquiry / other")
    priority: str = Field(default="medium", description="优先级：low / medium / high / urgent")
    subject: str = Field(..., description="工单标题")
    description: str | None = Field(default=None, description="工单描述")


class TicketResponse(BaseModel):
    id: str
    type: str
    priority: str
    status: str
    subject: str
    order_id: str | None
    created_at: str


class OrderResponse(BaseModel):
    id: str
    status: str
    total_amount: float | None
    currency: str
    product_info: str | None
    shipping_info: str | None
    created_at: str


class AuditLogResponse(BaseModel):
    id: str
    action: str
    resource_type: str
    resource_id: str | None
    created_at: str


class LoginRequest(BaseModel):
    wechat_id: str = Field(..., description="微信用户 ID")
    nickname: str | None = Field(default=None, description="用户昵称")


class LoginResponse(BaseModel):
    access_token: str
    role: str
    user_id: str


class ApprovalRequest(BaseModel):
    user_id: str
    conversation_id: str
    action: str
    details: dict = Field(default_factory=dict)
    risk_level: str = Field(default="medium", description="low / medium / high / critical")


__all__ = [
    "HealthResponse",
    "MessageRequest",
    "MessageResponse",
    "ToolCallRequest",
    "ToolCallResponse",
    "DocumentUploadRequest",
    "KnowledgeSearchRequest",
    "KnowledgeSearchResponse",
    "TicketCreateRequest",
    "TicketResponse",
    "OrderResponse",
    "AuditLogResponse",
    "LoginRequest",
    "LoginResponse",
    "ApprovalRequest",
]
