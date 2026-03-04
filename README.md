# AI Property Manager

AI-driven revenue optimization and property operations platform for short-term rentals.

## Quick Start

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies (creates .venv automatically)
uv sync

# Start local infrastructure
docker compose -f docker/docker-compose.yml up -d

# Run database migrations
uv run alembic upgrade head

# Seed initial data
uv run python -m scripts.seed_data

# Start the API server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Architecture

```
app/            → Application entrypoint (FastAPI startup, lifespan)
api/            → HTTP routes and request handling
core/           → Shared configuration, logging, constants
domain/         → Pure domain models and value objects
services/       → Business logic orchestration
ml/             → Feature engineering, ML models, reinforcement learning
infrastructure/ → Database, scraping, external API clients
workers/        → Background jobs (scraping, training, pricing)
config/         → Environment-specific YAML configs
scripts/        → Bootstrap and utility scripts
tests/          → Unit and integration tests
```

## Initial Region

Berchtesgaden, Germany — 5 km radius
