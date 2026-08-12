"""JWT 认证与权限管理。"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.database.models import User
from config.settings import settings

# =============================================================================
# 配置
# =============================================================================

SECRET_KEY = settings.JWT_SECRET_KEY.get_secret_value()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 小时

security = HTTPBearer()

# =============================================================================
# 数据模型
# =============================================================================


class TokenData(BaseModel):
    """Token 解析后的负载。"""
    user_id: uuid.UUID
    wechat_id: str
    role: Literal["customer", "agent", "admin"]


# =============================================================================
# JWT 工具函数
# =============================================================================


def _hash_password(password: str) -> str:
    """简单密码哈希（生产环境请使用 bcrypt/argon2）。"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(user_id: uuid.UUID, wechat_id: str, role: str) -> str:
    """创建 JWT Access Token。"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "wechat_id": wechat_id,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> TokenData:
    """解码并校验 JWT Token。"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = uuid.UUID(payload.get("sub"))
        wechat_id = payload.get("wechat_id", "")
        role = payload.get("role", "customer")
        return TokenData(user_id=user_id, wechat_id=wechat_id, role=role)
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# =============================================================================
# FastAPI 依赖注入
# =============================================================================


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> User:
    """获取当前已认证用户（需要 Bearer Token）。"""
    token = credentials.credentials
    token_data = decode_token(token)

    result = await session.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is disabled")
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """确保用户处于 active 状态。"""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def require_roles(*allowed_roles: Literal["customer", "agent", "admin"]):
    """角色权限装饰器工厂。"""

    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' is not allowed",
            )
        return current_user

    return role_checker


# 预定义权限组
require_admin = require_roles("admin")
require_agent = require_roles("agent", "admin")
require_customer = require_roles("customer", "agent", "admin")  # 登录用户即可
