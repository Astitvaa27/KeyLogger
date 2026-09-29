"""Command handlers for the CLI.

- setup   : initialize the lab workspace and show the environment (Module 1)
- status  : show environment, configuration, and lab state (Module 1)
- test    : run an experiment — telemetry + monitor + detect + score + store (2–7,10)
- analyze : analyse a session and export datasets (Module 8)
- report  : generate a professional PDF report (Module 9)
"""
from __future__ import annotations

from klab import __title__, __version__, ui
from klab import analysis as analysis_mod
from klab import dashboard as dashboard_mod
from klab import report as report_mod
from klab.config import Config, LabContext
from klab.detection import analyze as run_detection
from klab.environment import collect_environment
from klab.logging_setup import get_logger
from klab.monitor import backend_name, observe_processes
from klab.risk import score as score_risk
from klab.storage import Storage
from klab.telemetry import generate_batch

log = get_logger("commands")


def _print_environment(include_processes: bool = True) -> None:
    env = collect_environment(include_processes=include_processes)
    print(ui.header("Linux Environment"))
    print(ui.kv("Hostname", env.hostname))
    print(ui.kv("Distribution", env.distribution))
    print(ui.kv("OS / Kernel", f"{env.os_system} {env.os_release}"))
    print(ui.kv("Architecture", env.architecture))
    print(ui.kv("Python", f"{env.python_version} ({env.python_executable})"))
    print(ui.kv("User", env.username))
    print(ui.kv("CPU cores", env.cpu_count))
    print(ui.kv("Total memory", f"{env.total_memory_mb:.0f} MB"))
    print(ui.kv("Uptime", f"{env.uptime_seconds / 3600:.1f} h"))
    print(ui.kv("Running processes", len(env.processes)))

    if not env.is_linux:
        print()
        print(ui.warn("Host is not Linux — the framework targets Linux VMs; "
                      "process monitoring will be limited."))

    if include_processes:
        lab = env.lab_processes
        print(ui.header("Lab-relevant processes"))
        if lab:
            rows = [[p.pid, p.name, (p.cmdline or "")[:48]] for p in lab]
            print(ui.table(["PID", "NAME", "CMDLINE"], rows))
        else:
            print(ui.info("None detected (this is expected before running simulations)."))


def _ensure_workspace(ctx: LabContext) -> None:
    for d in ctx.paths.all_dirs():
        d.mkdir(parents=True, exist_ok=True)
    if not ctx.paths.config_file.exists():
        ctx.paths.config_file.write_text(Config(default_mode=ctx.mode.value).to_json())


# --------------------------------------------------------------------------
def cmd_setup(ctx: LabContext, args) -> int:
    """Initialize the cybersecurity laboratory workspace."""
    print(ui.banner("LINUX KEYLOGGING DEFENSE LAB — SETUP"))
    print(ui.info(f"{__title__} v{__version__}"))

    _ensure_workspace(ctx)
    print(ui.ok(f"Workspace ready at {ctx.paths.base}"))
    for d in ctx.paths.all_dirs():
        print(ui.kv("  dir", d))
    print(ui.ok(f"Config → {ctx.paths.config_file}"))

    # Initialize the SQLite schema now so the database is inspectable immediately.
    with Storage(ctx.paths.database):
        pass
    print(ui.ok(f"Database initialized → {ctx.paths.database}"))
    print(ui.info(f"Process-monitor backend: {backend_name()}"))

    _print_environment(include_processes=True)

    print(ui.header("Authorization"))
    print(ui.info("This lab is intended for an isolated, authorized VMware VM you own."))
    print(ui.info("All attack behaviour is SIMULATED. No real keystrokes are captured."))
    print()
    print(ui.ok("Setup complete. Next: `python main.py test --mode SUSPICIOUS`"))
    log.info("Lab setup completed at %s", ctx.paths.base)
    return 0


def cmd_status(ctx: LabContext, args) -> int:
    """Show environment, configuration, and lab initialization state."""
    print(ui.banner("LINUX KEYLOGGING DEFENSE LAB — STATUS"))

    print(ui.header("Lab State"))
    print(ui.kv("Initialized", ui.color("YES", "green") if ctx.is_initialized
                 else ui.color("NO — run `python main.py setup`", "yellow")))
    print(ui.kv("Workspace", ctx.paths.base))
    print(ui.kv("Config file", ctx.paths.config_file if ctx.paths.config_file.exists()
                 else "(missing)"))
    print(ui.kv("Database", ctx.paths.database if ctx.paths.database.exists()
                 else "(not yet created)"))
    print(ui.kv("Active mode", ctx.mode.value))
    print(ui.kv("Monitor backend", backend_name()))

    if ctx.paths.database.exists():
        with Storage(ctx.paths.database) as store:
            sessions = store.list_sessions()
            print(ui.kv("Recorded sessions", len(sessions)))
            if sessions:
                latest = sessions[0]
                risk = store.latest_risk_score(int(latest["id"]))
                print(ui.kv("Latest session",
                            f"#{latest['id']} · {latest['mode']} · "
                            f"risk={risk['score'] if risk else 0} "
                            f"({risk['level'] if risk else 'LOW'})"))

    print(ui.header("Configuration"))
    print(ui.kv("Lab name", ctx.config.lab_name))
    print(ui.kv("Default mode", ctx.config.default_mode))
    print(ui.kv("Log level", ctx.config.log_level))
    print(ui.kv("Event batch size", ctx.config.default_event_batch))
    print(ui.kv("Authorized lab", ctx.config.authorized_lab))

    _print_environment(include_processes=True)
    return 0


def cmd_test(ctx: LabContext, args) -> int:
    """Run an experiment: generate telemetry, observe, detect, score, store."""
    _ensure_workspace(ctx)
    count = args.count or ctx.config.default_event_batch
    print(ui.banner("LINUX KEYLOGGING DEFENSE LAB — TEST"))
    print(ui.info(f"Mode: {ctx.mode.value}  ·  events: {count}  ·  "
                  f"monitor: {'off' if args.no_monitor else backend_name()}"))

    with Storage(ctx.paths.database) as store:
        session_id = store.create_session(ctx.mode.value)

        # Module 2 — synthetic telemetry
        events = generate_batch(ctx.mode, count, seed=args.seed)
        store.add_events(session_id, events)
        print(ui.ok(f"Generated {len(events)} synthetic telemetry events."))

        # Module 3 — read-only process observation
        observations = []
        if not args.no_monitor:
            obs = observe_processes()
            observations = [o.to_dict() for o in obs]
            store.add_process_observations(session_id, observations)
            print(ui.ok(f"Observed {len(observations)} processes (read-only, "
                        f"{backend_name()})."))

        # Module 4 — detection
        detections = run_detection(events, observations)
        store.add_detections(session_id, [d.to_dict() for d in detections])
        print(ui.ok(f"Detection engine produced {len(detections)} finding(s)."))

        # Module 5 — risk scoring
        risk = score_risk(detections)
        store.add_risk_score(session_id, risk.score, risk.level, risk.breakdown)
        store.end_session(session_id, len(events))
        print(ui.ok(f"Risk score: {risk.score}/100 ({risk.level})."))

        # Module 6 — dashboard
        print()
        print(dashboard_mod.render_session(ctx, store, session_id))

    print()
    print(ui.info(f"Session #{session_id} stored. "
                  f"Next: `python main.py analyze` or `python main.py report`."))
    return 0


def _resolve_session(store: Storage, requested: int | None) -> int | None:
    if requested is not None:
        return requested if store.get_session(requested) else None
    return store.latest_session_id()


def cmd_analyze(ctx: LabContext, args) -> int:
    """Analyze a session's data and export CSV/JSON datasets."""
    print(ui.banner("LINUX KEYLOGGING DEFENSE LAB — ANALYZE"))
    if not ctx.paths.database.exists():
        print(ui.warn("No database yet. Run `python main.py test` first."))
        return 1

    with Storage(ctx.paths.database) as store:
        session_id = _resolve_session(store, args.session)
        if session_id is None:
            print(ui.warn("No matching session found. Run `python main.py test` first."))
            return 1

        summary = analysis_mod.analyze_session(store, session_id)
        totals = summary["totals"]
        ev = summary["event_volume"]
        risk = summary["risk"]

        print(ui.header(f"Session #{session_id} analysis"))
        print(ui.kv("Events", totals["events"]))
        print(ui.kv("Total keyboard events", totals["total_keyboard_events"]))
        print(ui.kv("Event count (min/mean/max)", f"{ev['min']} / {ev['mean']} / {ev['max']}"))
        print(ui.kv("Detections", totals["detections"]))
        print(ui.kv("Risk", f"{risk['score']}/100 ({risk['level']})"))

        print(ui.header("Event frequency by process"))
        for name, n in summary["event_frequency"]["by_process"].items():
            print(ui.kv(f"  {name}", n))

        print(ui.header("Detection frequency by rule"))
        by_rule = summary["detection_frequency"]["by_rule"]
        if by_rule:
            for rid, n in by_rule.items():
                print(ui.kv(f"  {rid}", n))
        else:
            print(ui.info("No detections."))

        if not args.no_export:
            paths = analysis_mod.export_all(store, summary, ctx.paths.datasets, session_id)
            print(ui.header("Exported datasets"))
            for p in paths:
                print(ui.ok(str(p)))

    return 0


def cmd_report(ctx: LabContext, args) -> int:
    """Generate a professional PDF report for a session."""
    print(ui.banner("LINUX KEYLOGGING DEFENSE LAB — REPORT"))
    if not ctx.paths.database.exists():
        print(ui.warn("No database yet. Run `python main.py test` first."))
        return 1

    with Storage(ctx.paths.database) as store:
        session_id = _resolve_session(store, args.session)
        if session_id is None:
            print(ui.warn("No matching session found. Run `python main.py test` first."))
            return 1
        summary = analysis_mod.analyze_session(store, session_id)
        path = report_mod.generate_report(ctx, store, session_id, summary)

    kind = "PDF" if path.suffix == ".pdf" else "Markdown (fpdf2 not installed)"
    print(ui.ok(f"{kind} report generated → {path}"))
    return 0
