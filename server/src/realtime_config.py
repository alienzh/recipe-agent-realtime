"""Build the OpenAIRealtime MLLM vendor for the realtime recipe.

The MLLM replaces the cascading STT->LLM->TTS. turn_detection is MLLM-owned
(server_vad); the top-level cascading turn_detection has no effect when set here.
"""
from typing import List, Optional

from agora_agent.agentkit.vendors import OpenAIRealtime


def build_realtime_mllm(
    api_key: str,
    model: str,
    greeting: Optional[str] = None,
    input_modalities: Optional[List[str]] = None,
) -> OpenAIRealtime:
    kwargs = {
        "api_key": api_key,
        "model": model,
        "turn_detection": {"mode": "server_vad"},
    }
    if greeting:
        kwargs["greeting_message"] = greeting
    if input_modalities:
        kwargs["input_modalities"] = input_modalities
    return OpenAIRealtime(**kwargs)
