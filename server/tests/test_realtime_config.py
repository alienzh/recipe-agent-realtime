import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import realtime_config as rc  # noqa: E402


def test_builds_openai_realtime_config():
    cfg = rc.build_vendor(
        "openai",
        {
            "OPENAI_API_KEY": "test-key",
            "OPENAI_MODEL": "gpt-4o-realtime-preview",
        },
    ).to_config()
    assert cfg["vendor"] == "openai"
    assert cfg["api_key"] == "test-key"
    assert cfg["params"]["model"] == "gpt-4o-realtime-preview"
    assert cfg["turn_detection"].model_dump(exclude_none=True) == {
        "mode": "server_vad"
    }


def test_openai_vision_variant_adds_input_modalities():
    cfg = rc.build_vendor(
        "openai",
        {"OPENAI_API_KEY": "k"},
        input_modalities=["text", "image"],
    ).to_config()
    assert cfg["input_modalities"] == ["text", "image"]


def test_builds_azure_openai_realtime_config():
    cfg = rc.build_vendor(
        "azure",
        {
            "AZURE_OPENAI_API_KEY": "azure-key",
            "AZURE_OPENAI_REALTIME_URL": "wss://example.openai.azure.com/openai/realtime",
            "AZURE_OPENAI_REALTIME_MODEL": "gpt-realtime-2",
        },
        greeting="Hello from Azure.",
    ).to_config()

    turn_detection = cfg.pop("turn_detection")
    assert turn_detection.model_dump(exclude_none=True) == {"mode": "server_vad"}
    assert cfg == {
        "vendor": "azure",
        "api_key": "azure-key",
        "url": "wss://example.openai.azure.com/openai/realtime",
        "params": {
            "model": "gpt-realtime-2",
            "voice": "alloy",
            "instructions": "You are a Conversational AI Agent, developed by Agora.",
        },
        "max_history": 20,
        "greeting_message": "Hello from Azure.",
        "output_modalities": ["audio"],
    }


def test_reports_missing_azure_configuration():
    with pytest.raises(ValueError) as error:
        rc.build_vendor("azure", {})

    assert "AZURE_OPENAI_API_KEY" in str(error.value)
    assert "AZURE_OPENAI_REALTIME_URL" in str(error.value)
    assert "AZURE_OPENAI_REALTIME_MODEL" in str(error.value)


def test_lists_supported_realtime_vendors():
    assert rc.available() == ["azure", "openai"]
    assert rc.required_env("azure") == [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_REALTIME_URL",
        "AZURE_OPENAI_REALTIME_MODEL",
    ]
