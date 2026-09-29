# Architecture

## Overview

The Linux Keylogging Defense Lab is a **single-host, CLI-first Python
framework**. It runs entirely inside one isolated VMware Linux VM — there is no
server, no browser, and no network service. Data flows through a pipeline of
modules, each with a single responsibility, coordinated by a CLI.

```
                         python main.py <command>
                                   │
                          ┌────────▼────────┐
                          │   CLI (cli.py)  │  argparse dispatch
                          └────────┬────────┘
                                   │  LabContext (paths + config + mode)
        ┌──────────────┬──────────┼───────────┬───────────────┐
        ▼              ▼          ▼           ▼               ▼
   Module 1        Module 2   Module 3    Module 4        Module 9
  Environment     Synthetic   Behavior    Detection        Report
  (read-only)     Telemetry   Monitor     Engine (KL-*)   Generator
        │              │          │           │               ▲
        │              └────┬─────┘           ▼               │
        │                   ▼            Module 5 (Risk)      │
        │            Module 7 (SQLite storage) ◀──────────────┤
        │                   │                                 │
        │                   ▼                                 │
        │            Module 8 (Analysis, CSV/JSON) ───────────┘
        │                   │
        └───────────────────┴──► Module 6 (Terminal Dashboard)
```

## Design principles

- **CLI-first**: every capability is reachable through `main.py`. A terminal
  dashboard (Module 6) is an optional view, not the primary interface.
- **Modular**: each module is an independent Python module under `src/klab/`
  with clear inputs/outputs, so it can be unit-tested in isolation.
- **Synthetic & read-only**: the only "real" system interaction is *read-only*
  observation of `/proc` metadata. All threat behaviour is generated data.
- **Transparent**: detection rules and risk scoring are explicit and explainable
  (no black-box logic).
- **Reproducible**: configuration and outputs live under a single workspace
  directory (`data/` by default) so experiments can be re-run and inspected.

## Component responsibilities

| Module | File (planned)          | Responsibility                                   |
|--------|-------------------------|--------------------------------------------------|
| CLI    | `cli.py`, `commands.py` | Parse args, build context, dispatch commands     |
| Config | `config.py`             | Paths, experiment modes, thresholds, config I/O  |
| 1      | `environment.py`        | Read-only Linux environment + process snapshot   |
| 2      | `telemetry.py`          | Generate synthetic keystroke telemetry           |
| 3      | `monitor.py`            | Read-only process/behaviour observation          |
| 4      | `detection.py`          | Rule engine (KL-001 … KL-006)                    |
| 5      | `risk.py`               | Transparent additive risk scoring                |
| 6      | `dashboard.py`          | Terminal SOC-style dashboard                      |
| 7      | `storage.py`            | SQLite persistence (events, detections, …)       |
| 8      | `analysis.py`           | Frequency/burst/interval analysis, CSV/JSON       |
| 9      | `report.py`             | PDF experiment report                            |
| 10     | `modes.py` / config     | NORMAL / SUSPICIOUS / HIGH_RISK experiment modes  |

## Workspace layout (runtime)

Created by `python main.py setup` (default base `./data`, override with
`--home` or `$KLAB_HOME`):

```
data/
├── config.json      # inspectable lab configuration
├── klab.sqlite3     # SQLite database (created by the storage module)
├── logs/            # rotating detailed logs
├── datasets/        # exported CSV/JSON experiment datasets
└── reports/         # generated PDF reports
```

## Data model (planned — Module 7)

SQLite tables, designed to be easy to inspect with the `sqlite3` CLI:

- `test_sessions` — one experiment run (mode, timestamps)
- `events` — synthetic keystroke telemetry events
- `process_observations` — read-only process metadata snapshots
- `detections` — fired detection rules with evidence
- `risk_scores` — per-session score, level, and breakdown

## Current status

All ten modules are implemented and covered by tests. The CLI exposes the full
pipeline through `setup`, `status`, `test`, `analyze`, and `report`. Experiment
outcomes are deterministic for a fixed seed (see `docs/methodology.md` and
`samples/expected_mode_outcomes.json`).
