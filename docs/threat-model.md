# Threat Model & Safety Boundaries

This document explains what the platform models, what it deliberately does
**not** do, and how the detection/scoring logic works.

## 1. Safety posture (most important)

KeyLogger is an **educational, defensive** platform. It is intentionally built
so that it *cannot* function as a real keylogger.

### Explicitly NOT implemented (by design)

- System-wide keyboard hooks
- Background / covert capture
- Capturing input from other applications
- Password or credential harvesting
- Browser input interception
- Persistence, stealth, or evasion
- Privilege escalation or AV/security-tool tampering
- Data exfiltration or covert monitoring

### Capture boundaries that ARE enforced

| Guarantee                        | How it is enforced                                   |
|----------------------------------|------------------------------------------------------|
| Capture only in-app              | `onKeyDown/onKeyUp` handlers bound to one `<textarea>`|
| Only while a test is active      | Handlers no-op unless `testing` is true              |
| User-initiated                   | Capture starts only on the explicit **Start test**   |
| No characters stored             | `classifyKey()` emits a *category*, never `event.key`|
| Control labels whitelisted       | Server drops any `key_label` not in an allow-list    |
| Visible active state             | Persistent red **TEST MODE** banner while active     |

The backend independently enforces the label allow-list
(`app/schemas/keystroke.py`), so even a crafted API request cannot persist a
literal character as a key label.

## 2. What is simulated vs. real

| Component            | Real or synthetic?                                        |
|----------------------|-----------------------------------------------------------|
| Keystroke lab        | Real events from the in-app textbox — **metadata only**   |
| Threat telemetry     | 100% **synthetic** (randomly generated numbers)           |
| "Suspicious process" | Fabricated name/values; no real process is inspected      |
| Network / persistence| Boolean flags in synthetic data; nothing is read from OS  |
| Detection engine     | Real rule logic, run over the synthetic telemetry         |

The simulation service (`app/services/simulation.py`) never imports `os`,
`psutil`, sockets, or any system-inspection facility. It only calls `random`.

## 3. Detection rules

| Rule     | Condition (synthetic indicator)      | Severity | Weight |
|----------|--------------------------------------|----------|--------|
| RULE-001 | `high_keyboard_event_volume`         | HIGH     | +25    |
| RULE-002 | `persistence_indicator`              | HIGH     | +25    |
| RULE-003 | `network_communication`              | CRITICAL | +25    |
| RULE-004 | `abnormal_event_frequency`           | MEDIUM   | +15    |
| RULE-005 | `suspicious_process_behavior`        | MEDIUM   | +10    |

Each fired rule produces: rule id, name, description, severity, concrete
**evidence**, a **recommendation**, its point **contribution**, and a timestamp.

## 4. Risk scoring

```
score = Σ (weight of each fired rule)      # then clamped to [0, 100]

  0–24  → LOW
 25–49  → MEDIUM
 50–74  → HIGH
 75–100 → CRITICAL
```

The API returns `score_breakdown` (`{rule_id: points}`) whose values always sum
to `risk_score`. This transparency is verified by an automated test
(`tests/test_flow_api.py::test_simulation_and_detection_flow`).

## 5. Application-security controls

- **Passwords**: bcrypt via passlib; never stored or logged in plaintext.
- **Authentication**: signed JWT (HS256); protected routes require a valid,
  active user.
- **Authorization**: every session-scoped route verifies ownership and returns
  404 for another user's resources (tested).
- **Input validation**: Pydantic v2 schemas on all request bodies.
- **SQL injection**: all DB access via SQLAlchemy parameterized queries.
- **CORS**: origins restricted to a configured allow-list.
- **Secrets**: sourced only from environment variables; `.env` is git-ignored.
- **Audit logging**: register, login, logout, session start/stop, simulation
  actions, and detection runs are recorded.

## 6. Residual considerations (limitations)

- JWTs are stateless; "logout" is client-side token disposal plus an audit
  entry. For production, add short-lived tokens + refresh/rotation or a
  server-side denylist.
- Tokens are stored in `localStorage` for simplicity; a hardened deployment
  would prefer httpOnly cookies with CSRF protection.
- Rate limiting and account lockout are out of scope for this capstone.
