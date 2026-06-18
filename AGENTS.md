# Agent Development Guide

For coding agents working in `recipe-agent-realtime`. This repository is the
**realtime** recipe in the Agora Conversational AI recipes family.

## System shape

- **`server/`** — Python FastAPI agent backend (:8000). Owns Agora token
  generation and agent session lifecycle. Uses `OpenAIRealtime` MLLM via
  `.with_mllm()` — replaces the STT/LLM/TTS cascade. SDK: `agora-agents>=2.3.0`
  (`import agora_agent`).
- **`web/`** — Next.js 16 / React 19 / TypeScript frontend (:3000).
- Auth: Token007 from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.
- No `llm/` service — single-process, MLLM is BYO-key (OPENAI_API_KEY required).

## Pipeline

`OpenAIRealtime` MLLM via `.with_mllm()` — voice-to-voice, no separate STT/LLM/TTS.
Turn detection is MLLM-owned (`server_vad`). No tools (MLLM is tool-less).

## Routing / ownership

- UI and RTC/RTM lifecycle live in `web/`.
- Browser-facing `/api/*` paths are Next rewrites (`web/next.config.ts`) to the
  agent backend; do not add `web/app/api/**/route.ts` for agent/token logic.
- Token generation and agent lifecycle live in `server/src/`.
- MLLM vendor builder lives in `server/src/realtime_config.py`.

## Supported modes

- **Local:** `bun run dev` starts `server` (:8000) and `web` (:3000).
  The web app calls `/api/*`; Next rewrites to
  `AGENT_BACKEND_URL=http://localhost:8000`.
- **Deploy:** deploy `web` (Next) + `server` (reachable FastAPI).
  Set `AGENT_BACKEND_URL` in the web deployment.

## Env vars

| Variable | Default | Notes |
|---|---|---|
| `AGORA_APP_ID` | — | required |
| `AGORA_APP_CERTIFICATE` | — | required |
| `OPENAI_API_KEY` | — | **required** — validated at agent start (not server boot); needs OpenAI Realtime API access |
| `OPENAI_MODEL` | `gpt-4o-realtime-preview` | OpenAI Realtime model name |
| `AGENT_GREETING` | built-in | Optional opening line override |

## Patterns

- Keep the web client calling `/api/*`; hide backend placement behind Next rewrites.
- Keep token generation and the App Certificate in `server/`.
- `OPENAI_API_KEY` is validated in `agent.start()` — the server boots without it,
  but `/startAgent` returns 400 until the key is set.
- `turn_detection` is MLLM-owned (`server_vad`); do not set a top-level
  `turn_detection` on `AgoraAgent(...)` when using `.with_mllm()`.

## Anti-patterns

- Do not reintroduce `llm/` or the cascading STT/LLM/TTS vendors.
- Do not reintroduce Next Route Handlers for agent/token logic.
- Do not put `PORT` in `server/.env.example` (it would clobber the random port
  that `verify:local:fastapi` injects via `load_dotenv(override=True)`).
- Do not link to `docs/ai/` — that progressive-disclosure tree is not present yet.
- Do not add tools — the OpenAIRealtime MLLM has no tool support.

## Commands

```bash
bun run setup
bun run dev
bun run doctor
bun run doctor:local
bun run verify         # web-only, no creds
bun run verify:local   # full local gate
```

Narrower checks: `bun run verify:backend`, `bun run verify:local:fastapi`,
`bun run verify:web:proxy`.

## Done criteria

1. Run the narrowest relevant verification command.
2. Web-affecting changes: `bun run verify:web` passes.
3. Backend-affecting changes: `bun run verify:local` (or narrower
   `verify:local:fastapi` / `verify:backend`) passes.
4. If you change required env vars or setup steps, update the root README,
   the relevant module README, and `server/.env.example` together.

## Git conventions

- Conventional Commits: `type: description` or `type(scope): description`
  (`feat`, `fix`, `chore`, `test`, `docs`). Lowercase after the prefix, present
  tense.
- No AI tool names in commit messages or PR descriptions. No `Co-Authored-By`
  trailers. No `--no-verify`. No git config changes.
- Branch names: `type/short-description` (e.g. `feat/add-language-selector`).
