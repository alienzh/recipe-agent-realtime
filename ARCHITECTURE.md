# Architecture — Realtime Recipe

Two processes. The browser talks only to Next.js `/api/*`, which rewrites to the
agent backend. The agent backend owns Agora tokens and agent lifecycle.

`OPENAI_API_KEY` is required — validated at agent start, not server boot.

## Request flow

```
Browser
  │  GET /api/get_config            → token + channel/UIDs
  │  POST /api/startAgent           → start agent session
  ▼
Next.js  (rewrites /api/* → AGENT_BACKEND_URL)
  ▼
Agent backend (server/, :8000)
  │  builds OpenAIRealtime MLLM via .with_mllm()
  ▼
Agora ConvoAI Cloud
  │  user speech → OpenAI Realtime (voice-to-voice, server_vad)
  │  agent speech → user's channel
  ▼
User hears realtime voice response; RTM transcript + metrics → web UI
```

`POST /api/stopAgent { agentId }` ends the session.

## Why no llm/ service

Unlike the custom-llm recipe family, the realtime recipe attaches a single
`OpenAIRealtime` MLLM vendor via `agora_agent.with_mllm(mllm)`. This vendor
handles the full voice-to-voice pipeline — STT, reasoning, and TTS are all
internal to the OpenAI Realtime model. No cascading vendors are used, no
separate mock service is needed, and no public tunnel is required.

Trade-off: `OPENAI_API_KEY` with Realtime API access is required. The agent
is **not zero-key**.

## MLLM vendor

`server/src/realtime_config.py` contains `build_realtime_mllm()`, which
constructs an `OpenAIRealtime` vendor with:

- `turn_detection={"mode": "server_vad"}` — vendor-side VAD; the top-level
  cascading `turn_detection` on `AgoraAgent(...)` is not set.
- `greeting_message` — optional opening utterance from the agent.
- `input_modalities` — optional (e.g. `["text", "image"]` for vision variants).

No tools — the OpenAI Realtime MLLM has no tool support in this SDK.

## API (agent backend, port 8000)

| Endpoint | Method | Description |
| --- | --- | --- |
| `/get_config` | GET | Token + channel/UID config |
| `/startAgent` | POST | Start the realtime agent session |
| `/stopAgent` | POST | Stop the agent by `agent_id` |

The browser calls these as `/api/*`; Next rewrites them to `AGENT_BACKEND_URL`.

## Auth

- Browser → agent backend: none (local dev).
- Agent backend → Agora cloud: Token007, generated from `AGORA_APP_ID` +
  `AGORA_APP_CERTIFICATE`.
- Agora cloud → OpenAI Realtime: `OPENAI_API_KEY` (BYO — passed at agent start).
