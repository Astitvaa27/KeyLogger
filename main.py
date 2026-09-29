#!/usr/bin/env python3
"""Entry point for the Linux Keylogging Defense Lab.

Usage:
    python main.py setup
    python main.py status
    python main.py test
    python main.py analyze
    python main.py report

This is a CLI-first, Linux-native DEFENSIVE research framework. All attack
behaviour is simulated; it never captures real keystrokes or credentials.
"""
from __future__ import annotations

import os
import sys

# Make the `src/` layout importable without requiring installation.
_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from klab.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
