# Experiment Methodology & Reproducibility

This document describes how to run reproducible experiments with the lab and how
to interpret the results.

## Experiment lifecycle

Each `test` run performs one full pipeline pass and stores everything in SQLite:

1. **Session** — a `test_sessions` row is created for the chosen mode.
2. **Telemetry (Module 2)** — synthetic keyboard-activity events are generated,
   biased by the mode profile (Module 10).
3. **Observation (Module 3)** — running processes are snapshotted read-only
   (`psutil`, or `/proc` fallback).
4. **Detection (Module 4)** — rules KL-001…KL-006 run over telemetry + observations.
5. **Risk (Module 5)** — a transparent additive score and level are computed.
6. **Storage (Module 7)** — events, observations, detections, and the risk score
   are persisted.
7. **Dashboard (Module 6)** — a SOC-style summary is printed.

`analyze` (Module 8) then derives statistics and exports datasets; `report`
(Module 9) renders a PDF.

## Experiment modes

| Mode              | Intent                         | Typical outcome |
|-------------------|--------------------------------|-----------------|
| `NORMAL_MODE`     | Ordinary human typing          | LOW (score 0)   |
| `SUSPICIOUS_MODE` | Mixed monitoring indicators    | HIGH (~60)      |
| `HIGH_RISK_MODE`  | Strong keylogger-like signals  | CRITICAL (100)  |

These outcomes are deterministic for a fixed `--seed` (see
`samples/expected_mode_outcomes.json`).

## Reproducing the reference experiments

```bash
python main.py setup

# Baseline (expected LOW)
python main.py --mode NORMAL test --count 50 --seed 1 --no-monitor

# Suspicious (expected HIGH)
python main.py --mode SUSPICIOUS test --count 50 --seed 1 --no-monitor

# High risk (expected CRITICAL)
python main.py --mode HIGH_RISK test --count 50 --seed 1 --no-monitor

# Analyse + export datasets for the latest session
python main.py analyze

# Generate a PDF report
python main.py report
```

`--no-monitor` makes a run depend only on synthetic telemetry, so results are
fully reproducible across machines. Omit it to include live (read-only) process
observation, which additionally exercises KL-002/KL-004 against real processes
that happen to match the lab watch-list (normally none).

## Interpreting results

- **Detections** name the rule, severity, concrete evidence, and a recommended
  action.
- **Risk score** is the sum of unique indicator weights (25/25/25/15/10),
  clamped to 0–100, and the dashboard prints the exact contribution breakdown.
- **Datasets** (`data/datasets/`) contain the raw events, the detections, and a
  JSON analysis summary for offline experimentation.

## Inspecting the database

```bash
sqlite3 data/klab.sqlite3 ".tables"
sqlite3 data/klab.sqlite3 "SELECT id, mode, event_count FROM test_sessions;"
sqlite3 data/klab.sqlite3 "SELECT rule_id, severity, evidence FROM detections;"
```

## Sample datasets

`samples/` contains committed, reproducible reference data:

- `telemetry_*.json` / `.csv` — the five named telemetry datasets
- `expected_mode_outcomes.json` — expected detections/score per mode (seed=1)
