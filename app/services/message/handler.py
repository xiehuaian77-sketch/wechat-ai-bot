"""微信消息处理。"""
from __future__ import annotations

import time
from typing import Any

import httpx
from app.agent.engine import agent_engine
from app.services.ai.manager import ai_manager
from app.services.message.permissions import check_permission
from app.utils.logger import logger
from config.settings import settings

# ComWeChatRobot HTTP Hook 配置（从 .env 加载）
WECHAT_HOOK_URL = str(settings.WECHAT_HOOK_URL)
WECHAT_HOOK_SECRET = settings.WECHAT_HOOK_SECRET.get_secret_value()


async def send_wechat_message(wxid: str, content: str, room_id: str | None = None) -> bool:
    """通过 ComWeChatRobot 发送微信消息。"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "wxid": wxid,
                "content": content,
                "at": [],
            }
            if room_id:
                payload["room_id"] = room_id

            response = await client.post(
                f"{WECHAT_HOOK_URL}/api/send/text",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            logger.info(f"Sent message to {wxid}: {content[:50]}...")
            return True
    except Exception as e:
        logger.error(f"Failed to send message to {wxid}: {e}")
        return False


async def handle_wechat_message(payload: dict[str, Any]) -> None:
    """处理 ComWeChatRobot 推送的微信消息。"""
    start_time = time.time()

    try:
        # 1. 解析消息字段（兼容 ComWeChatRobot 格式）
        msg_data = parse_payload(payload)
        wxid = msg_data["wxid"]
        content = msg_data["content"]
        msg_type = msg_data["msg_type"]
        room_id = msg_data.get("room_id")
        nickname = msg_data.get("nickname", "Unknown")

        logger.info(f"[{msg_type}] {nickname}({wxid}): {content[:100]}")

        # 2. 权限检查
        allowed, reason = check_permission(wxid, room_id)
        if not allowed:
            await send_wechat_message(wxid, f"⛔ {reason}")
            return

        # 3. 根据消息类型处理
        if msg_type == "text":
            await handle_text_message(wxid, content, room_id, nickname)
        elif msg_type == "image":
            await handle_image_message(wxid, content, room_id)
        elif msg_type == "file":
            await handle_file_message(wxid, content, room_id)
        else:
            logger.info(f"Ignored unsupported message type: {msg_type}")

    except Exception as e:
        logger.error(f"Error handling wechat message: {e}", exc_info=True)

    elapsed = time.time() - start_time
    logger.info(f"Message processed in {elapsed:.2f}s")


def parse_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """解析 ComWeChatRobot Hook payload。"""
    # ComWeChatRobot 消息格式（常见字段）
    return {
        "wxid": payload.get("wxid") or payload.get("from_wxid") or payload.get("sender", ""),
        "content": payload.get("content") or payload.get("msg") or payload.get("text", ""),
        "msg_type": normalize_msg_type(payload.get("type") or payload.get("msg_type") or payload.get("message_type", "text")),
        "room_id": payload.get("room_id") or payload.get("from_room_id"),
        "nickname": payload.get("nickname") or payload.get("from_nickname") or "",
        "is_at": payload.get("is_at", False),
        "is_self": payload.get("is_self", False),
    }


def normalize_msg_type(raw_type: Any) -> str:
    """标准化消息类型。"""
    if isinstance(raw_type, str):
        t = raw_type.lower()
        if t in ("text", "txt", "1", "string"):
            return "text"
        if t in ("image", "img", "pic", "3"):
            return "image"
        if t in ("file", "attachment", "6"):
            return "file"
        if t in ("voice", "audio", "34"):
            return "voice"
        if t in ("video", "43"):
            return "video"
    return "text"


async def handle_text_message(wxid: str, content: str, room_id: str | None, nickname: str) -> None:
    """处理文本消息。"""
    # 检测 Battle Mode 命令
    if content.startswith("@battle ") or content.startswith("battle "):
        await handle_battle_mode(wxid, content, room_id)
        return

    # 检测知识库上传命令
    if content.startswith("/upload ") or content.startswith("上传"):
        await handle_upload_command(wxid, content, room_id)
        return

    # 检测管理命令
    if content.startswith("/admin ") or content.startswith("管理"):
        await handle_admin_command(wxid, content, room_id)
        return

    # 普通对话：调用 AI Agent
    try:
        # 构建消息历史（简化版：单轮对话）
        messages = [{"role": "user", "content": content}]

        # 调用 Agent 引擎（使用 custom provider）
        result = await agent_engine.run(messages, provider="custom")

        reply = result.get("final_answer", "抱歉，我暂时无法回答这个问题。")
        await send_wechat_message(wxid, reply, room_id)

    except Exception as e:
        logger.error(f"AI chat error: {e}")
        await send_wechat_message(wxid, "⚠️ 处理失败，请稍后重试或联系客服。", room_id)


async def handle_battle_mode(wxid: str, content: str, room_id: str | None) -> None:
    """处理 Battle Mode 双模型对战。"""
    # 解析命令：@battle ModelA vs ModelB: 问题
    try:
        # 简单解析逻辑
        body = content.replace("@battle ", "").replace("battle ", "", 1)
        if ":" in body:
            models_part, question = body.split(":", 1)
            models = models_part.split("vs")
            model_a = models[0].strip() if len(models) > 0 else "gpt-4o-mini"
            model_b = models[1].strip() if len(models) > 1 else "deepseek-chat"
        else:
            question = body
            model_a = "gpt-4o-mini"
            model_b = "deepseek-chat"

        # 并行调用两个模型（默认使用 custom provider）
        import asyncio
        from app.services.ai.factory import ProviderFactory

        def resolve_target(model_name: str) -> tuple[str, str]:
            try:
                return ProviderFactory.resolve_model(model_name)
            except Exception:
                return ("custom", model_name)

        provider_a, model_a_resolved = resolve_target(model_a)
        provider_b, model_b_resolved = resolve_target(model_b)

        results = await asyncio.gather(
            ai_manager.chat(provider_a, [{"role": "user", "content": question}], model=model_a_resolved),
            ai_manager.chat(provider_b, [{"role": "user", "content": question}], model=model_b_resolved),
            return_exceptions=True,
        )

        reply_a = results[0].result() if not isinstance(results[0], Exception) else str(results[0])
        reply_b = results[1].result() if not isinstance(results[1], Exception) else str(results[1])

        response = f"⚔️ Battle Mode\n\n🤖 {model_a}:\n{reply_a[:200]}...\n\n🤖 {model_b}:\n{reply_b[:200]}...\n\n请回复 A 或 B 投票！"
        await send_wechat_message(wxid, response, room_id)

    except Exception as e:
        logger.error(f"Battle mode error: {e}")
        await send_wechat_message(wxid, "⚠️ Battle Mode 失败，请稍后重试。", room_id)


async def handle_image_message(wxid: str, content: str, room_id: str | None) -> None:
    """处理图片消息（TODO：接入多模态 Vision）。"""
    await send_wechat_message(wxid, "🖼️ 图片消息已收到，多模态识别功能开发中...", room_id)


async def handle_file_message(wxid: str, content: str, room_id: str | None) -> None:
    """处理文件消息。"""
    await send_wechat_message(wxid, "📎 文件消息已收到，RAG 知识库功能开发中...", room_id)


async def handle_upload_command(wxid: str, content: str, room_id: str | None) -> None:
    """处理知识库上传命令。"""
    await send_wechat_message(wxid, "📚 知识库上传功能开发中，请通过管理面板上传文档。", room_id)


async def handle_admin_command(wxid: str, content: str, room_id: str | None) -> None:
    """处理管理命令。"""
    await send_wechat_message(wxid, "🔧 管理面板：http://localhost:8000/admin", room_id)


__all__ = ["handle_wechat_message", "send_wechat_message"]
