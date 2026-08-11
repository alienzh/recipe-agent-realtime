"""
Agent — Realtime Recipe

High-level API for managing Agora Conversational AI Agents using a selectable
realtime MLLM. The MLLM replaces the cascading STT->LLM->TTS:

  OpenAIRealtime or AzureOpenAIRealtime (voice-to-voice, server_vad)

Provider settings are validated in start(), not __init__.
"""
import logging
import os
from typing import Any, Dict, Optional

from agora_agent import Area, AsyncAgora
from agora_agent.agentkit import Agent as AgoraAgent
from realtime_config import DEFAULT_VENDOR, build_vendor

logger = logging.getLogger("uvicorn.error")


class Agent:
    """
    High-level wrapper for an Agora Conversational AI Agent using a realtime MLLM.

    The MLLM is attached via .with_mllm(). No separate STT, LLM, or TTS vendors
    are used. Provider settings are validated at start() time.
    """

    def __init__(self):
        self.app_id = os.getenv("AGORA_APP_ID")
        self.app_certificate = os.getenv("AGORA_APP_CERTIFICATE")
        self.greeting = os.getenv(
            "AGENT_GREETING",
            "Hi! I'm a realtime voice assistant — let's just talk.",
        )

        # Credential validation happens in start() so /get_config and the server
        # can still run before the selected provider is configured.
        self.vendor = os.getenv("MLLM_VENDOR", DEFAULT_VENDOR)

        if not self.app_id or not self.app_certificate:
            raise ValueError("AGORA_APP_ID and AGORA_APP_CERTIFICATE are required")

        self.client = AsyncAgora(
            area=Area.US,
            app_id=self.app_id,
            app_certificate=self.app_certificate,
        )

        # Track active sessions by agent_id
        self._sessions: Dict[str, Any] = {}

    async def start(
        self,
        channel_name: str,
        agent_uid: int,
        user_uid: int,
        vendor: Optional[str] = None,
        output_audio_codec: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Start realtime voice agent."""
        if not channel_name or not str(channel_name).strip():
            raise ValueError("channel_name is required and cannot be empty")
        if agent_uid <= 0:
            raise ValueError("agent_uid is required and cannot be empty")
        if user_uid <= 0:
            raise ValueError("user_uid is required and cannot be empty")

        selected = (vendor or self.vendor).strip().lower()
        mllm = build_vendor(selected, greeting=self.greeting)

        parameters = {
            "audio_scenario": "chorus",  # web client — ultra-low-latency chorus profile
            "data_channel": "rtm",
            "enable_error_message": True,
            "enable_metrics": True,
        }
        if isinstance(output_audio_codec, str) and output_audio_codec.strip():
            parameters["output_audio_codec"] = output_audio_codec.strip()

        agora_agent = AgoraAgent(
            client=self.client,
            greeting=self.greeting,
            failure_message="Please wait a moment.",
            max_history=50,
            advanced_features={"enable_rtm": True},
            parameters=parameters,
        )
        agora_agent = agora_agent.with_mllm(mllm)

        session = agora_agent.create_async_session(
            channel=channel_name,
            agent_uid=str(agent_uid),
            remote_uids=[str(user_uid)],
            enable_string_uid=False,
            idle_timeout=30,
            expires_in=3600,
        )

        logger.info(
            "Starting realtime agent channel=%s agent_uid=%s user_uid=%s vendor=%s",
            channel_name,
            agent_uid,
            user_uid,
            selected,
        )

        try:
            agent_id = await session.start()
        except Exception:
            logger.exception(
                "Failed to start realtime agent channel=%s agent_uid=%s user_uid=%s",
                channel_name,
                agent_uid,
                user_uid,
            )
            raise

        # Save session for later stop
        self._sessions[agent_id] = session

        logger.info(
            "Started realtime agent agent_id=%s channel=%s",
            agent_id,
            channel_name,
        )

        return {
            "agent_id": agent_id,
            "channel_name": channel_name,
            "vendor": selected,
            "status": "started",
        }

    async def stop(self, agent_id: str) -> None:
        """Stop a running agent. Falls back to the stateless client path."""
        if not agent_id or not str(agent_id).strip():
            raise ValueError("agent_id is required and cannot be empty")

        session = self._sessions.pop(agent_id, None)
        if session:
            try:
                await session.stop()
                logger.info("Stopped agent from active session agent_id=%s", agent_id)
                return
            except Exception:
                logger.warning(
                    "Failed to stop agent from active session; falling back agent_id=%s",
                    agent_id,
                    exc_info=True,
                )

        logger.info("Stopping agent through client.stop_agent agent_id=%s", agent_id)
        await self.client.stop_agent(agent_id)
