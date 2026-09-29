"""Command handlers for the CLI.

Phase 1 implements `setup` and `status` (Module 1 — Test Environment) fully.
`test`, `analyze`, and `report` are registered and print a clear notice that
they arrive in later phases, so the CLI is complete and runnable end-to-end.
"""
from __future__ import annotations

from klab import __title__, __version__, ui
from klab.config import Config, LabContext
from klab.environment import collect_environment
from klab.logging_setup import get_logger

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


def cmd_setup(ctx: LabContext, args) -> int:
    """Initialize the cybersecurity laboratory workspace."""
    print(ui.banner("LINUX KEYLOGGING DEFENSE LAB — SETUP"))
    print(ui.info(f"{__title__} v{__version__}"))

    # Create the directory layout.
    for d in ctx.paths.all_dirs():
        d.mkdir(parents=True, exist_ok=True)
    print(ui.ok(f"Workspace ready at {ctx.paths.base}"))
    for d in ctx.paths.all_dirs():
        print(ui.kv("  dir", d))

    # Write (or refresh) the config file.
    if not ctx.paths.config_file.exists():
        cfg = Config(default_mode=ctx.mode.value)
        ctx.paths.config_file.write_text(cfg.to_json())
        print(ui.ok(f"Wrote default config → {ctx.paths.config_file}"))
    else:
        print(ui.info(f"Config already present → {ctx.paths.config_file}"))

    # Note about the database (schema is created by the storage module in a
    # later phase; setup ensures the directory exists now).
    print(ui.info(f"Database path reserved → {ctx.paths.database} "
                  "(schema created by the storage module)"))

    _print_environment(include_processes=True)

    print(ui.header("Authorization"))
    print(ui.info("This lab is intended for an isolated, authorized VMware VM you own."))
    print(ui.info("All attack behaviour is SIMULATED. No real keystrokes are captured."))
    print()
    print(ui.ok("Setup complete. Next: `python main.py status`"))
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

    print(ui.header("Configuration"))
    print(ui.kv("Lab name", ctx.config.lab_name))
    print(ui.kv("Default mode", ctx.config.default_mode))
    print(ui.kv("Log level", ctx.config.log_level))
    print(ui.kv("Event batch size", ctx.config.default_event_batch))
    print(ui.kv("Authorized lab", ctx.config.authorized_lab))

    _print_environment(include_processes=True)
    return 0


def _not_yet(name: str, phase: str) -> int:
    print(ui.banner(f"LINUX KEYLOGGING DEFENSE LAB — {name.upper()}"))
    print(ui.warn(f"`{name}` is scaffolded and arrives in {phase}."))
    print(ui.info("Phase 1 delivers the lab foundation and Module 1 (Test Environment): "
                  "`setup` and `status`."))
    return 0


def cmd_test(ctx: LabContext, args) -> int:
    """Run an experiment: generate synthetic telemetry + observe + detect."""
    return _not_yet("test", "a later phase (telemetry + monitor + detection)")


def cmd_analyze(ctx: LabContext, args) -> int:
    """Analyze stored telemetry and detections; export datasets."""
    return _not_yet("analyze", "a later phase (analysis + datasets)")


def cmd_report(ctx: LabContext, args) -> int:
    """Generate a professional PDF experiment report."""
    return _not_yet("report", "a later phase (report generation)")
