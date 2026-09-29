# Threat Model & Safety Boundaries

## Purpose

This document defines what the Linux Keylogging Defense Lab models, what it
deliberately does **not** do, and the controls that keep it safe. The framework
is a **defensive** research tool for an **isolated, authorized VM you own**.

## 1. Authorization & environment

- The lab is intended to run **only inside an isolated VMware VM** (Kali/Ubuntu)
  that the operator owns and controls.
- It performs no network communication and exposes no service.
- It requires no elevated privileges to function; it reads only public `/proc`
  metadata available to a normal user.

## 2. What the lab deliberately does NOT do (by design)

- ❌ System-wide keyboard hooks or input capture of any kind
- ❌ Reading keystrokes, clipboard, screen, files, or credentials
- ❌ Capturing or storing sensitive typed text
- ❌ Persistence (autostart, cron, services, systemd units)
- ❌ Stealth, obfuscation, or anti-analysis / evasion
- ❌ Privilege escalation
- ❌ Disabling or tampering with security tooling
- ❌ Network communication or data exfiltration

There is no code path in the framework that hooks input devices, reads
`/dev/input`, attaches to other processes, or records characters typed by a
user. Process observation (Module 3) is strictly **read-only metadata**.

## 3. Simulated vs. real

| Aspect                    | Real or synthetic?                                  |
|---------------------------|-----------------------------------------------------|
| Keystroke telemetry       | **Synthetic** — generated numbers, never real keys  |
| "demo-keylogger" process  | **Fabricated** — a name in generated data only      |
| Persistence / network flags | **Synthetic** booleans in generated telemetry     |
| Process/behaviour metadata | **Real but read-only** (`/proc`: pid, name, cmdline) |
| Detection & risk logic    | **Real** rules run over the synthetic telemetry     |

Module 1 (`environment.py`) reads only: hostname, OS/kernel, distribution,
Python runtime, CPU/memory totals, uptime, and process `name`/`cmdline` from
`/proc`. "Lab-relevant" process matching is done on the process **name** only,
so the repository path is never mistaken for a lab process.

## 4. Detection rules (planned — Module 4)

| Rule    | Condition (over synthetic telemetry)  | Severity |
|---------|---------------------------------------|----------|
| KL-001  | Abnormal keyboard-event volume        | HIGH     |
| KL-002  | Suspicious process behaviour          | MEDIUM   |
| KL-003  | Persistence indicator                 | HIGH     |
| KL-004  | Unexpected network communication      | HIGH     |
| KL-005  | Abnormal process execution            | MEDIUM   |
| KL-006  | Suspicious combination of behaviours  | CRITICAL |

Each detection produces: `rule_id`, `severity`, `evidence`, `timestamp`, and a
`recommended_action`.

## 5. Risk scoring (planned — Module 5)

Additive and fully transparent:

```
keyboard monitoring indicator  +25
persistence indicator          +25
network indicator              +25
abnormal event volume          +15
suspicious process behaviour   +10
                    → clamp to [0, 100]

  0–24  LOW      25–49  MEDIUM      50–74  HIGH      75–100  CRITICAL
```

The engine reports exactly which indicators contributed and by how much, so a
score is never a black box.

## 6. Data handling

- All output is written under one workspace directory (`data/` by default) so it
  is easy to inspect, archive, or wipe.
- The SQLite database is intended to be opened directly with the `sqlite3` CLI
  for verification.
- Logs are verbose to support reproducible experiments, but contain only lab
  metadata — never captured input.

## 7. Limitations

- Because all threat behaviour is synthetic, the lab demonstrates detection
  *logic and workflow*, not real-world malware capture.
- Read-only process observation reflects only what `/proc` exposes to the
  running user; it is not a kernel-level EDR.
- The framework is single-host and single-user by design.
