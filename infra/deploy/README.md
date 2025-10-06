# Deployment guide

1. Populate environment variables as described in `.env.example`.
2. Build and run services via `docker-compose up --build`.
3. Apply database migrations inside `api_core` container with `alembic upgrade head`.
4. Configure Telegram bots and set webhook URLs pointing to the public ingress domain.
