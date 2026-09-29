"""Terminal output helpers (stdlib only).

Provides consistent banners, section headers, key/value rows, and simple tables
used by the CLI and (later) the terminal dashboard. Colour is applied only when
stdout is a TTY, so piped/redirected output stays clean.
"""
from __future__ import annotations

import os
import sys

_USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None

_CODES = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "cyan": "\033[36m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "red": "\033[31m",
    "magenta": "\033[35m",
    "grey": "\033[90m",
}

# Severity / risk level -> colour name.
LEVEL_COLORS = {
    "LOW": "green",
    "MEDIUM": "yellow",
    "HIGH": "red",
    "CRITICAL": "magenta",
    "INFO": "cyan",
}


def color(text: str, name: str) -> str:
    if not _USE_COLOR or name not in _CODES:
        return text
    return f"{_CODES[name]}{text}{_CODES['reset']}"


def bold(text: str) -> str:
    return color(text, "bold")


def banner(title: str, width: int = 55) -> str:
    line = "=" * width
    centered = title.center(width)
    return "\n".join([color(line, "cyan"), color(bold(centered), "cyan"), color(line, "cyan")])


def header(title: str) -> str:
    return "\n" + bold(color(f"── {title} ", "cyan")) + color("─" * max(0, 40 - len(title)), "grey")


def kv(key: str, value, key_width: int = 22) -> str:
    return f"  {color(key.ljust(key_width), 'grey')} {value}"


def level_tag(level: str) -> str:
    level = level.upper()
    return color(f"[{level}]", LEVEL_COLORS.get(level, "cyan"))


def table(headers: list[str], rows: list[list[str]], indent: str = "  ") -> str:
    """Render a simple fixed-width table."""
    cols = len(headers)
    widths = [len(h) for h in headers]
    for row in rows:
        for i in range(cols):
            widths[i] = max(widths[i], len(str(row[i])) if i < len(row) else 0)
    out = []
    head = indent + "  ".join(bold(str(headers[i]).ljust(widths[i])) for i in range(cols))
    out.append(head)
    out.append(indent + "  ".join(color("-" * widths[i], "grey") for i in range(cols)))
    for row in rows:
        cells = [str(row[i]) if i < len(row) else "" for i in range(cols)]
        out.append(indent + "  ".join(cells[i].ljust(widths[i]) for i in range(cols)))
    return "\n".join(out)


def ok(text: str) -> str:
    return color("✔ ", "green") + text


def warn(text: str) -> str:
    return color("! ", "yellow") + text


def info(text: str) -> str:
    return color("• ", "cyan") + text
