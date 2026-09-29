# Linux Keylogging Defense Lab

### Linux Keylogging Simulation, Detection and Behavioral Analysis Framework

A **CLI-first, Linux-native, defensive** cybersecurity research framework
designed to run inside an **isolated, authorized VMware VM** (Kali Linux or
Ubuntu). It demonstrates the full defensive workflow around keylogging using
**only synthetic data and read-only system observation**:

```
Linux VM
   ├── Test Environment              (Module 1)   ✅
   ├── Synthetic Keylogger Telemetry (Module 2)   ✅
   ├── Process/Behavior Monitor      (Module 3)   ✅
   ├── Detection Engine              (Module 4)   ✅
   ├── Risk Scoring                  (Module 5)   ✅
   ├── Terminal Dashboard            (Module 6)   ✅
   ├── Event Logger / Storage        (Module 7)   ✅
   ├── Analysis + Datasets           (Module 8)   ✅
   ├── Report Generator              (Module 9)   ✅
   └── Experiment Modes              (Module 10)  ✅
```

> **Build status:** all 10 modules implemented. `setup`, `status`, `test`,
> `analyze`, and `report` are fully functional. 40 unit tests, ruff clean.

---

## ⚠️ Safety & Authorization (read first)

This is a **defensive** research tool for a lab you own and control.

- ✅ Runs inside **your own isolated VMware VM**; intended for authorized study.
- ✅ All "attack" behaviour is **simulated** — telemetry is fabricated.
- ✅ System observation is **read-only** (`/proc` metadata, process listings).
- ❌ **No** real keylogging, keystroke capture, or input hooking.
- ❌ **No** password/credential capture.
- ❌ **No** persistence, stealth, evasion, privilege escalation, or exfiltration.

See [`docs/threat-model.md`](docs/threat-model.md) for the full safety model.

---

## Requirements

- Linux (Kali/Ubuntu recommended); works on any modern Linux with `/proc`
- Python 3.9+
- No external services required for the core lab (SQLite is used later)

## Quick start

```bash
# 1. (optional) create a virtual environment
python3 -m venv .venv && source .venv/bin/activate

# 2. install dependencies (core runs on the stdlib; deps support later modules)
pip install -r requirements.txt

# 3. initialize the lab and inspect the environment
python main.py setup

# 4. show environment, configuration, and lab state
python main.py status
```

## Commands

| Command                 | Purpose                                                 |
|-------------------------|---------------------------------------------------------|
| `python main.py setup`  | Initialize workspace, write config, init DB, show env   |
| `python main.py status` | Show Linux environment, config, and lab state           |
| `python main.py test`   | Run an experiment (telemetry → monitor → detect → score)|
| `python main.py analyze`| Analyze telemetry/detections; export CSV/JSON datasets  |
| `python main.py report` | Generate a professional PDF report                      |

Global options: `--home DIR` (workspace location), `--mode {NORMAL,SUSPICIOUS,HIGH_RISK}`,
`--log-level LEVEL`, `--version`.

`test` options: `--count N`, `--seed N` (reproducible), `--no-monitor`.
`analyze` / `report` options: `--session ID` (default: latest).

### Example

```bash
python main.py setup
python main.py --mode HIGH_RISK test --count 60 --seed 1
python main.py analyze      # exports datasets to data/datasets/
python main.py report       # writes a PDF to data/reports/
```

## Project layout

```
KeyLogger/
├── main.py                 # CLI entry point
├── requirements.txt
├── pyproject.toml          # pytest + ruff config
├── src/klab/               # framework package
│   ├── cli.py              # argparse dispatch
│   ├── commands.py         # command handlers
│   ├── config.py           # config, paths, experiment modes
│   ├── environment.py      # Module 1 — read-only environment inspection
│   ├── telemetry.py        # Module 2 — synthetic keystroke telemetry
│   ├── monitor.py          # Module 3 — read-only process/behaviour monitor
│   ├── detection.py        # Module 4 — KL-001…KL-006 detection engine
│   ├── risk.py             # Module 5 — transparent risk scoring
│   ├── dashboard.py        # Module 6 — terminal SOC dashboard
│   ├── storage.py          # Module 7 — SQLite persistence
│   ├── analysis.py         # Module 8 — analysis + CSV/JSON export
│   ├── report.py           # Module 9 — PDF report generation
│   ├── modes.py            # Module 10 — experiment mode profiles
│   ├── logging_setup.py    # detailed logging (console + rotating file)
│   └── ui.py               # terminal output helpers
├── tests/                  # pytest suite (40 tests)
├── docs/                   # architecture, threat model, methodology, screenshots
├── samples/                # sample datasets (committed)
└── data/                   # lab runtime output (git-ignored)
```

## Experiment modes (Module 10)

The lab supports three modes that will bias synthetic telemetry generation to
demonstrate how the defensive pipeline distinguishes ordinary activity from
suspicious keylogging-like behaviour:

- `NORMAL_MODE` — ordinary baseline activity
- `SUSPICIOUS_MODE` — mixed indicators
- `HIGH_RISK_MODE` — strong keylogger-like signals

## Testing

```bash
pip install -r requirements.txt
pytest              # unit tests
ruff check src tests
```

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — architecture & data flow
- [`docs/threat-model.md`](docs/threat-model.md) — safety boundaries & threat model
- [`docs/methodology.md`](docs/methodology.md) — running reproducible experiments

## Note on project history

This repository previously hosted a React/FastAPI **web** implementation of the
concept. It has been intentionally replaced with this Linux CLI-first framework
per the project's new direction. The complete previous implementation remains
recoverable in git history (commit `4d15d3a`).

## License / Use

Educational capstone project for authorized, isolated lab use only. Do not
repurpose any part of it for unauthorized monitoring.
