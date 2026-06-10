# menu.tn — Backend

FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL

## Quickstart

```bash
# 1. Start Postgres + Redis
docker compose up -d   # from the repo root

# 2. Install dependencies
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Copy and configure env
cp ../.env.example .env
# Edit .env — at minimum set SECRET_KEY

# 4. Run migrations
alembic upgrade head

# 5. Start the API
uvicorn app.main:app --reload
# → http://localhost:8000/docs
```

## Useful commands

```bash
# Create a new migration after changing models
alembic revision --autogenerate -m "describe your change"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Start Celery worker (for background tasks)
celery -A app.workers.celery_app worker --loglevel=info
```

## API structure

All endpoints are under `/v1`. See `/docs` for the full Swagger UI.

| Router | Prefix | Description |
|--------|--------|-------------|
| auth | `/v1/auth` | Register, login, profile |
| businesses | `/v1/businesses` | Business CRUD + public page |
| categories | `/v1/categories` | Menu categories |
| products | `/v1/products` | Menu items |
| qr | `/v1/qr` | QR code generation + scan tracking |
| analytics | `/v1/analytics` | Event tracking + overview (Premium) |
| subscriptions | `/v1/subscription` | Plan management |
