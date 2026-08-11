"""Construction smoke: the real AgoraAgent is built and a session is created (SDK session faked).

Closes the gap where the rest of the suite stubs the whole Agent (FakeAgent) and never
exercises AgoraAgent construction — the exact path that agora-agents 2.3.x changed.
"""
import asyncio
import sys


def _fresh_agent_module():
    sys.modules.pop("agent", None)
    import agent
    return agent


def test_start_constructs_real_agent_and_returns_shape(fake_env, monkeypatch):
    agent = _fresh_agent_module()
    captured = {}

    class FakeSession:
        async def start(self):
            return "test-agent-id"

        async def stop(self):
            captured["stopped"] = True

    def fake_create_async_session(self, **kwargs):
        captured["channel"] = kwargs.get("channel")
        captured["remote_uids"] = kwargs.get("remote_uids")
        captured["mllm"] = self.mllm
        return FakeSession()

    from agora_agent.agentkit import Agent as AgoraAgent
    monkeypatch.setattr(AgoraAgent, "create_async_session", fake_create_async_session)

    instance = agent.Agent()
    result = asyncio.run(instance.start(channel_name="ch", agent_uid=111, user_uid=222))

    assert result["agent_id"] == "test-agent-id"
    assert result["channel_name"] == "ch"
    assert result["vendor"] == "openai"
    assert result["status"] == "started"
    assert captured["channel"] == "ch"
    assert captured["remote_uids"] == ["222"]
    assert captured["mllm"]["vendor"] == "openai"


def test_start_constructs_azure_realtime_agent(fake_env, monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "azure-key")
    monkeypatch.setenv(
        "AZURE_OPENAI_REALTIME_URL",
        "wss://example.openai.azure.com/openai/realtime",
    )
    monkeypatch.setenv("AZURE_OPENAI_REALTIME_MODEL", "gpt-realtime-2")

    agent = _fresh_agent_module()
    captured = {}

    class FakeSession:
        async def start(self):
            return "azure-agent-id"

    def fake_create_async_session(self, **kwargs):
        captured["mllm"] = self.mllm
        return FakeSession()

    from agora_agent.agentkit import Agent as AgoraAgent
    monkeypatch.setattr(
        AgoraAgent,
        "create_async_session",
        fake_create_async_session,
    )

    instance = agent.Agent()
    result = asyncio.run(
        instance.start(
            channel_name="azure-ch",
            agent_uid=333,
            user_uid=444,
            vendor="azure",
        )
    )

    assert result["vendor"] == "azure"
    assert captured["mllm"]["vendor"] == "azure"
    assert captured["mllm"]["url"] == "wss://example.openai.azure.com/openai/realtime"
    assert captured["mllm"]["params"]["model"] == "gpt-realtime-2"
    assert captured["mllm"]["output_modalities"] == ["audio"]
