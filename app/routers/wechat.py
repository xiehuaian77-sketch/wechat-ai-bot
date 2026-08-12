"""微信 Hook 路由。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from app.services.message.handler import handle_wechat_message

router = APIRouter()


@router.post("/wechat", tags=["wechat"])
async def wechat_hook(request: Request, background_tasks: BackgroundTasks) -> dict[str, Any]:
    """接收 ComWeChatRobot 推送消息。"""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON") from None

    # 异步处理，快速响应
    background_tasks.add_task(handle_wechat_message, payload)
    return {"status": "accepted"}


@router.get("/wechat/test", tags=["wechat"])
async def wechat_test() -> dict[str, str]:
    """Hook 测试端点。"""
    return {"status": "ok", "message": "WeChat hook is ready"}


__all__ = ["router"]
