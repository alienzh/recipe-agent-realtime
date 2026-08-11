# Agora Conversational AI — Realtime Recipe (Python)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![Bun](https://img.shields.io/badge/bun-latest-black)](https://bun.sh/)

The **realtime** recipe in the Agora Conversational AI recipes family.
Voice-to-voice conversation using a selectable realtime MLLM provider — no
separate STT, LLM, or TTS. Choose OpenAI Realtime or Azure OpenAI Realtime,
speak, and hear the model respond directly.

**Not zero-key** — configure the credentials for the provider you select.

**Pipeline:** `<MLLM_VENDOR>` via `.with_mllm()` (`server_vad` turn detection)

## Prerequisites

- [Python 3.10+](https://www.python.org/)
- [Bun](https://bun.sh/)
- [Agora CLI](https://github.com/AgoraIO/cli) — makes generating an App ID + App Certificate easy
- Provider credentials for OpenAI Realtime or Azure OpenAI Realtime

## Run It

```bash
# 1. Install web deps + create the Python venv
bun run setup

# 2. Add Agora credentials (CLI), or edit server/.env.local by hand
agora login
agora project use <your-project>          # select which project to use
agora project env write server/.env.local # writes App ID + Certificate

# 3. Configure one realtime provider in server/.env.local
#    MLLM_VENDOR=openai  (default) or azure
#    Fill in the matching provider variables from server/.env.example

# 4. Run backend + web
bun run dev
```

Open [http://localhost:3000](http://localhost:3000) → **Start Conversation** → speak.

### Working from a clone

If you cloned this repo (rather than scaffolding via the Agora CLI), the steps
above are complete as written: `bun run setup` creates the Python venv and
installs web dependencies, then `bun run dev` brings up both services. You
still need Agora credentials and the selected provider's settings in
`server/.env.local` before a conversation can connect.

Services:

- Frontend — http://localhost:3000
- Backend — http://localhost:8000
- Mock LLM — N/A (the selected realtime MLLM handles voice end-to-end)
- API docs — http://localhost:8000/docs

## Deploy

Deploy `web` (Next.js) and `server` (a reachable FastAPI backend). Set
`AGENT_BACKEND_URL` in the web deployment so the Next rewrites reach the backend.

A backend-only Docker image is published to
`ghcr.io/AgoraIO-Conversational-AI/recipe-agent-realtime` on `v*` tags.
It exposes **BACKEND-ONLY** (:8000). No separate service is needed.

## Environment variables

Backend env file: [`server/.env.example`](server/.env.example).

| Variable | Required | Default | Notes |
| --- | :---: | :---: | --- |
| `AGORA_APP_ID` | ✅ | — | Agora Console → Project → App ID |
| `AGORA_APP_CERTIFICATE` | ✅ | — | Agora Console → Project → App Certificate |
| `MLLM_VENDOR` | | `openai` | Realtime provider: `openai` or `azure` |
| `OPENAI_API_KEY` | OpenAI only | — | OpenAI key with Realtime API access |
| `OPENAI_MODEL` | | `gpt-4o-realtime-preview` | OpenAI Realtime model name |
| `AZURE_OPENAI_API_KEY` | Azure only | — | Azure OpenAI API key |
| `AZURE_OPENAI_REALTIME_URL` | Azure only | — | Azure OpenAI Realtime WebSocket URL |
| `AZURE_OPENAI_REALTIME_MODEL` | Azure only | — | Azure Realtime deployment or model name |
| `AGENT_GREETING` | | built-in | Optional opening line override |

## Commands

```bash
bun run setup            # install web deps + create server/ venv
bun run dev              # run backend (:8000) + web (:3000)

bun run doctor           # prerequisite check (no creds needed)
bun run doctor:local     # + .env.local + credentials checks

bun run verify           # web-only gate (no Agora creds needed)
bun run verify:local     # full local gate: backend compile + smoke tests + web build
bun run clean            # remove venvs and build artifacts
```

Tests run standalone (no Agora cloud needed): `pytest` in `server/`, plus
`bun run verify` in `web/`. CI runs them on Linux/macOS/Windows × Python 3.10 & 3.13.

## Architecture

```
Browser (localhost:3000)
  │  fetch /api/*
  ▼
Next.js  ──rewrite──▶  Agent backend  (server/, localhost:8000)
                          │  starts agent session (selected realtime MLLM)
                          ▼
                       Agora ConvoAI Cloud
                          │  OpenAI or Azure Realtime (voice-to-voice, server_vad)
                          ▼
                       User hears realtime voice response
```

No cascading STT/LLM/TTS vendors. No `llm/` service.
See [ARCHITECTURE.md](./ARCHITECTURE.md).

## What You Get

- A **Next.js** web client (:3000) that drives the RTC/RTM lifecycle and only ever calls `/api/*`.
- A **FastAPI** agent backend (:8000) that owns Agora token generation and the agent session lifecycle.
- The `/api/vendors` · `/api/get_config` · `/api/startAgent` · `/api/stopAgent` contract between the web client and the backend (Next rewrites, no Route Handlers).
- **Selectable realtime MLLM** attached via `.with_mllm()` — OpenAI Realtime or Azure OpenAI Realtime replaces the cascading STT→LLM→TTS pipeline.
- **Server-side VAD** (`server_vad`) turn detection — owned by the MLLM, no top-level cascading VAD config needed.
- **Provider-specific configuration** — validated at agent start so the backend can boot before credentials are added.

## How It Works

1. The browser loads `/api/vendors`, then calls `/api/get_config`; the
   backend mints an Agora token from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.
2. The browser joins the RTC channel, then calls `/api/startAgent`; the backend
   validates the selected provider settings and starts the matching MLLM.
3. The user speaks. Agora routes audio to the selected realtime endpoint.
4. The selected provider processes voice-to-voice and streams response audio back.
5. The agent's voice plays in the channel. RTM transcript + metrics arrive in the web UI.
6. `/api/stopAgent` ends the session.

## Repo Map

- `web/` — Next.js frontend (:3000); RTC/RTM lifecycle and UI.
- `server/` — FastAPI agent backend (:8000); Agora tokens + agent lifecycle, realtime MLLM registry.
- `ARCHITECTURE.md` — system shape and component boundaries.
- `AGENTS.md` — guide for coding agents working in this repo.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `/startAgent` returns 400 | Configure every environment variable listed for the selected provider. |
| Azure agent returns 404 | Check the Azure Realtime WebSocket URL and deployment/model name. |
| Agent starts but no audio | Ensure the selected deployment supports realtime voice. |
| Local calls fail under a global proxy (Clash, etc.) | Configure your proxy to send `127.0.0.1`, `localhost`, and RFC-1918 ranges DIRECT. |

## More Docs

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [AGENTS.md](./AGENTS.md)

## License

Released under the [MIT License](./LICENSE).
