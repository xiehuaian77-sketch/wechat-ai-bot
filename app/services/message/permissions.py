"""消息权限控制。"""
from __future__ import annotations

from config.settings import settings


def check_permission(wxid: str, room_id: str | None) -> tuple[bool, str]:
    """检查消息发送者是否有权限使用 Bot。

    Returns:
        (allowed, reason)
    """
    # 检查黑名单
    if room_id and settings.GROUP_BLACKLIST:
        blacklisted = [g.strip() for g in settings.GROUP_BLACKLIST.split(",") if g.strip()]
        if room_id in blacklisted:
            return False, "该群已被拉黑"

    # 检查白名单（如果配置了白名单，只有白名单用户可用）
    if settings.ADMIN_WHITELIST:
        whitelisted = [w.strip() for w in settings.ADMIN_WHITELIST.split(",") if w.strip()]
        if wxid not in whitelisted:
            return False, "您不在白名单中，无法使用"

    return True, "OK"


__all__ = ["check_permission"]
