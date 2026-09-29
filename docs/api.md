# API Reference

Base URL: `/api`. Interactive docs (Swagger UI) are served at `/docs`, and the
OpenAPI schema at `/openapi.json`.

Authenticated endpoints require an `Authorization: Bearer <JWT>` header. Obtain
a token from `/api/auth/register` or `/api/auth/login`.

## Auth

### `POST /api/auth/register`
Create an account. Returns a token bundle.
```json
// request
{ "email": "a@example.com", "username": "alice", "password": "AlicePass1!", "full_name": "Alice" }
// 201 response
{ "access_token": "...", "token_type": "bearer", "expires_in": 3600, "user": { ... } }
```

### `POST /api/auth/login`
```json
{ "username_or_email": "alice", "password": "AlicePass1!" }
```
Returns the same token bundle. `401` on bad credentials.

### `GET /api/auth/me`
Returns the current user. Requires auth.

### `POST /api/auth/logout`
Records an audit entry. The client discards the token. Requires auth.

## Sessions

| Method & path                        | Description                       |
|--------------------------------------|-----------------------------------|
| `POST /api/sessions/start`           | Start a new session (`{label?}`)  |
| `POST /api/sessions/stop?session_id=`| Stop an active session            |
| `GET  /api/sessions`                 | List the user's sessions          |
| `GET  /api/sessions/{session_id}`    | Get one owned session             |

## Keystrokes

### `POST /api/keystrokes/events`
Ingest a batch of keystroke **metadata** for an active session.
```json
{
  "session_id": 1,
  "events": [
    { "sequence_number": 0, "category": "LETTER", "interval_ms": 120, "duration_ms": 80 },
    { "sequence_number": 1, "category": "MODIFIER", "key_label": "Shift", "interval_ms": 90 }
  ]
}
```
`category` is one of: `LETTER, DIGIT, WHITESPACE, MODIFIER, ENTER, EDITING_KEY,
NAVIGATION, FUNCTION, PUNCTUATION, OTHER`. `key_label` is retained only for
whitelisted control keys. `409` if the session is not active.

### `GET /api/keystrokes/statistics?session_id=`
Returns computed behavioral statistics (KPM, WPM, intervals, backspace rate,
modifier frequency, category distribution).

## Simulation (synthetic)

| Method & path                  | Body                                        |
|--------------------------------|---------------------------------------------|
| `POST /api/simulation/start`   | `{session_id, profile}`                     |
| `POST /api/simulation/generate`| `{session_id, count, profile}`              |
| `POST /api/simulation/stop`    | `{session_id}`                              |
| `POST /api/simulation/reset`   | `{session_id}` — deletes synthetic events   |
| `GET  /api/simulation/events?session_id=` | List synthetic telemetry         |

`profile` ∈ `benign | balanced | aggressive`. A synthetic event looks like:
```json
{
  "id": 12, "session_id": 1, "process_name": "demo-keylogger.exe",
  "keyboard_events": 1250, "persistence_indicator": true, "network_activity": true,
  "event_rate_per_min": 640,
  "risk_indicators": ["high_keyboard_event_volume", "persistence_indicator",
                      "network_communication", "abnormal_event_frequency",
                      "suspicious_process_behavior"]
}
```

## Detection & risk

### `GET /api/detection/rules`
Returns the rule catalog (id, name, description, severity, weight, recommendation).

### `POST /api/detection/analyze`
```json
{ "session_id": 1 }
```
Runs the engine over the session's synthetic telemetry:
```json
{
  "id": 3, "session_id": 1, "risk_score": 100, "risk_level": "CRITICAL",
  "score_breakdown": { "RULE-001": 25, "RULE-002": 25, "RULE-003": 25, "RULE-004": 15, "RULE-005": 10 },
  "triggered_rules": [ { "rule_id": "RULE-003", "severity": "CRITICAL",
                         "evidence": "...", "recommendation": "...", "contribution": 25 } ]
}
```

### `GET /api/detection/results?session_id=`
Lists prior detection runs (newest first).

## Dashboard

### `GET /api/dashboard/summary`
Aggregated SOC summary: current risk level/score, events detected, active
session, suspicious processes, rules triggered, keyboard events, simulation
status, session count, and a recent event timeline.

### `WS /api/dashboard/ws?token=<JWT>`
Pushes a fresh summary JSON frame every ~5 seconds.

## Health

### `GET /api/health`
Liveness + database connectivity. No auth required.

## Status codes

| Code | Meaning                                   |
|------|-------------------------------------------|
| 200  | OK                                        |
| 201  | Created                                   |
| 401  | Missing/invalid token                     |
| 403  | Disabled account                          |
| 404  | Resource not found / not owned by caller  |
| 409  | Conflict (duplicate user, inactive session)|
| 422  | Validation error                          |
