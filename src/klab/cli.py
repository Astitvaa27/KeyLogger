"""Command-line interface: argument parsing and dispatch."""
from __future__ import annotations

import argparse
import sys

from klab import __title__, __version__, commands
from klab.config import build_context
from klab.logging_setup import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description=f"{__title__} (v{__version__}) — CLI-first, defensive, synthetic.",
        epilog="All attack behaviour is SIMULATED. No real keystrokes are captured.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--home",
        metavar="DIR",
        default=None,
        help="Override the lab workspace directory (default: ./data or $KLAB_HOME).",
    )
    parser.add_argument(
        "--mode",
        metavar="MODE",
        default=None,
        help="Experiment mode: NORMAL | SUSPICIOUS | HIGH_RISK.",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        help="Override log level (DEBUG, INFO, WARNING, ERROR).",
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>", required=True)

    sub.add_parser("setup", help="Initialize the lab workspace and show the environment.")
    sub.add_parser("status", help="Show environment, configuration, and lab state.")

    p_test = sub.add_parser("test", help="Run an experiment (synthetic telemetry + detection).")
    p_test.add_argument("--count", type=int, default=None,
                        help="Number of synthetic events to generate (default: config batch).")
    p_test.add_argument("--seed", type=int, default=None,
                        help="Seed for reproducible telemetry.")
    p_test.add_argument("--no-monitor", action="store_true",
                        help="Skip read-only process observation.")

    p_analyze = sub.add_parser("analyze", help="Analyze telemetry/detections and export datasets.")
    p_analyze.add_argument("--session", type=int, default=None,
                           help="Session id to analyze (default: latest).")
    p_analyze.add_argument("--no-export", action="store_true",
                           help="Print analysis without writing dataset files.")

    p_report = sub.add_parser("report", help="Generate a professional PDF report.")
    p_report.add_argument("--session", type=int, default=None,
                          help="Session id to report on (default: latest).")
    return parser


_HANDLERS = {
    "setup": commands.cmd_setup,
    "status": commands.cmd_status,
    "test": commands.cmd_test,
    "analyze": commands.cmd_analyze,
    "report": commands.cmd_report,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        ctx = build_context(base_dir=args.home, mode=args.mode)
    except ValueError as exc:
        parser.error(str(exc))
        return 2  # unreachable; parser.error exits

    level = args.log_level or ctx.config.log_level
    configure_logging(log_dir=ctx.paths.logs, level=level)

    handler = _HANDLERS[args.command]
    try:
        return handler(ctx, args)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as exc:  # top-level safety net with a clear message
        configure_logging().error("Command '%s' failed: %s", args.command, exc, exc_info=True)
        print(f"Error: {exc}", file=sys.stderr)
        return 1
