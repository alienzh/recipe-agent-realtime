# Architecture — Realtime Recipe

Two processes. The browser talks only to Next.js `/api/*`, which rewrites to the
agent backend. The agent backend owns Agora tokens and agent lifecycle.

The selected provider's settings are validated at agent start, not server boot.

## Request flow

```
Browser
  │  GET /api/vendors               → realtime provider options
  │  GET /api/get_config            → token + channel/UIDs
  │  POST /api/startAgent {vendor}  → start agent session
  ▼
Next.js  (rewrites /api/* → AGENT_BACKEND_URL)
  ▼
Agent backend (server/, :8000)
  │  builds the selected realtime MLLM via .with_mllm()
  ▼
Agora ConvoAI Cloud
  │  user speech → OpenAI or Azure Realtime (voice-to-voice, server_vad)
  │  agent speech → user's channel
  ▼
User hears realtime voice response; RTM transcript + metrics → web UI
```

`POST /api/stopAgent { agentId }` ends the session.

## Why no llm/ service

Unlike the custom-llm recipe family, the realtime recipe attaches one selected
MLLM vendor via `agora_agent.with_mllm(mllm)`. This vendor
handles the full voice-to-voice pipeline — STT, reasoning, and TTS are all
internal to the realtime model. No cascading vendors are used, no
separate mock service is needed, and no public tunnel is required.

Trade-off: the selected provider requires BYO credentials. The agent is **not
zero-key**.

## MLLM vendor

`server/src/realtime_config.py` contains one builder per provider and a shared
registry. It currently supports `OpenAIRealtime` and `AzureOpenAIRealtime` with:

- `turn_detection={"mode": "server_vad"}` — vendor-side VAD; the top-level
  cascading `turn_detection` on `AgoraAgent(...)` is not set.
- `greeting_message` — optional opening utterance from the agent.
- provider-specific model, URL, voice, and credentials.

No tools — the realtime MLLM flow has no tool support in this recipe.

## API (agent backend, port 8000)

| Endpoint | Method | Description |
| --- | --- | --- |
| `/get_config` | GET | Token + channel/UID config |
| `/vendors` | GET | Selectable realtime providers and required env vars |
| `/startAgent` | POST | Start the realtime agent session |
| `/stopAgent` | POST | Stop the agent by `agent_id` |

The browser calls these as `/api/*`; Next rewrites them to `AGENT_BACKEND_URL`.

## Auth

- Browser → agent backend: none (local dev).
- Agent backend → Agora cloud: Token007, generated from `AGORA_APP_ID` +
  `AGORA_APP_CERTIFICATE`.
- Agora cloud → selected provider: provider API key (BYO, passed at agent start).
