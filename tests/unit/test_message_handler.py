"""消息处理层单元测试（handler / parse / normalize）。"""

from __future__ import annotations

from typing import Any

import pytest

from app.services.message import handler as handler_module
from app.services.message.handler import (
    handle_admin_command,
    handle_battle_mode,
    handle_file_message,
    handle_image_message,
    handle_text_message,
    handle_upload_command,
    handle_wechat_message,
    normalize_msg_type,
    parse_payload,
)

# =========================================================================
# parse_payload / normalize_msg_type
# =========================================================================


class TestParsePayload:
    def test_standard_format(self):
        payload = {
            "wxid": "wxid_abc",
            "content": "你好",
            "type": "text",
            "room_id": "room_1",
            "nickname": "小明",
        }
        data = parse_payload(payload)
        assert data["wxid"] == "wxid_abc"
        assert data["content"] == "你好"
        assert data["msg_type"] == "text"
        assert data["room_id"] == "room_1"
        assert data["nickname"] == "小明"

    def test_comwechatrobot_aliases(self):
        payload = {
            "from_wxid": "wxid_x",
            "msg": "hello",
            "message_type": "3",
            "from_room_id": "room_9",
            "from_nickname": "小红",
        }
        data = parse_payload(payload)
        assert data["wxid"] == "wxid_x"
        assert data["content"] == "hello"
        assert data["msg_type"] == "image"
        assert data["room_id"] == "room_9"
        assert data["nickname"] == "小红"

    def test_empty_payload_defaults(self):
        data = parse_payload({})
        assert data["wxid"] == ""
        assert data["content"] == ""
        assert data["msg_type"] == "text"
        assert data["room_id"] is None
        assert data["is_at"] is False
        assert data["is_self"] is False


class TestNormalizeMsgType:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("text", "text"),
            ("txt", "text"),
            ("1", "text"),
            ("string", "text"),
            ("image", "image"),
            ("img", "image"),
            ("pic", "image"),
            ("3", "image"),
            ("file", "file"),
            ("attachment", "file"),
            ("6", "file"),
            ("voice", "voice"),
            ("audio", "voice"),
            ("34", "voice"),
            ("video", "video"),
            ("43", "video"),
            ("unknown-type", "text"),
            ("TEXT", "text"),
            ("IMAGE", "image"),
        ],
    )
    def test_normalize(self, raw: str, expected: str):
        assert normalize_msg_type(raw) == expected

    def test_non_string_type(self):
        assert normalize_msg_type(1) == "text"
        assert normalize_msg_type(None) == "text"


# =========================================================================
# send_wechat_message
# =========================================================================


class _FakeResponse:
    def __init__(self, ok: bool = True) -> None:
        self._ok = ok

    def raise_for_status(self) -> None:
        if not self._ok:
            raise RuntimeError("HTTP 500")


class _FakeHttpxClient:
    def __init__(self, ok: bool = True) -> None:
        self._ok = ok
        self.posted: list[dict[str, Any]] = []

    async def __aenter__(self) -> _FakeHttpxClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def post(self, url: str, json: dict[str, Any], headers: dict[str, str]) -> _FakeResponse:
        self.posted.append({"url": url, "json": json})
        return _FakeResponse(ok=self._ok)


@pytest.fixture
def fake_httpx(monkeypatch: pytest.MonkeyPatch) -> _FakeHttpxClient:
    client = _FakeHttpxClient(ok=True)
    monkeypatch.setattr(handler_module.httpx, "AsyncClient", lambda *a, **kw: client)
    return client


@pytest.mark.anyio
async def test_send_wechat_message_success(fake_httpx: _FakeHttpxClient):
    ok = await handler_module.send_wechat_message("wxid_1", "hello")
    assert ok is True
    assert len(fake_httpx.posted) == 1
    assert fake_httpx.posted[0]["json"]["wxid"] == "wxid_1"
    assert fake_httpx.posted[0]["json"]["content"] == "hello"


@pytest.mark.anyio
async def test_send_wechat_message_with_room(fake_httpx: _FakeHttpxClient):
    ok = await handler_module.send_wechat_message("wxid_1", "hello", room_id="room_1")
    assert ok is True
    assert fake_httpx.posted[0]["json"]["room_id"] == "room_1"


@pytest.mark.anyio
async def test_send_wechat_message_failure(monkeypatch: pytest.MonkeyPatch):
    client = _FakeHttpxClient(ok=False)
    monkeypatch.setattr(handler_module.httpx, "AsyncClient", lambda *a, **kw: client)
    ok = await handler_module.send_wechat_message("wxid_1", "hello")
    assert ok is False


# =========================================================================
# 子命令处理
# =========================================================================


@pytest.mark.anyio
async def test_handle_text_message_calls_agent(monkeypatch: pytest.MonkeyPatch):
    sent: list[tuple[str, str]] = []

    async def fake_send(wxid: str, content: str, room_id: str | None = None) -> bool:
        sent.append((wxid, content))
        return True

    class FakeAgentEngine:
        async def run(self, messages: list[dict[str, str]], provider: str) -> dict[str, str]:
            assert provider == "custom"
            return {"final_answer": "这是 AI 的回答"}

    monkeypatch.setattr(handler_module, "send_wechat_message", fake_send)
    monkeypatch.setattr(handler_module.agent_engine, "run", FakeAgentEngine().run)

    await handle_text_message("wxid_1", "你好", None, "小明")
    assert len(sent) == 1
    assert sent[0][0] == "wxid_1"
    assert sent[0][1] == "这是 AI 的回答"


@pytest.mark.anyio
async def test_handle_text_message_agent_error_fallback(monkeypatch: pytest.MonkeyPatch):
    sent: list[str] = []

    async def fake_send(wxid: str, content: str, room_id: str | None = None) -> bool:
        sent.append(content)
        return True

    async def failing_run(self, *args: Any, **kwargs: Any) -> dict[str, str]:
        raise RuntimeError("agent crashed")

    monkeypatch.setattr(handler_module, "send_wechat_message", fake_send)
    monkeypatch.setattr(handler_module.agent_engine, "run", failing_run)

    await handle_text_message("wxid_1", "你好", None, "小明")
    assert len(sent) == 1
    assert "处理失败" in sent[0]


@pytest.mark.anyio
async def test_handle_text_message_battle_command(monkeypatch: pytest.MonkeyPatch):
    called: list[str] = []

    async def fake_battle(wxid: str, content: str, room_id: str | None) -> None:
        called.append(content)

    monkeypatch.setattr(handler_module, "handle_battle_mode", fake_battle)
    await handle_text_message("wxid_1", "@battle 你好", None, "小明")
    assert called == ["@battle 你好"]


@pytest.mark.anyio
async def test_handle_text_message_upload_command(monkeypatch: pytest.MonkeyPatch):
    called: list[str] = []

    async def fake_upload(wxid: str, content: str, room_id: str | None) -> None:
        called.append(content)

    monkeypatch.setattr(handler_module, "handle_upload_command", fake_upload)
    await handle_text_message("wxid_1", "/upload 文档", None, "小明")
    assert called == ["/upload 文档"]


@pytest.mark.anyio
async def test_handle_text_message_admin_command(monkeypatch: pytest.MonkeyPatch):
    called: list[str] = []

    async def fake_admin(wxid: str, content: str, room_id: str | None) -> None:
        called.append(content)

    monkeypatch.setattr(handler_module, "handle_admin_command", fake_admin)
    await handle_text_message("wxid_1", "/admin 列表", None, "小明")
    assert called == ["/admin 列表"]


@pytest.mark.anyio
async def test_handle_image_message_replies_placeholder(monkeypatch: pytest.MonkeyPatch):
    sent: list[tuple[str, str]] = []

    async def fake_send(wxid: str, content: str, room_id: str | None = None) -> bool:
        sent.append((wxid, content))
        return True

    monkeypatch.setattr(handler_module, "send_wechat_message", fake_send)
    await handle_image_message("wxid_1", "file.jpg", None)
    assert len(sent) == 1
    assert "图片" in sent[0][1]


@pytest.mark.anyio
async def test_handle_file_message_replies_placeholder(monkeypatch: pytest.MonkeyPatch):
    sent: list[str] = []

    async def fake_send(wxid: str, content: str, room_id: str | None = None) -> bool:
        sent.append(content)
        return True

    monkeypatch.setattr(handler_module, "send_wechat_message", fake_send)
    await handle_file_message("wxid_1", "a.pdf", None)
    assert len(sent) == 1
    assert "文件" in sent[0]


@pytest.mark.anyio
async def test_handle_upload_command_replies_placeholder(monkeypatch: pytest.MonkeyPatch):
    sent: list[str] = []

    async def fake_send(wxid: str, content: str, room_id: str | None = None) -> bool:
        sent.append(content)
        return True

    monkeypatch.setattr(handler_module, "send_wechat_message", fake_send)
    await handle_upload_command("wxid_1", "/upload x.pdf", None)
    assert len(sent) == 1
    assert "知识库" in sent[0]


@pytest.mark.anyio
async def test_handle_admin_command_replies_panel(monkeypatch: pytest.MonkeyPatch):
    sent: list[str] = []

    async def fake_send(wxid: str, content: str, room_id: str | None = None) -> bool:
        sent.append(content)
        return True

    monkeypatch.setattr(handler_module, "send_wechat_message", fake_send)
    await handle_admin_command("wxid_1", "/admin 列表", None)
    assert len(sent) == 1
    assert "admin" in sent[0].lower()


@pytest.mark.anyio
async def test_handle_battle_mode_full_command(monkeypatch: pytest.MonkeyPatch):
    sent: list[str] = []

    async def fake_send(wxid: str, content: str, room_id: str | None = None) -> bool:
        sent.append(content)
        return True

    async def fake_chat(
        provider_name: str, messages: list[dict[str, str]], model: str | None = None
    ) -> str:
        return f"reply-from-{model}"

    monkeypatch.setattr(handler_module, "send_wechat_message", fake_send)
    monkeypatch.setattr(handler_module.ai_manager, "chat", fake_chat)
    # handler 内部 `from app.services.ai.factory import ProviderFactory`，
    # 因此 patch factory 模块的属性
    import app.services.ai.factory as factory_module

    monkeypatch.setattr(
        factory_module.ProviderFactory, "resolve_model", staticmethod(lambda m: ("openai", m))
    )

    await handle_battle_mode("wxid_1", "@battle gpt-4o vs deepseek-chat: 谁更聪明？", None)
    assert len(sent) == 1
    assert "⚔️ Battle Mode" in sent[0]
    assert "gpt-4o" in sent[0]
    assert "deepseek-chat" in sent[0]


@pytest.mark.anyio
async def test_handle_battle_mode_short_command(monkeypatch: pytest.MonkeyPatch):
    sent: list[str] = []

    async def fake_send(wxid: str, content: str, room_id: str | None = None) -> bool:
        sent.append(content)
        return True

    async def fake_chat(
        provider_name: str, messages: list[dict[str, str]], model: str | None = None
    ) -> str:
        return f"reply-from-{model}"

    monkeypatch.setattr(handler_module, "send_wechat_message", fake_send)
    monkeypatch.setattr(handler_module.ai_manager, "chat", fake_chat)
    import app.services.ai.factory as factory_module

    monkeypatch.setattr(
        factory_module.ProviderFactory, "resolve_model", staticmethod(lambda m: ("openai", m))
    )

    await handle_battle_mode("wxid_1", "battle 今天天气怎么样", None)
    assert len(sent) == 1
    assert "⚔️ Battle Mode" in sent[0]


# =========================================================================
# handle_wechat_message 主流程
# =========================================================================


@pytest.mark.anyio
async def test_handle_wechat_message_permission_denied(monkeypatch: pytest.MonkeyPatch):
    sent: list[str] = []

    async def fake_send(wxid: str, content: str, room_id: str | None = None) -> bool:
        sent.append(content)
        return True

    monkeypatch.setattr(handler_module, "send_wechat_message", fake_send)
    monkeypatch.setattr(
        handler_module,
        "check_permission",
        lambda wxid, room_id: (False, "您不在白名单中，无法使用"),
    )

    await handle_wechat_message({"wxid": "wxid_x", "content": "hi", "type": "text"})
    assert len(sent) == 1
    assert "白名单" in sent[0]


@pytest.mark.anyio
async def test_handle_wechat_message_text_flow(monkeypatch: pytest.MonkeyPatch):
    sent: list[str] = []

    async def fake_send(wxid: str, content: str, room_id: str | None = None) -> bool:
        sent.append(content)
        return True

    async def fake_run(messages: list[dict[str, str]], provider: str) -> dict[str, str]:
        return {"final_answer": "OK!"}

    monkeypatch.setattr(handler_module, "send_wechat_message", fake_send)
    monkeypatch.setattr(handler_module, "check_permission", lambda wxid, room_id: (True, "OK"))
    monkeypatch.setattr(handler_module.agent_engine, "run", fake_run)

    await handle_wechat_message({"wxid": "wxid_1", "content": "你好", "type": "text"})
    assert len(sent) == 1
    assert sent[0] == "OK!"


@pytest.mark.anyio
async def test_handle_wechat_message_image_flow(monkeypatch: pytest.MonkeyPatch):
    sent: list[str] = []

    async def fake_send(wxid: str, content: str, room_id: str | None = None) -> bool:
        sent.append(content)
        return True

    monkeypatch.setattr(handler_module, "send_wechat_message", fake_send)
    monkeypatch.setattr(handler_module, "check_permission", lambda wxid, room_id: (True, "OK"))

    await handle_wechat_message({"wxid": "wxid_1", "content": "a.jpg", "type": "3"})
    assert len(sent) == 1
    assert "图片" in sent[0]


@pytest.mark.anyio
async def test_handle_wechat_message_unsupported_type(monkeypatch: pytest.MonkeyPatch):
    sent: list[str] = []

    async def fake_send(wxid: str, content: str, room_id: str | None = None) -> bool:
        sent.append(content)
        return True

    monkeypatch.setattr(handler_module, "send_wechat_message", fake_send)
    monkeypatch.setattr(handler_module, "check_permission", lambda wxid, room_id: (True, "OK"))

    # voice 类型目前无处理分支，不应发送消息
    await handle_wechat_message({"wxid": "wxid_1", "content": "voice.mp3", "type": "34"})
    assert len(sent) == 0


@pytest.mark.anyio
async def test_handle_wechat_message_exception_is_swallowed(monkeypatch: pytest.MonkeyPatch):
    async def boom(wxid: str, content: str, room_id: str | None = None) -> bool:
        raise RuntimeError("network down")

    monkeypatch.setattr(handler_module, "send_wechat_message", boom)
    monkeypatch.setattr(
        handler_module,
        "check_permission",
        lambda wxid, room_id: (_ for _ in ()).throw(RuntimeError("permission check crashed")),
    )

    # 异常应被捕获，不抛出
    await handle_wechat_message({"wxid": "wxid_1", "content": "hi", "type": "text"})
