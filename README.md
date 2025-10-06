# AiOtvet Platform

AiOtvet is a modular customer-support automation platform integrating Telegram chatbots, a FastAPI core, knowledge base retrieval augmented generation, and administration tools.

## Components

- **api_core** — FastAPI service handling REST and WebSocket APIs, database access, and LLM orchestration.
- **tg_gateway** — Customer-facing Telegram bot built with aiogram.
- **admin_tg** — Operator Telegram bot with a Mini App.
- **web_admin** — React/Next.js web console for operators.
- **worker** — Background task runner for embeddings and notifications.
- **infra** — Docker Compose and Nginx configuration.

## Local development

1. Create a `.env` file using `.env.example` as a template.
2. Install Python dependencies and run the API: `uvicorn api_core.main:app --reload`.
3. Run tests with `pytest`.
4. Launch the web admin using `npm install && npm run dev` inside `web_admin`.

## Database migrations

Alembic migrations live under `api_core/migrations`. Apply them with:

```bash
alembic upgrade head
```

## Testing

Run unit and integration tests with:

```bash
pytest
```

## Licensing

This repository is provided for internal evaluation and is not licensed for redistribution.
