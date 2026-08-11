"""Realtime MLLM vendor registry for the realtime recipe.

Each builder shows the exact SDK constructor and environment variables for one
provider. The selected MLLM owns turn detection, so no top-level cascading turn
detection is configured on the agent.
"""
import os
from typing import Callable, Dict, List, Optional, Tuple

from agora_agent.agentkit.vendors import AzureOpenAIRealtime, OpenAIRealtime

CATEGORY = "MLLM"
DEFAULT_VENDOR = "openai"


def build_openai(
    env: Dict[str, str],
    greeting: Optional[str] = None,
    input_modalities: Optional[List[str]] = None,
):
    """OpenAI Realtime - requires OPENAI_API_KEY."""
    kwargs = {
        "api_key": env["OPENAI_API_KEY"],
        "model": env.get("OPENAI_MODEL", "gpt-4o-realtime-preview"),
        "turn_detection": {"mode": "server_vad"},
    }
    if greeting:
        kwargs["greeting_message"] = greeting
    if input_modalities:
        kwargs["input_modalities"] = input_modalities
    return OpenAIRealtime(**kwargs)


def build_azure(
    env: Dict[str, str],
    greeting: Optional[str] = None,
    input_modalities: Optional[List[str]] = None,
):
    """Azure OpenAI Realtime - requires the user's Azure resource settings."""
    if input_modalities:
        raise ValueError("Azure OpenAI Realtime does not support input_modalities")

    kwargs = {
        "api_key": env["AZURE_OPENAI_API_KEY"],
        "url": env["AZURE_OPENAI_REALTIME_URL"],
        "model": env["AZURE_OPENAI_REALTIME_MODEL"],
        "voice": "alloy",
        "instructions": "You are a Conversational AI Agent, developed by Agora.",
        "output_modalities": ["audio"],
        "max_history": 20,
        "turn_detection": {"mode": "server_vad"},
    }
    if greeting:
        kwargs["greeting_message"] = greeting
    return AzureOpenAIRealtime(**kwargs)


REGISTRY: Dict[str, Tuple[Callable, List[str]]] = {
    "openai": (build_openai, ["OPENAI_API_KEY"]),
    "azure": (
        build_azure,
        [
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_REALTIME_URL",
            "AZURE_OPENAI_REALTIME_MODEL",
        ],
    ),
}


def available() -> List[str]:
    return sorted(REGISTRY)


def required_env(name: str) -> List[str]:
    return list(REGISTRY[name][1])


def needs_key(name: str) -> bool:
    return bool(REGISTRY[name][1])


def build_vendor(
    name: str,
    env: Optional[Dict[str, str]] = None,
    greeting: Optional[str] = None,
    input_modalities: Optional[List[str]] = None,
):
    """Build a realtime MLLM and report missing provider configuration."""
    env = env if env is not None else os.environ
    if name not in REGISTRY:
        raise ValueError(f"unknown {CATEGORY} vendor '{name}'; choose one of {available()}")

    builder, required = REGISTRY[name]
    missing = [variable for variable in required if not env.get(variable)]
    if missing:
        raise ValueError(
            f"{CATEGORY} vendor '{name}' requires environment variable(s): "
            f"{', '.join(missing)}"
        )

    return builder(env, greeting=greeting, input_modalities=input_modalities)
