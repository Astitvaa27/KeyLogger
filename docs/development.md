# Development Guide

## Prerequisites

- Python 3.11+
- Node.js 20+ (22 recommended)
- PostgreSQL 16 (or Docker)

## Option A — Docker (fastest)

```bash
cp .env.example .env        # edit SECRET_KEY etc.
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend docs: http://localhost:8000/docs
- The backend container runs `alembic upgrade head` before serving.

## Option B — Manual setup

### 1. Database

Create a database and user (matching your `.env`):
```bash
sudo -u postgres psql -c "CREATE USER keylogger WITH PASSWORD 'keylogger_dev';"
sudo -u postgres psql -c "CREATE DATABASE keylogger OWNER keylogger;"
```

### 2. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configure environment (or use a root .env)
export DATABASE_URL="postgresql+psycopg2://keylogger:keylogger_dev@localhost:5432/keylogger"
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"
export CORS_ORIGINS="http://localhost:5173"

# Apply migrations, then run the API
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

The detection-rule catalog is seeded automatically on startup.

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env         # points VITE_API_BASE_URL at the backend
npm run dev
```

Open http://localhost:5173 and register an account.

## Environment variables

See [`.env.example`](../.env.example) at the repo root. Key values:

| Variable                | Purpose                                  |
|-------------------------|------------------------------------------|
| `DATABASE_URL`          | SQLAlchemy connection string             |
| `SECRET_KEY`            | JWT signing key (generate a long random) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime                     |
| `CORS_ORIGINS`          | Comma-separated allowed frontend origins |
| `VITE_API_BASE_URL`     | Frontend → backend REST base             |
| `VITE_WS_BASE_URL`      | Frontend → backend WebSocket base        |

## Testing

### Backend
```bash
cd backend && source .venv/bin/activate
pytest                 # runs against in-memory SQLite; no DB needed
ruff check app tests   # lint
```

The suite covers: password hashing & JWT, analytics math, the simulation
service, the detection/scoring engine, auth flows, keystroke ingest &
statistics, session-active enforcement, the full simulation→detection→dashboard
flow, and cross-user authorization boundaries.

### Frontend
```bash
cd frontend
npm run lint
npm run build          # type-free production build check
```

## Database migrations

```bash
cd backend
# After changing a model:
alembic revision --autogenerate -m "describe change"
alembic upgrade head
# Roll back one step:
alembic downgrade -1
```

## Project layout

```
KeyLogger/
├── backend/     # FastAPI + SQLAlchemy + Alembic + pytest
├── frontend/    # React + Vite + Tailwind + Recharts
├── docs/        # architecture, threat-model, api, development
├── docker-compose.yml
├── .env.example
└── README.md
```

## Common issues

- **`401` on every request** — the token expired or `SECRET_KEY` changed;
  log in again.
- **CORS errors in the browser** — add your frontend origin to `CORS_ORIGINS`
  and restart the backend.
- **`alembic` can't connect** — confirm `DATABASE_URL` and that PostgreSQL is
  running.
- **bcrypt version warning** — resolved by the pinned `bcrypt==4.0.1` in
  `requirements.txt`.
