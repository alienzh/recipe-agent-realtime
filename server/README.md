# Agora Agent Backend — Realtime Recipe

FastAPI service that owns Agora token generation and agent session lifecycle for
the realtime recipe. It is the service the web client reaches through the
Next.js `/api/*` rewrite proxy (port 8000).

## What this service does

Runs a selectable realtime MLLM via `.with_mllm()` — **BYO-key, not zero-key**:

**Pipeline:** `<MLLM_VENDOR>` (voice-to-voice, `server_vad` turn detection)

OpenAI Realtime and Azure OpenAI Realtime are available. The selected vendor
replaces the cascading STT→LLM→TTS pipeline with one realtime model. Provider
settings are validated at agent start, not server boot.

There is **no separate `llm/` service** in this recipe.

## Run

Use the repo-root `README.md` for the full local flow (`bun run dev`). To work on
this module directly:

```bash
cd server
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python src/server.py
```

## Environment

`server/.env.example` is the template. Required:

- `AGORA_APP_ID` — Agora project App ID.
- `AGORA_APP_CERTIFICATE` — Agora project App Certificate.

Provider-specific required variables:

| Provider | Variables |
| --- | --- |
| OpenAI | `OPENAI_API_KEY` |
| Azure | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_REALTIME_URL`, `AZURE_OPENAI_REALTIME_MODEL` |

Optional:

| Variable | Default | Notes |
| --- | :---: | --- |
| `MLLM_VENDOR` | `openai` | Realtime provider: `openai` or `azure` |
| `OPENAI_MODEL` | `gpt-4o-realtime-preview` | OpenAI Realtime model name |
| `AGENT_GREETING` | built-in | Optional opening line override |

## API

- `GET /get_config` — token + channel/UID config
- `GET /vendors` — selectable realtime providers and required environment variables
- `POST /startAgent` — start an agent session
- `POST /stopAgent` — stop an agent session

The repo-root `bun run verify:local:fastapi` exercises these routes through the
Next proxy using a fake agent (`scripts/run_fake_server.py`), so no live Agora
session is required.
