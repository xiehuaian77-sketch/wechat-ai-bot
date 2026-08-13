"""AI 服务层单元测试（factory / manager / providers / permissions）。"""

from __future__ import annotations

from typing import Any

import pytest

from app.services.ai.factory import ProviderFactory
from app.services.ai.manager import AIManager
from app.services.message.permissions import check_permission
from config.settings import settings

# =========================================================================
# ProviderFactory
# =========================================================================


class TestProviderFactory:
    def test_resolve_known_provider_name(self):
        assert ProviderFactory.resolve_model("openai") == ("openai", "")
        assert ProviderFactory.resolve_model("deepseek") == ("deepseek", "")
        assert ProviderFactory.resolve_model("custom") == ("custom", "")

    def test_resolve_mapped_model(self):
        assert ProviderFactory.resolve_model("gpt-4o-mini") == ("openai", "gpt-4o-mini")
        assert ProviderFactory.resolve_model("deepseek-chat") == ("deepseek", "deepseek-chat")
        assert ProviderFactory.resolve_model("claude-3-5-haiku-20241022") == (
            "anthropic",
            "claude-3-5-haiku-20241022",
        )

    def test_resolve_unknown_model_defaults_to_openai(self):
        assert ProviderFactory.resolve_model("some-future-model") == ("openai", "some-future-model")

    def test_create_known_provider(self):
        provider = ProviderFactory.create("openai")
        assert provider.name == "openai"

    def test_create_case_insensitive(self):
        provider = ProviderFactory.create("OpenAI")
        assert provider.name == "openai"

    def test_create_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="未知的 AI 提供商"):
            ProviderFactory.create("not-a-provider")

    def test_list_models_groups_by_provider(self):
        models = ProviderFactory.list_models()
        assert isinstance(models, dict)
        assert "openai" in models
        assert "gpt-4o-mini" in models["openai"]
        assert "deepseek-chat" in models["deepseek"]
        # 所有映射值都出现在结果中
        total = sum(len(v) for v in models.values())
        assert total == len(ProviderFactory._model_map)


# =========================================================================
# AIManager
# =========================================================================


class FakeProvider:
    """模拟 AI Provider，用于测试 AIManager 逻辑。"""

    name = "fake"

    def __init__(self, model: str | None = None) -> None:
        self._model = model or "fake-model"
        self.chat_calls: list[dict[str, Any]] = []
        self.stream_calls: list[dict[str, Any]] = []

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        self.chat_calls.append({"messages": messages, **kwargs})
        return "fake reply"

    async def stream_chat(self, messages: list[dict[str, str]], **kwargs: Any):
        self.stream_calls.append({"messages": messages, **kwargs})
        yield "chunk1"
        yield "chunk2"


@pytest.fixture
def fake_ai_manager(monkeypatch: pytest.MonkeyPatch) -> AIManager:
    """创建隔离的 AIManager，并 mock ProviderFactory。"""

    def fake_create(provider_name: str, **kwargs: Any) -> FakeProvider:
        return FakeProvider(model=kwargs.get("model"))

    def fake_resolve_model(model_name: str) -> tuple[str, str]:
        return ("fake", model_name)

    monkeypatch.setattr(ProviderFactory, "create", staticmethod(fake_create))
    monkeypatch.setattr(ProviderFactory, "resolve_model", staticmethod(fake_resolve_model))
    return AIManager()


@pytest.mark.anyio
async def test_manager_get_provider_caches_instance(fake_ai_manager: AIManager):
    p1 = fake_ai_manager.get_provider("fake")
    p2 = fake_ai_manager.get_provider("fake")
    assert p1 is p2


@pytest.mark.anyio
async def test_manager_get_provider_with_model_key(fake_ai_manager: AIManager):
    p1 = fake_ai_manager.get_provider("fake", "model-a")
    p2 = fake_ai_manager.get_provider("fake", "model-b")
    assert p1 is not p2
    assert p1._model == "model-a"
    assert p2._model == "model-b"


@pytest.mark.anyio
async def test_manager_chat_returns_provider_reply(fake_ai_manager: AIManager):
    reply = await fake_ai_manager.chat("fake", [{"role": "user", "content": "hi"}])
    assert reply == "fake reply"
    provider = fake_ai_manager.get_provider("fake")
    assert len(provider.chat_calls) == 1


@pytest.mark.anyio
async def test_manager_stream_chat_yields_chunks(fake_ai_manager: AIManager):
    chunks = [
        c async for c in fake_ai_manager.stream_chat("fake", [{"role": "user", "content": "hi"}])
    ]
    assert chunks == ["chunk1", "chunk2"]


# =========================================================================
# OpenAI / Custom Provider
# =========================================================================


def _build_openai_mocks(monkeypatch: pytest.MonkeyPatch, content: str):
    """Mock AsyncOpenAI，返回固定回复。

    注意：provider 模块使用 ``from openai import AsyncOpenAI`` 绑定引用，
    因此必须 patch 模块自身属性而非 openai 包根命名空间。
    """

    class FakeDelta:
        def __init__(self, content: str | None) -> None:
            self.content = content

    class FakeMessage:
        def __init__(self, content: str) -> None:
            self.content = content

    class FakeChoice:
        def __init__(self, content: str) -> None:
            self.message = FakeMessage(content)
            self.delta = FakeDelta(content)

    class FakeResponse:
        def __init__(self, content: str) -> None:
            self.choices = [FakeChoice(content)]

    class FakeStream:
        def __init__(self, chunks: list[str]) -> None:
            self._chunks = chunks
            self.created = None
            self.id = None
            self.model = None
            self.object = None
            self.usage = None

        def __aiter__(self):
            self._iter = iter(self._chunks)
            return self

        async def __anext__(self) -> FakeResponse:
            try:
                chunk = next(self._iter)
            except StopIteration:
                raise StopAsyncIteration from None
            return FakeResponse(chunk)

    class FakeCompletions:
        def __init__(self, content: str) -> None:
            self._content = content

        async def create(self, **kwargs: Any):
            if kwargs.get("stream"):
                return FakeStream([self._content])
            return FakeResponse(self._content)

    class FakeChat:
        def __init__(self, content: str) -> None:
            self.completions = FakeCompletions(content)

    class FakeClient:
        def __init__(self, **kwargs: Any) -> None:
            self.chat = FakeChat(content)

    monkeypatch.setattr("app.services.ai.openai_provider.AsyncOpenAI", FakeClient)
    monkeypatch.setattr("app.services.ai.custom_provider.AsyncOpenAI", FakeClient)


@pytest.mark.anyio
async def test_openai_provider_chat(monkeypatch: pytest.MonkeyPatch):
    from app.services.ai.openai_provider import OpenAIProvider

    _build_openai_mocks(monkeypatch, "Hello from OpenAI")
    provider = OpenAIProvider(
        api_key="test-key", base_url="https://test.example/v1", model="gpt-test"
    )
    assert provider.name == "openai"
    assert provider.model == "gpt-test"
    reply = await provider.chat([{"role": "user", "content": "hi"}])
    assert reply == "Hello from OpenAI"


@pytest.mark.anyio
async def test_openai_provider_stream_chat(monkeypatch: pytest.MonkeyPatch):
    from app.services.ai.openai_provider import OpenAIProvider

    _build_openai_mocks(monkeypatch, "streamed")
    provider = OpenAIProvider(
        api_key="test-key", base_url="https://test.example/v1", model="gpt-test"
    )
    chunks = [c async for c in provider.stream_chat([{"role": "user", "content": "hi"}])]
    assert chunks == ["streamed"]


@pytest.mark.anyio
async def test_custom_provider_chat(monkeypatch: pytest.MonkeyPatch):
    from app.services.ai.custom_provider import CustomProvider

    _build_openai_mocks(monkeypatch, "Hello from Custom")
    provider = CustomProvider(
        api_key="test-key", base_url="https://test.example/v1", model="custom-test"
    )
    assert provider.name == "custom"
    assert provider.model == "custom-test"
    reply = await provider.chat([{"role": "user", "content": "hi"}])
    assert reply == "Hello from Custom"


@pytest.mark.anyio
async def test_custom_provider_stream_chat(monkeypatch: pytest.MonkeyPatch):
    from app.services.ai.custom_provider import CustomProvider

    _build_openai_mocks(monkeypatch, "custom-stream")
    provider = CustomProvider(
        api_key="test-key", base_url="https://test.example/v1", model="custom-test"
    )
    chunks = [c async for c in provider.stream_chat([{"role": "user", "content": "hi"}])]
    assert chunks == ["custom-stream"]


@pytest.mark.anyio
async def test_openai_provider_chat_error_raises(monkeypatch: pytest.MonkeyPatch):
    from app.services.ai.openai_provider import OpenAIProvider

    class FailingCompletions:
        async def create(self, **kwargs: Any):
            raise RuntimeError("api down")

    class FailingChat:
        def __init__(self) -> None:
            self.completions = FailingCompletions()

    class FailingClient:
        def __init__(self, **kwargs: Any) -> None:
            self.chat = FailingChat()

    monkeypatch.setattr("app.services.ai.openai_provider.AsyncOpenAI", FailingClient)
    monkeypatch.setattr("app.services.ai.custom_provider.AsyncOpenAI", FailingClient)
    provider = OpenAIProvider(
        api_key="test-key", base_url="https://test.example/v1", model="gpt-test"
    )
    with pytest.raises(RuntimeError, match="api down"):
        await provider.chat([{"role": "user", "content": "hi"}])


# =========================================================================
# 消息权限
# =========================================================================


class TestCheckPermission:
    def test_no_whitelist_allows_all(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(settings, "ADMIN_WHITELIST", "")
        monkeypatch.setattr(settings, "GROUP_BLACKLIST", "")
        allowed, reason = check_permission("wxid_any", None)
        assert allowed is True
        assert reason == "OK"

    def test_whitelist_allows_member(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(settings, "ADMIN_WHITELIST", "wxid_a, wxid_b")
        monkeypatch.setattr(settings, "GROUP_BLACKLIST", "")
        allowed, _ = check_permission("wxid_b", None)
        assert allowed is True

    def test_whitelist_blocks_unknown(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(settings, "ADMIN_WHITELIST", "wxid_a, wxid_b")
        monkeypatch.setattr(settings, "GROUP_BLACKLIST", "")
        allowed, reason = check_permission("wxid_evil", None)
        assert allowed is False
        assert "白名单" in reason

    def test_blacklist_blocks_room(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(settings, "ADMIN_WHITELIST", "")
        monkeypatch.setattr(settings, "GROUP_BLACKLIST", "room_1, room_2")
        allowed, reason = check_permission("wxid_any", "room_1")
        assert allowed is False
        assert "拉黑" in reason

    def test_blacklist_only_blocks_matching_room(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(settings, "ADMIN_WHITELIST", "")
        monkeypatch.setattr(settings, "GROUP_BLACKLIST", "room_1")
        allowed, _ = check_permission("wxid_any", "room_other")
        assert allowed is True

    def test_whitelist_check_happens_after_blacklist(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(settings, "ADMIN_WHITELIST", "wxid_a")
        monkeypatch.setattr(settings, "GROUP_BLACKLIST", "room_1")
        # 群在黑名单中，即使人在白名单也拒绝
        allowed, reason = check_permission("wxid_a", "room_1")
        assert allowed is False
        assert "拉黑" in reason
