# KeyLogger

### Virtual Keylogger Simulation and Keylogging Detection & Behavioral Analysis Platform

A final-year **cybersecurity capstone** demonstrating the full **defensive**
lifecycle around keylogging:

> Virtual Keystroke Capture → Keystroke Analytics → Threat Simulation →
> Keylogging Detection → Behavioral Analysis → Risk Scoring → SOC Dashboard →
> Defensive Recommendations

[![tests](https://img.shields.io/badge/backend%20tests-29%20passing-brightgreen)]()
[![lint](https://img.shields.io/badge/lint-ruff%20%2B%20eslint%20clean-brightgreen)]()
[![license](https://img.shields.io/badge/scope-educational%20%2F%20defensive-blue)]()

---

## ⚠️ Safety & Ethical Scope (read first)

This project is an **educational simulation and detection platform**. It is
**deliberately not a real keylogger** and cannot be used as one.

**What it does NOT do — by design:**
❌ system-wide keyboard hooks ❌ background/covert capture ❌ capturing other
apps' input ❌ password/credential harvesting ❌ browser input interception
❌ persistence ❌ stealth/evasion ❌ privilege escalation ❌ AV tampering
❌ data exfiltration ❌ covert monitoring.

**What it actually does:**
- ✅ Captures keystroke **metadata** (category + timing) **only** inside its own
  in-app *Virtual Keylogger Lab* textbox, and **only** after the user clicks
  **START TEST**.
- ✅ Never stores the characters typed — only key *categories*.
- ✅ Shows a persistent banner while active:
  *"TEST MODE — Input is being analyzed only inside this application."*
- ✅ Generates **synthetic** threat telemetry (fabricated numbers; no real
  process/network access) to drive the detection engine.
- ✅ Runs a transparent, rule-based detection + risk-scoring engine and presents
  results in a SOC-style dashboard.

Full details: [`docs/threat-model.md`](docs/threat-model.md).

---

## Problem Statement

Keyloggers are among the most common and damaging credential-theft tools, yet
security students rarely get a **safe** environment to study how such threats
*behave* and how defenders *detect* them. Building a real keylogger to "learn
detection" is unsafe and unethical. This project solves that: it models the
behavioral signals and detection workflow **without ever implementing malicious
capability**, so the concepts can be studied, demonstrated, and evaluated
responsibly.

## Objectives

1. Provide a safe, sandboxed way to observe **typing behavior** and derive
   analytics from keystroke metadata.
2. Model keylogger-like **threat telemetry** using purely synthetic data.
3. Implement a **transparent, rule-based detection engine** (no black-box ML).
4. Produce an explainable **risk score** with per-rule contributions.
5. Present everything through a professional **SOC dashboard**.
6. Enforce **application-security best practices** throughout (auth, validation,
   authorization, auditing).

## Features

- **Authentication** — registration, login (username *or* email), JWT sessions,
  bcrypt hashing, protected routes, audit logging.
- **Virtual Keylogger Lab** — explicit Start/Stop, live session timer, total
  keystrokes, KPM, average interval; metadata-only capture with a visible
  TEST MODE banner.
- **Keystroke Analytics** — KPM, WPM, mean/median inter-key interval, pause
  time, backspace rate, modifier frequency, category distribution, with charts.
- **Synthetic Threat Simulation** — benign/balanced/aggressive profiles;
  start/stop/generate/reset; fabricated process telemetry.
- **Detection Engine** — 5 rules, each with severity, evidence, and a
  recommendation.
- **Risk Scoring** — additive, transparent, banded LOW→CRITICAL with a per-rule
  breakdown.
- **SOC Dashboard** — risk gauge, stat cards, event timeline, operations status,
  live WebSocket updates (with REST polling fallback).

## Architecture

Three tiers: React SPA ⇄ FastAPI ⇄ PostgreSQL. See
[`docs/architecture.md`](docs/architecture.md) for diagrams and the data model.

```
frontend/  React + Vite + Tailwind + Recharts   (auth, lab, analytics,
                                                  simulation, detection, SOC)
backend/   FastAPI + SQLAlchemy + Alembic        (JWT auth, services, REST + WS)
docs/      architecture · threat-model · api · development
```

## Technology Stack

| Layer     | Technology                                             |
|-----------|--------------------------------------------------------|
| Frontend  | React 18, Vite 5, Tailwind CSS 3, Recharts, React Router 6 |
| Backend   | Python 3.11, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2 |
| Database  | PostgreSQL 16                                          |
| Auth      | JWT (python-jose), bcrypt (passlib)                    |
| Realtime  | WebSocket (dashboard)                                  |
| Tooling   | pytest, Ruff, ESLint, Docker Compose                   |

## Installation

### Quick start (Docker)
```bash
cp .env.example .env      # edit SECRET_KEY etc.
docker compose up --build
# frontend → http://localhost:5173   backend docs → http://localhost:8000/docs
```

### Manual setup
See [`docs/development.md`](docs/development.md) for full step-by-step
instructions. In brief:

**Environment**
```bash
cp .env.example .env
# set SECRET_KEY, DATABASE_URL, CORS_ORIGINS
```

**Database**
```bash
sudo -u postgres psql -c "CREATE USER keylogger WITH PASSWORD 'keylogger_dev';"
sudo -u postgres psql -c "CREATE DATABASE keylogger OWNER keylogger;"
```

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## API Overview

Base path `/api`; interactive docs at `/docs`. Highlights:

```
POST /api/auth/register        POST /api/simulation/start
POST /api/auth/login           POST /api/simulation/generate
GET  /api/auth/me              GET  /api/simulation/events
POST /api/sessions/start       POST /api/detection/analyze
POST /api/sessions/stop        GET  /api/detection/rules
POST /api/keystrokes/events    GET  /api/detection/results
GET  /api/keystrokes/statistics GET /api/dashboard/summary
GET  /api/health               WS   /api/dashboard/ws
```

Full reference: [`docs/api.md`](docs/api.md).

## Testing

```bash
# Backend — 29 tests, in-memory SQLite (no external DB needed)
cd backend && source .venv/bin/activate
pytest
ruff check app tests

# Frontend
cd frontend
npm run lint
npm run build
```

Coverage spans hashing/JWT, analytics math, the simulation service, the
detection/scoring engine, auth flows, keystroke ingest & statistics,
active-session enforcement, the full simulation→detection→dashboard flow, and
cross-user authorization.

## Screenshots

> _Placeholder — add captures for your submission:_
>
> - `docs/screenshots/dashboard.png` — SOC dashboard
> - `docs/screenshots/lab.png` — Virtual Keylogger Lab (TEST MODE active)
> - `docs/screenshots/analytics.png` — Keystroke analytics
> - `docs/screenshots/detection.png` — Detection & risk breakdown

## Security Considerations

- bcrypt password hashing; secrets only from environment variables.
- JWT-protected routes; per-resource ownership checks (404 on cross-user access).
- Pydantic validation on all inputs; SQLAlchemy parameterized queries.
- CORS restricted to configured origins; audit logging of sensitive actions.
- Server-side enforcement that keystroke *characters* are never persisted.

Details and residual risks: [`docs/threat-model.md`](docs/threat-model.md).

## Limitations

- Stateless JWT logout (client-side disposal + audit entry); no refresh/rotation.
- Tokens in `localStorage` for demo simplicity (httpOnly cookies recommended for
  production).
- No rate limiting / account lockout (out of capstone scope).
- Threat data is synthetic by design — there is no real host telemetry.

## Future Scope

- Real endpoint-agent integration feeding *authentic* (consented) telemetry.
- Machine-learning anomaly detection alongside the transparent rule engine.
- Alerting/notification integrations (email, Slack, SIEM export).
- Role-based access control and multi-tenant SOC views.
- Historical trend analytics and per-user behavioral baselining.

## License / Use

Educational capstone project. Intended solely for learning, demonstration, and
defensive research. Do not repurpose any part of it for unauthorized monitoring.
