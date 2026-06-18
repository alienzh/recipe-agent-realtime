"""Shared fixtures for the server test suite (standalone: no cloud, no creds)."""
import importlib
import os
import sys

import pytest

_SERVER_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if _SERVER_SRC not in sys.path:
    sys.path.insert(0, _SERVER_SRC)

FAKE_ENV = {
    "AGORA_APP_ID": "0123456789abcdef0123456789abcdef",
    "AGORA_APP_CERTIFICATE": "fedcba9876543210fedcba9876543210",
    # OPENAI_API_KEY is required for the realtime MLLM; a dummy value is legit
    # here because start() validates the key before building OpenAIRealtime —
    # the smoke test monkeypatches create_async_session so the SDK never dials out.
    "OPENAI_API_KEY": "sk-test-dummy",
}


@pytest.fixture
def fake_env(monkeypatch):
    import dotenv
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: False)
    for key, value in FAKE_ENV.items():
        monkeypatch.setenv(key, value)
    return dict(FAKE_ENV)


class FakeAgent:
    def __init__(self):
        self.started = []
        self.stopped = []

    async def start(self, channel_name, agent_uid, user_uid, output_audio_codec=None):
        self.started.append((channel_name, agent_uid, user_uid))
        return {
            "agent_id": f"fake-agent-{agent_uid}",
            "channel_name": channel_name,
            "status": "started",
        }

    async def stop(self, agent_id):
        self.stopped.append(agent_id)
