# Professional AI Voice Assistant

This repository is building a production-quality AI voice assistant in phases. The current implementation is **Phase 1 only**: a secure, persisted, streaming **text conversation foundation** that prepares the system for realtime voice in a later phase.

## Architecture Summary

- React + TypeScript + Vite frontend in `apps/web`.
- FastAPI + Pydantic v2 backend in `services/api`.
- SQLAlchemy 2.x async persistence with Alembic migrations.
- PostgreSQL for users, settings, conversations, and messages.
- Provider-agnostic chat model abstraction in `services/api/app/providers`.
- Assistant orchestration separated from HTTP routes and provider SDK details.

See `docs/architecture/technical-blueprint.md` for the full blueprint.

## Current Capabilities

- Local development authentication scaffold.
- Conversation creation and history loading.
- Persisted user and assistant messages.
- Server-sent event streaming for assistant text responses.
- Fake local AI provider for deterministic development without external credentials.
- Optional OpenAI provider behind the `ChatModelProvider` abstraction.
- Basic settings UI for response style.

## Intentionally Deferred

Voice/audio, STT, TTS, WebSocket voice sessions, web search, tool/plugin ecosystem, long-term memory, pgvector, reminders, email/calendar integrations, destructive actions, scheduled background workflows, and multi-provider routing are intentionally not implemented in Phase 1.

## Prerequisites

- Python 3.12+
- Node.js 20+
- npm
- Docker and Docker Compose for local PostgreSQL
- `uv` for Python dependency management is recommended

## Environment Setup

```bash
cp .env.example .env
```

For local development, keep `AI_PROVIDER=fake` unless you intentionally configure a real provider. Do not commit secrets.

## Database Setup

```bash
docker compose up -d postgres
cd services/api
uv sync --dev
uv run alembic upgrade head
```

## Start the Backend

```bash
cd services/api
uv run uvicorn app.main:app --reload
```

Backend defaults to <http://localhost:8000>.

## Start the Frontend

```bash
cd apps/web
npm install
npm run dev
```

Frontend defaults to <http://localhost:5173>.

## Local Login

With the default `.env.example` values, log in with:

- Email: `local@example.com`
- Password: `local-password`

The local user is created on first successful local login when `APP_ENV=local`.

## Testing and Checks

Backend:

```bash
cd services/api
uv run ruff check app tests
uv run pytest
```

Frontend:

```bash
cd apps/web
npm run build
npm run test
```

## Streaming API Decision

Phase 1 uses HTTP Server-Sent Events for text response streaming. SSE is simple, works well for one-way assistant text deltas, is easy to debug, and does not prematurely introduce the bidirectional WebSocket/WebRTC voice transport planned for Phase 2.
