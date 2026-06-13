# Agora Agent Backend — Realtime Recipe

FastAPI service that owns Agora token generation and agent session lifecycle for
the realtime recipe. It is the service the web client reaches through the
Next.js `/api/*` rewrite proxy (port 8000).

## What this service does

Runs a single `OpenAIRealtime` MLLM via `.with_mllm()` — **BYO-key, not zero-key**:

**Pipeline:** `OpenAIRealtime` MLLM (voice-to-voice, server_vad turn detection)

The `OpenAIRealtime` vendor replaces the cascading STT→LLM→TTS with a single
realtime model. `OPENAI_API_KEY` is required and is validated at agent start
(not server boot), so the server starts even if the key is absent, but
`/startAgent` returns 400 until the key is configured.

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
- `OPENAI_API_KEY` — OpenAI key with Realtime API access (required; validated at agent start).

Optional:

| Variable | Default | Notes |
| --- | :---: | --- |
| `OPENAI_MODEL` | `gpt-4o-realtime-preview` | OpenAI Realtime model name |
| `AGENT_GREETING` | built-in | Optional opening line override |

## API

- `GET /get_config` — token + channel/UID config
- `POST /startAgent` — start an agent session
- `POST /stopAgent` — stop an agent session

The repo-root `bun run verify:local:fastapi` exercises these routes through the
Next proxy using a fake agent (`scripts/run_fake_server.py`), so no live Agora
session is required.
