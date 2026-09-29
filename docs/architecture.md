# Architecture

## Overview

KeyLogger is a three-tier application: a React single-page app, a FastAPI
backend, and a PostgreSQL database. It demonstrates a complete **defensive**
workflow around keylogging — from behavioral capture of the user's own typing,
through synthetic threat simulation, to rule-based detection, transparent risk
scoring, and a SOC-style dashboard.

```
┌──────────────────────────────┐        ┌──────────────────────────────┐
│          Frontend            │  REST  │           Backend            │
│  React + Vite + Tailwind     │◀──────▶│  FastAPI + SQLAlchemy        │
│                              │  WS    │                              │
│  • Auth (JWT in localStorage)│◀──────▶│  • Auth / JWT / bcrypt       │
│  • Virtual Keylogger Lab     │        │  • Keystroke ingest+analytics│
│  • Analytics (Recharts)      │        │  • Synthetic simulation      │
│  • Threat Simulation         │        │  • Detection engine          │
│  • Detection & Risk          │        │  • Risk scoring              │
│  • SOC Dashboard (live WS)   │        │  • Dashboard aggregation     │
└──────────────────────────────┘        └───────────────┬──────────────┘
                                                         │ SQLAlchemy
                                                         ▼
                                              ┌────────────────────┐
                                              │    PostgreSQL 16   │
                                              │  (Alembic-managed) │
                                              └────────────────────┘
```

## Backend layers

```
backend/app/
├── main.py            # FastAPI app assembly, CORS, lifespan seeding
├── core/
│   ├── config.py      # Pydantic settings (env-driven, no hard-coded secrets)
│   ├── database.py    # Engine, SessionLocal, declarative Base, get_db
│   └── security.py    # bcrypt hashing + JWT create/decode
├── models/            # SQLAlchemy ORM models (7 tables) + enums
├── schemas/           # Pydantic request/response models
├── services/          # Business logic (pure, testable)
│   ├── analytics.py   # Keystroke statistics
│   ├── simulation.py  # Synthetic telemetry generation
│   ├── detection.py   # Rule engine + risk scoring
│   └── audit.py       # Audit logging helper
├── api/
│   ├── deps.py        # get_current_user, session ownership guard
│   ├── router.py      # Aggregates all routers under /api
│   └── routes/        # auth, sessions, keystrokes, simulation,
│                      # detection, dashboard, health
└── utils/seed.py      # Seeds the detection-rule catalog
```

**Design principle:** business logic lives in `services/` as pure functions
that operate on ORM objects or plain data, so it can be unit-tested without a
web server or database. Routes are thin — they handle auth, validation, and
persistence, then delegate.

## Data model

| Table                   | Purpose                                                   |
|-------------------------|-----------------------------------------------------------|
| `users`                 | Accounts; bcrypt password hash                            |
| `sessions`              | A user-initiated test/analysis run                        |
| `keystroke_test_events` | Per-keystroke **metadata** (category, timing) — no chars  |
| `simulation_events`     | **Synthetic** telemetry for a hypothetical process        |
| `detection_results`     | Output of a detection run (score, level, breakdown)       |
| `detection_rules`       | Seeded catalog of rules and weights                       |
| `audit_logs`            | Security-relevant user actions                            |

Relationships: a `User` has many `Session`s; each `Session` has many
`keystroke_test_events`, `simulation_events`, and `detection_results`. All
child rows cascade-delete with their session.

## Request lifecycle (example: detection)

1. Client `POST /api/detection/analyze` with a JWT and `session_id`.
2. `get_current_user` decodes the JWT and loads the active user.
3. The route confirms the session belongs to that user (404 otherwise).
4. It loads the session's `simulation_events`.
5. `services.detection.analyze()` aggregates indicators, fires matching rules,
   and computes a transparent score.
6. A `DetectionResult` is persisted; an `AuditLog` entry is recorded.
7. The result (score, level, per-rule breakdown) is returned.

## Real-time dashboard

The SOC dashboard first loads a summary over REST, then opens a WebSocket
(`/api/dashboard/ws?token=<JWT>`) that pushes a fresh summary every ~5s. If the
socket fails, the client transparently falls back to REST polling.

## Risk-scoring model

Scoring is additive and fully transparent (see [threat-model.md](threat-model.md)):
each fired rule contributes a fixed weight; the sum (clamped 0–100) maps to a
band (LOW/MEDIUM/HIGH/CRITICAL). The API returns the exact per-rule
contribution so the score is never a black box.
